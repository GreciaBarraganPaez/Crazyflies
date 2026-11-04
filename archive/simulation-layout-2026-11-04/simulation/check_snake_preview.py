"""Isolated Snake firmware/server/controller integration. Requires ROS domain 89."""
import argparse
import json
import math
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import time
import yaml
import rclpy
from ament_index_python.packages import get_package_share_directory
from snake_preview_server import SnakePreviewServer
from snake_controller import SnakeController
from check_blended_preview import Fleet
from static_shapes import DRONES, HOME, minimum_distance
from scenes.snake import validate_limit,world,MAX_MEMBERS,BORDER_IDS,border_points
import gesture_bridge as bridge


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit',type=int,default=MAX_MEMBERS)
    parser.add_argument('--report',type=Path)
    parser.add_argument('--seed',type=int,default=31)
    parser.add_argument('--return-during-split',action='store_true')
    args=parser.parse_args();validate_limit(args.limit)
    if os.environ.get('ROS_DOMAIN_ID')!='89':raise SystemExit('Use ROS_DOMAIN_ID=89; no live flight commands are sent')
    share=Path(get_package_share_directory('crazyflie'))
    params=yaml.safe_load((share/'config/server.yaml').read_text())['/crazyflie_server']['ros__parameters']
    params.update(yaml.safe_load((Path(__file__).parent/'config/crazyflies.yaml').read_text()))
    params['sim'].update(backend='none',controller='none',max_dt=.02)
    params['robot_description']=(Path(get_package_share_directory('crazyflie_description'))/'urdf/crazyflie_description.urdf').read_text()
    with TemporaryDirectory() as tmp:
        config=Path(tmp)/'server.yaml';config.write_text(yaml.safe_dump({'/crazyflie_server':{'ros__parameters':params}}))
        rclpy.init(args=['--ros-args','--params-file',str(config),'--log-level','error'])
        server=SnakePreviewServer()
        try:
            for cf in server.cfs.values():
                cf.setpoint.position.x,cf.setpoint.position.y,cf.setpoint.position.z=map(float,cf.initialPosition)
            assert server.get_parameter('swarmgesture.snake_scene').value
            assert not server.get_parameter('swarmgesture.continuous_trajectories').value
            fleet=Fleet(server)
            land_calls=[]
            original_land=fleet.land
            def land(**kwargs):land_calls.append(kwargs);original_land(**kwargs)
            fleet.land=land
            def points():return tuple(tuple(getattr(server.cfs[n].state.position,k) for k in ('x','y','z')) for n in DRONES)
            class Feedback:
                def __call__(self):return bridge.arrival_metrics(points(),HOME,.2)[0]
            ctrl=SnakeController(SimpleNamespace(allcfs=fleet,timeHelper=SimpleNamespace(time=server.backend.time)),Feedback())
            ctrl.send_command=lambda data:server.receive_command(SimpleNamespace(data=json.dumps(data)))
            events=[]
            def event(data):
                if data['event']!='state':events.append(data)
                ctrl.receive_status(SimpleNamespace(data=json.dumps(data)))
            server.scene_event=event
            bridge.set_fast_test_timing(True)
            ctrl.keyboard_command(f'count {args.limit}');ctrl.keyboard_command(f'seed {args.seed}');ctrl.arm();ctrl.handle('one')
            stage=0;worst=float('inf');peak=3;moving_frames=0
            min_speed=float('inf');min_split_speed=float('inf');growth_seen=False;split_landed=False
            head_changes=[];last_heads=();split_seen=False;final_lengths=[]
            deadline=time.monotonic()+max(90,args.limit*20)
            while time.monotonic()<deadline:
                if server.snake.pending and not server.snake.pending[0].done():time.sleep(.015)
                server._timer_callback();now=server.backend.time();ctrl.update(now)
                poses=points();gap=minimum_distance(poses);worst=min(worst,gap)
                assert gap>=.52,(stage,now,gap)
                rejected=[e for e in events if e['event']=='rejected']
                assert not rejected,rejected
                assert server.snake.deadline_fallbacks==0,'Gameplay missed a program boundary'
                scene=server.snake.scene;program=server.snake.program
                if scene:
                    peak=max(peak,scene.members)
                    if len(scene.snakes)==2:split_seen=True
                    for group,(previous,head) in enumerate(zip(last_heads,scene.heads)):
                        if previous!=head:
                            assert scene.snakes[group].actors[1]==previous
                            head_changes.append(head)
                    last_heads=scene.heads
                else:last_heads=()
                if scene and program and program[0].kind in ('move','launch','eat'):
                    plan,start,_=program
                    actors=plan.after.actors if plan.kind=='eat' else scene.actors
                    for i in actors:
                        v=server.cfs[DRONES[i]].state.velocity
                        speed=math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z)
                        min_speed=min(min_speed,speed)
                        assert speed>.25,('Stopped body drone',i,plan.kind,now,speed)
                    for i,p in zip(BORDER_IDS,border_points()):assert math.dist(poses[i],p)<1e-4
                    moving_frames+=1
                if scene and program and program[0].kind=='split':
                    for i in scene.actors:
                        v=server.cfs[DRONES[i]].state.velocity
                        speed=math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z)
                        min_split_speed=min(min_split_speed,speed)
                        assert speed>.05,('Stopped during split',i,now,speed)
                    for i,p in zip(BORDER_IDS,border_points()):assert math.dist(poses[i],p)<1e-4
                if stage==0 and ctrl.state=='ready':ctrl.handle('peace');stage=1
                elif stage==1 and scene and scene.members==args.limit:
                    final_lengths=[len(s.actors) for s in scene.snakes]
                    stage=2
                elif stage==2 and ctrl.state=='ready':
                    assert not land_calls,'Automatic grid return unexpectedly landed the fleet'
                    assert bridge.arrival_metrics(poses,HOME,.2)[0],'Automatic return did not reach the grid'
                    assert any(e['event']=='returning' and e.get('reason','').startswith('All apples') for e in events)
                    ctrl.handle('ok');stage=3
                elif stage==3 and args.limit==3 and ctrl.state=='ready':
                    ctrl.land('No-apple restart regression');stage=4
                elif stage==3 and program:
                    plan,start,_=program
                    if args.return_during_split and plan.kind=='split' and now-start>.6:
                        split_landed=True;ctrl.handle('palm');stage=4
                    elif not args.return_during_split and args.limit>3 and plan.kind=='eat' and now-start>.6:
                        growth_seen=True;ctrl.handle('palm');stage=4
                    elif args.limit==3 and scene and scene.moves>=6:
                        ctrl.handle('palm');stage=4
                elif stage==4 and ctrl.state=='grounded':
                    ctrl.handle('one');assert ctrl.state=='grounded','Landing auto-armed takeoff'
                    ctrl.arm();ctrl.handle('one');stage=5
                elif stage==5 and ctrl.state=='ready':ctrl.land('Rearm regression');stage=6
                elif stage==6 and ctrl.state=='grounded':break
            else:raise AssertionError(('Snake integration timeout',stage,ctrl.state,events[-5:]))
            assert peak==args.limit,(peak,args.limit)
            if args.limit>3:assert moving_frames>100
            assert len(head_changes)>=args.limit-3
            assert split_seen==(args.limit>9)
            if args.limit==15:assert sorted(final_lengths)==[7,8]
            assert fleet.go_to_count==0,'Scene playback used SDK goTo streaming'
            assert len(land_calls)==2
            assert bridge.arrival_metrics(points(),tuple((x,y,.04) for x,y,z in HOME),.15)[0]
            report=dict(result='passed',mode='smooth_head_growth',limit=args.limit,seed=args.seed,
                        initial_apples=args.limit-3,border_drones=4,peak_chain=peak,
                        automatic_split=split_seen,
                        final_snake_lengths=final_lengths,
                        minimum_splitting_body_speed_m_s=min_split_speed if split_seen else None,
                        simulated_seconds=now,minimum_center_spacing_m=worst,
                        minimum_playing_body_speed_m_s=min_speed if math.isfinite(min_speed) else None,moving_frames=moving_frames,
                        head_identity_changes=head_changes,deadline_fallbacks=server.snake.deadline_fallbacks,
                        collections=sum(len(e.get('collected_ids',())) for e in events),first_game_collections=peak-3,
                        interrupted_split_landed=split_landed,
                        interrupted_growth_landed=growth_seen,grid_return_and_restart=True,
                        automatic_grid_return=True,
                        manual_rearm_after_landing=True,commands_streamed_per_frame=False)
            if args.report:
                args.report.parent.mkdir(parents=True,exist_ok=True)
                args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            print('SNAKE_PREVIEW_PASS: '+json.dumps(report))
        finally:server.on_shutdown_callback();server.destroy_node();rclpy.try_shutdown()


if __name__=='__main__':main()
