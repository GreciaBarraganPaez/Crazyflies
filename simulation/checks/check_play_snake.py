"""Native playable-Snake integration on ROS domain 89, never the live fleet."""
from simulation.core.paths import CONFIG_DIR, REPORTS_DIR
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
from simulation.servers.play_snake_server import PlayerServer
from simulation.controllers.play_snake_controller import PlayerController
from simulation.scenes.play_snake import DRONES,HOME
from simulation.checks.helpers import Fleet,Drone
from simulation.tests.helpers import scripted_direction
from simulation.core.static_shapes import minimum_distance
import simulation.controllers.gesture_bridge as bridge


class PlayerFleet(Fleet):
    def __init__(self,server):
        self.server=server;self.go_to_count=0
        self.crazyfliesByName={name:Drone(self,name) for name in DRONES}


def main():
    if os.environ.get('ROS_DOMAIN_ID')!='89':raise SystemExit('Use ROS_DOMAIN_ID=89')
    share=Path(get_package_share_directory('crazyflie'))
    params=yaml.safe_load((share/'config/server.yaml').read_text())['/crazyflie_server']['ros__parameters']
    params.update(yaml.safe_load((CONFIG_DIR/'snake-player.yaml').read_text()))
    params['sim'].update(backend='none',controller='none',max_dt=.02)
    params['robot_description']=(Path(get_package_share_directory('crazyflie_description'))/'urdf/crazyflie_description.urdf').read_text()
    with TemporaryDirectory() as tmp:
        config=Path(tmp)/'server.yaml';config.write_text(yaml.safe_dump({'/crazyflie_server':{'ros__parameters':params}}))
        rclpy.init(args=['--ros-args','--params-file',str(config),'--log-level','error'])
        server=PlayerServer()
        try:
            assert set(server.cfs)==set(DRONES)
            assert server.get_parameter('swarmgesture.snake_player').value
            assert not server.get_parameter('swarmgesture.snake_split').value
            for cf in server.cfs.values():
                cf.setpoint.position.x,cf.setpoint.position.y,cf.setpoint.position.z=map(float,cf.initialPosition)
            fleet=PlayerFleet(server);lands=[];original_land=fleet.land
            def land(**kwargs):lands.append(kwargs);original_land(**kwargs)
            fleet.land=land
            def poses():return tuple(tuple(getattr(server.cfs[n].state.position,k) for k in ('x','y','z')) for n in DRONES)
            ctrl=PlayerController(SimpleNamespace(allcfs=fleet,timeHelper=SimpleNamespace(time=server.backend.time)),
                                  lambda:bridge.arrival_metrics(poses(),HOME,.2)[0])
            ctrl.send_command=lambda data:server.receive_command(SimpleNamespace(data=json.dumps(data)))
            events=[]
            def status(data):
                if data['event']!='state':events.append(data)
                ctrl.receive_status(SimpleNamespace(data=json.dumps(data)))
            server.scene_event=status
            bridge.set_fast_test_timing(True)
            ctrl.handle('one');assert ctrl.state=='grounded'
            ctrl.arm();ctrl.handle('one')
            stage=0;worst=float('inf');speed_min=float('inf');peak=3;head_changes=[];last_head=None
            commands=set();last_source=None;deadline=time.monotonic()+150
            while time.monotonic()<deadline:
                # Set the intended future direction before awaiting that plan.
                # The same controller handle() entry point receives webcam UDP.
                queued=server.snake.queued_scene
                if stage==1 and queued is not None and queued is not last_source:
                    direction=scripted_direction(queued);ctrl.handle(direction)
                    commands.add(direction);last_source=queued
                if server.snake.pending and not server.snake.pending[0].done():time.sleep(.01)
                server._timer_callback();now=server.backend.time();ctrl.update(now)
                gap=minimum_distance(poses());worst=min(worst,gap);assert gap>=.52
                assert not [e for e in events if e['event']=='rejected']
                assert server.snake.deadline_fallbacks==0
                scene=server.snake.scene;program=server.snake.program
                if scene:
                    peak=max(peak,scene.members);assert len(scene.snakes)==1
                    head=scene.actors[0]
                    if last_head is not None and head!=last_head:
                        assert scene.actors[1]==last_head;head_changes.append(head)
                    last_head=head
                else:last_head=None
                if scene and program and program[0].kind in ('move','launch'):
                    for i in scene.actors:
                        v=server.cfs[DRONES[i]].state.velocity
                        speed=math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z)
                        speed_min=min(speed_min,speed);assert speed>.3
                if stage==0 and ctrl.state=='ready':ctrl.handle('peace');stage=1
                elif stage==1 and peak==8 and ctrl.state=='ready':
                    assert not lands;assert bridge.arrival_metrics(poses(),HOME,.2)[0]
                    ctrl.handle('peace');stage=2
                elif stage==2 and ctrl.state=='ready':
                    assert not lands
                    assert any(e['event']=='returning' and e.get('reason','').startswith('No clear') for e in events)
                    ctrl.handle('peace');stage=3
                elif stage==3 and program and program[0].kind=='launch' and now-program[1]>.6:
                    ctrl.handle('palm');stage=4
                elif stage==4 and ctrl.state=='grounded':
                    ctrl.handle('one');assert ctrl.state=='grounded'
                    ctrl.arm();ctrl.handle('one');stage=5
                elif stage==5 and ctrl.state=='ready':ctrl.land('Rearm regression');stage=6
                elif stage==6 and ctrl.state=='grounded':break
            else:raise AssertionError(('Player timeout',stage,ctrl.state,peak,events[-5:]))
            assert peak==8 and len(head_changes)>=5
            assert commands=={'left','right','up','down'}
            assert len(lands)==2 and fleet.go_to_count==0
            report=dict(result='passed',actual_drones=len(server.cfs),maximum_snakes=1,
                initial_members=3,apples_collected_first_game=5,head_identity_changes=head_changes,
                directions=sorted(commands),minimum_center_spacing_m=worst,minimum_body_speed_m_s=speed_min,
                automatic_grid_return=True,restart_from_grid=True,palm_during_growth_landed=True,
                blocked_path_returns_to_grid=True,
                manual_rearm_after_landing=True,deadline_fallbacks=server.snake.deadline_fallbacks,
                commands_streamed_per_frame=False,simulated_seconds=now)
            output=REPORTS_DIR/'play-snake.json'
            output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            print('PLAY_SNAKE_PASS: '+json.dumps(report))
        finally:server.on_shutdown_callback();server.destroy_node();rclpy.try_shutdown()


if __name__=='__main__':main()
