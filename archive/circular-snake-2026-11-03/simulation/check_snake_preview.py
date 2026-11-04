"""Isolated Snake firmware/server/controller integration. Requires ROS domain 89."""
import argparse
import json
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
from scenes.snake import validate_limit
import gesture_bridge as bridge


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit',type=int,default=5)
    parser.add_argument('--report',type=Path)
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
            ctrl.keyboard_command(f'count {args.limit}');ctrl.arm();ctrl.handle('one')
            stage=0;due=None;worst=float('inf');peak=3;loop_frames=0
            deadline=time.monotonic()+max(90,args.limit*15)
            while time.monotonic()<deadline:
                if server.snake.pending:time.sleep(.015)
                server._timer_callback();now=server.backend.time();ctrl.update(now)
                gap=minimum_distance(points());worst=min(worst,gap)
                assert gap>=.52,(stage,now,gap)
                rejected=[e for e in events if e['event']=='rejected']
                assert not rejected,rejected
                if server.snake.scene:peak=max(peak,server.snake.scene.members)
                moving=(server.snake.program and server.snake.program[0].kind=='loop' and not server.snake.pending)
                if moving:loop_frames+=1
                if stage==0 and ctrl.state=='ready':ctrl.handle('peace');stage=1
                elif stage==1 and moving:
                    if due is None:due=now+25.
                    if now>=due:
                        if args.limit>3:ctrl.handle('ok');stage=2
                        else:ctrl.handle('three');stage=3;due=None
                elif stage==2 and moving:
                    if server.snake.scene.pickup is None:
                        if peak<args.limit:ctrl.handle('ok')
                        else:ctrl.handle('three');stage=3;due=None
                elif stage==3 and moving and server.snake.scene.direction==1:
                    if due is None:due=now+25.
                    if now>=due:ctrl.handle('fist');stage=4
                elif stage==4 and ctrl.state=='ready':
                    assert not land_calls,'Fist unexpectedly landed the fleet'
                    ctrl.handle('peace');stage=5
                elif stage==5 and moving:
                    if args.limit>3:ctrl.handle('ok');stage=6;due=None
                    else:ctrl.handle('palm');stage=7
                elif stage==6 and server.snake.program and server.snake.program[0].kind=='stage':
                    if due is None:due=now+1.2
                    if now>=due:ctrl.handle('palm');stage=7
                elif stage==7 and ctrl.state=='grounded':break
            else:raise AssertionError(('Snake integration timeout',stage,ctrl.state,events[-5:]))
            assert peak==args.limit,(peak,args.limit)
            assert sum(e['event']=='collected' for e in events)==args.limit-3
            assert loop_frames>100
            assert fleet.go_to_count==0,'Scene playback used SDK goTo streaming'
            assert len(land_calls)==1
            assert bridge.arrival_metrics(points(),tuple((x,y,.04) for x,y,z in HOME),.15)[0]
            report=dict(result='passed',limit=args.limit,peak_chain=peak,simulated_seconds=now,
                        minimum_center_spacing_m=worst,loop_frames=loop_frames,
                        collections=sum(e['event']=='collected' for e in events),
                        interrupted_pickup_landed=args.limit>3,grid_return_and_restart=True,
                        commands_streamed_per_frame=False)
            if args.report:
                args.report.parent.mkdir(parents=True,exist_ok=True)
                args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            print('SNAKE_PREVIEW_PASS: '+json.dumps(report))
        finally:server.on_shutdown_callback();server.destroy_node();rclpy.try_shutdown()


if __name__=='__main__':main()
