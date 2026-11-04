"""Isolated real-preview-server integration; no external ROS flight commands.

Run with ROS_DOMAIN_ID=88 in WSL. Direct adapters invoke this process's own
simulator callbacks, exercising the firmware planner, asynchronous join and
controller together without depending on external DDS discovery.
"""
import json
import argparse
import random
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import time
import yaml
import rclpy
from rclpy.duration import Duration
from ament_index_python.packages import get_package_share_directory
from crazyflie_interfaces import srv
from crazyflie_interfaces.msg import TrajectoryPolynomialPiece
from preview_server import ContinuousPreviewServer
from smooth_animation_bridge import SmoothAnimationController
from formation_registry import FORMATIONS, GESTURES_BY_SHAPE, validate_speed
from static_shapes import DRONES, COUNT, HOME, minimum_distance
import gesture_bridge as bridge
from formation_colors import ColorAnimator


class Drone:
    def __init__(self,fleet,name):self.fleet,self.name=fleet,name
    def goTo(self,point,yaw,duration):
        self.fleet.go_to_count+=1
        request=srv.GoTo.Request()
        request.goal.x,request.goal.y,request.goal.z=point
        request.yaw=yaw;request.duration=Duration(seconds=duration).to_msg()
        self.fleet.server._go_to_callback(request,srv.GoTo.Response(),self.name)
    def uploadTrajectory(self,trajectory_id,offset,trajectory):
        request=srv.UploadTrajectory.Request()
        request.trajectory_id=trajectory_id;request.piece_offset=offset
        for polynomial in trajectory.polynomials:
            piece=TrajectoryPolynomialPiece()
            piece.duration=Duration(seconds=polynomial.duration).to_msg()
            piece.poly_x=polynomial.px.p.tolist();piece.poly_y=polynomial.py.p.tolist()
            piece.poly_z=polynomial.pz.p.tolist();piece.poly_yaw=polynomial.pyaw.p.tolist()
            request.pieces.append(piece)
        self.fleet.server._upload_trajectory_callback(request,srv.UploadTrajectory.Response(),self.name)


class Fleet:
    def __init__(self,server):
        self.server=server;self.go_to_count=0
        self.crazyfliesByName={name:Drone(self,name) for name in DRONES}
    def takeoff(self,targetHeight,duration):
        request=srv.Takeoff.Request();request.height=targetHeight
        request.duration=Duration(seconds=duration).to_msg()
        self.server._takeoff_callback(request,srv.Takeoff.Response())
    def land(self,targetHeight,duration):
        request=srv.Land.Request();request.height=targetHeight
        request.duration=Duration(seconds=duration).to_msg()
        self.server._land_callback(request,srv.Land.Response())
    def startTrajectory(self,trajectory_id,relative=False):
        request=srv.StartTrajectory.Request();request.trajectory_id=trajectory_id
        request.relative=relative;request.timescale=1.
        self.server._start_trajectory_callback(request,srv.StartTrajectory.Response())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--speed',type=float,default=1.)
    modes=parser.add_mutually_exclusive_group()
    modes.add_argument('--demo-rounds',type=int,default=0)
    modes.add_argument('--switches',type=int,default=0,help='Seeded random timed formation changes')
    parser.add_argument('--seed',type=int,default=20261102)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    speed=validate_speed(args.speed)
    if args.demo_rounds<0 or args.switches<0:parser.error('Counts must be nonnegative')
    rng=random.Random(args.seed)
    if os.environ.get('ROS_DOMAIN_ID')!='88':
        raise SystemExit('Run this isolated check with ROS_DOMAIN_ID=88; it must not share the live project domain.')
    share=Path(get_package_share_directory('crazyflie'))
    params=yaml.safe_load((share/'config/server.yaml').read_text())['/crazyflie_server']['ros__parameters']
    params.update(yaml.safe_load((Path(__file__).parent/'config/crazyflies.yaml').read_text()))
    params['sim'].update(backend='none',controller='none',max_dt=.02)
    params['robot_description']=(Path(get_package_share_directory('crazyflie_description'))/'urdf/crazyflie_description.urdf').read_text()
    with TemporaryDirectory() as tmp:
        config=Path(tmp)/'server.yaml'
        config.write_text(yaml.safe_dump({'/crazyflie_server':{'ros__parameters':params}}))
        rclpy.init(args=['--ros-args','--params-file',str(config),'--log-level','error'])
        server=ContinuousPreviewServer()
        try:
            for cf in server.cfs.values():
                cf.setpoint.position.x,cf.setpoint.position.y,cf.setpoint.position.z=map(float,cf.initialPosition)
            fleet=Fleet(server)
            def points():
                return tuple((server.cfs[n].state.position.x,server.cfs[n].state.position.y,server.cfs[n].state.position.z) for n in DRONES)
            class Feedback:
                def at(self,goals,tolerance=.2):return bridge.arrival_metrics(points(),goals,tolerance)[0]
                def __call__(self):return self.at(HOME)
                def snapshot(self):return points()
            swarm=SimpleNamespace(allcfs=fleet,timeHelper=SimpleNamespace(time=server.backend.time))
            ctrl=SmoothAnimationController(swarm,Feedback())
            ctrl.continuous=ctrl.use_blends=True
            ctrl.route_min_sec,ctrl.route_speed=1.,1.6
            events=[]
            def status(state,target,**details):
                events.append(dict(state=state,target=target,**details))
                ctrl._receive_blend(SimpleNamespace(data=json.dumps(events[-1])))
            server._blend_event=status
            # Exercise the same grounded speed command and upload path as users.
            ctrl.keyboard_command(f'speed {speed}')
            assert ctrl.speed==speed and not ctrl.armed
            bridge.set_fast_test_timing(True)
            ctrl.arm();ctrl.handle('one')
            color_animator=ColorAnimator()
            heart_brightness=[];wave_color_samples=0;spiral_scales=[];spiral_phases=[];moon_fractions=[]
            stage=0;spiral_until=None;moon_until=None;random_due=None;worst=float('inf');min_airborne_height=float('inf')
            deadline=time.monotonic()+max(45,10*(args.switches+len(FORMATIONS)*args.demo_rounds))
            while time.monotonic()<deadline:
                if server.blend_job:time.sleep(.003)
                server._timer_callback();now=server.backend.time();ctrl.update(now)
                gap=minimum_distance(points());worst=min(worst,gap)
                colors=color_animator.update(points(),now)
                if now-color_animator.fade_start>=color_animator.fade_sec:
                    if color_animator.frame.shape=='heart':heart_brightness.append(colors[0][0])
                    elif color_animator.frame.shape=='sine':
                        crest=max(range(COUNT),key=lambda i:points()[i][2])
                        assert max(colors[crest])>=max(max(c) for c in colors)-1e-5
                        wave_color_samples+=1
                    elif color_animator.frame.shape=='spiral' and ctrl.shape=='spiral' and ctrl.smooth_running:
                        spiral_scales.append(color_animator.frame.scale)
                        spiral_phases.append(color_animator.frame.phase)
                    elif color_animator.frame.shape=='moon' and ctrl.shape=='moon' and ctrl.smooth_running:
                        moon_fractions.append(color_animator.frame.scale)
                assert gap>=.52,(stage,gap)
                assert not any(e['state']=='rejected' for e in events),events
                if ctrl.state in ('ready','showing','blending','to_shape','to_grid'):
                    min_airborne_height=min(min_airborne_height,min(p[2] for p in points()))
                    assert min_airborne_height>.6,min_airborne_height
                completed=[e for e in events if e['state']=='completed']
                if args.demo_rounds or args.switches:
                    if stage==0 and ctrl.state=='ready':
                        if args.demo_rounds:ctrl.keyboard_command('demo')
                        else:ctrl.handle('peace')
                        stage=1
                    elif stage==1:
                        assert fleet.go_to_count==COUNT,'Demo/switch issued an intermediate waypoint'
                        if len(completed)>=(len(FORMATIONS)*args.demo_rounds or args.switches) and ctrl.state=='showing':
                            ctrl.keyboard_command('demo off')
                            ctrl.land('Validation');stage=6
                        elif args.switches and ctrl.state=='showing' and ctrl.smooth_running:
                            if random_due is None:random_due=now+rng.uniform(.05,ctrl.period(ctrl.shape)*1.4)
                            if now>=random_due:
                                target=rng.choice([s for s in FORMATIONS if s!=ctrl.shape])
                                ctrl.handle(GESTURES_BY_SHAPE[target]);random_due=None
                    elif stage==6 and ctrl.state=='grounded':break
                    continue
                if stage==0 and ctrl.state=='ready':ctrl.handle('peace');stage=1
                elif stage==1 and ctrl.smooth_running and now-ctrl.program_started>4.2:
                    ctrl.handle('three');stage=2
                elif stage==2 and ctrl.shape=='sine' and ctrl.smooth_running:
                    assert fleet.go_to_count==COUNT,'Separate brake/waypoint command was issued'
                    next_at=now+1.;stage=3
                elif stage==3 and now>=next_at:ctrl.handle('ok');stage=4
                elif stage==4 and ctrl.shape=='spiral' and ctrl.state=='showing':
                    assert fleet.go_to_count==COUNT
                    assert ctrl.smooth_running
                    if spiral_until is None:spiral_until=now+1.3*ctrl.period('spiral')
                    if now>=spiral_until:
                        ctrl.handle('moon');stage=7
                elif stage==7 and ctrl.shape=='moon' and ctrl.smooth_running:
                    assert fleet.go_to_count==COUNT
                    if moon_until is None:moon_until=now+1.2*ctrl.period('moon')
                    if now>=moon_until:ctrl.handle('peace');stage=5
                elif stage==5 and ctrl.shape=='heart' and ctrl.smooth_running:
                    assert fleet.go_to_count==COUNT
                    ctrl.handle('palm');stage=6
                elif stage==6 and ctrl.state=='grounded':break
            else:raise AssertionError(('Integration timeout',ctrl.state,events))
            expected=len(FORMATIONS)*args.demo_rounds or args.switches or len(FORMATIONS)
            assert len(completed)==expected,events
            if args.demo_rounds:
                assert [e['target'] for e in completed]==(list(FORMATIONS)[1:]+list(FORMATIONS)[:1])*args.demo_rounds
            if not args.switches:
                assert max(heart_brightness)-min(heart_brightness)>.4,heart_brightness
                assert wave_color_samples>=5,wave_color_samples
                assert max(spiral_scales)-min(spiral_scales)<1e-5,spiral_scales
                assert max(spiral_phases)-min(spiral_phases)>2.8,spiral_phases
                assert max(moon_fractions)-min(moon_fractions)>.95,moon_fractions
            report=dict(result='passed',speed=speed,demo_rounds=args.demo_rounds,seed=args.seed,
                        completed_transitions=len(completed),simulated_seconds=now,
                        minimum_center_spacing_m=worst,minimum_airborne_height_m=min_airborne_height,
                        wave_color_frames=wave_color_samples,targets=[e['target'] for e in completed])
            if args.report:
                args.report.parent.mkdir(parents=True,exist_ok=True)
                args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            print(f'ISOLATED_PREVIEW_PASS: {len(completed)} transitions at {speed:g}x, {now:.1f} simulation seconds, grid landing; '
                  f'no intermediate goTo commands; minimum measured center spacing {worst:.3f}m')
            print(f'COLOR_SYNC_PASS: heart brightness follows size; rainbow follows wave over {wave_color_samples} frames; gold-purple tracks constant-size spiral; moon follows half/full outline.')
        finally:
            server.on_shutdown_callback();server.destroy_node();rclpy.try_shutdown()


if __name__=='__main__':main()
