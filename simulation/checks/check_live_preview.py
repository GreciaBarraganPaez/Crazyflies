"""Live ideal-preview smoke check. Stop the interactive bridge first.

This deliberately arms and moves simulated drones. It refuses a non-ideal backend
and reserves UDP 5055 to prevent a concurrent gesture bridge. Never a physics or
hardware collision-avoidance validation.
"""
import socket
bridge_lock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
try:
    bridge_lock.bind(('0.0.0.0',5055))
except OSError:
    raise RuntimeError('Stop the gesture bridge before running the live preview check')
import time,math
import rclpy
from rclpy.parameter_client import AsyncParameterClient
from rclpy.time import Time
from crazyflie_py import Crazyswarm
import simulation.controllers.gesture_bridge as bridge
from simulation.controllers.gesture_bridge import GridArrivalMonitor
from simulation.controllers.smooth_animation_bridge import SmoothAnimationController as FormationAnimationController
from simulation.core.continuous_trajectories import PERIODS
from simulation.controllers.heart_animation_bridge import heart_targets
from simulation.core.static_shapes import DRONES,HOME,minimum_distance,targets
swarm=Crazyswarm();node=swarm.allcfs
params=AsyncParameterClient(node,'crazyflie_server');assert params.wait_for_services(timeout_sec=3)
f=params.get_parameters(['sim.backend']);rclpy.spin_until_future_complete(node,f,timeout_sec=3)
assert f.done() and f.result().values[0].string_value=='none'
monitor=GridArrivalMonitor(node)
def pump():
    for _ in range(32):rclpy.spin_once(node,timeout_sec=0)
end=time.monotonic()+2
while time.monotonic()<end:pump();time.sleep(.01)
initial=[]
for name in DRONES:
    p=monitor.buffer.lookup_transform('world',name,Time()).transform.translation
    initial.append((p.x,p.y,p.z))
assert max(math.dist(p[:2],(x,y)) for p,(x,y,z) in zip(initial,HOME))<.001 and max(abs(p[2]) for p in initial)<.15, 'Idle preview grid incorrect'
print('Idle preview grid verified: 19 distinct starting positions.',flush=True)
bridge.set_fast_test_timing(True)
ctrl=FormationAnimationController(swarm,monitor);ctrl.configure_backend('none')
starts=[]
start_trajectory=swarm.allcfs.startTrajectory
def record_start(trajectory_id, **kwargs):
    starts.append(trajectory_id)
    return start_trajectory(trajectory_id, **kwargs)
swarm.allcfs.startTrajectory=record_start
ctrl.arm();ctrl.handle('one')
phase=0;last=None;expansions=[];worst=minimum_distance(initial)
startwall=time.monotonic();startsim=swarm.timeHelper.time();deadline=startwall+90
try:
    while time.monotonic()<deadline:
        pump();now=swarm.timeHelper.time();ctrl.update()
        pts=[]
        for name in DRONES:
            p=monitor.buffer.lookup_transform('world',name,Time()).transform.translation
            pts.append((p.x,p.y,p.z))
        worst=min(worst,minimum_distance(pts))
        assert minimum_distance(pts)>=.52, 'Observed spacing below validation limit'
        if phase==0 and ctrl.state=='ready':ctrl.handle('peace');phase=1
        if phase==1 and ctrl.smooth_running:
            if now-ctrl.program_started>=PERIODS['heart']*2.2:
                print('Continuous heart: entry + loop boundary crossed; period 3.2s.',flush=True)
                ctrl.handle('three');phase=2
        if phase==2:
            assert not ctrl.playback.normalizing, 'Separate stop/align phase was started'
        if phase==2 and ctrl.shape=='sine' and ctrl.state=='showing' and ctrl.smooth_running:
            assert starts.count(70)==1 and starts.count(82)==1 and starts.count(72)==0, starts
            print('SINE_VISIBLE: measured maximum shape error',monitor.last_status,flush=True)
            wave_due=now+PERIODS['sine']*2.1;phase=3
        if phase==3 and now>=wave_due:ctrl.handle('palm');phase=4
        if phase==4 and ctrl.state=='grounded':
            ground=tuple((x,y,.04) for x,y,z in HOME)
            if monitor.at(ground,tolerance=.10):
                print(f'LIVE_PREVIEW_PASS: heart -> sine -> grid landing, minimum measured spacing {worst:.3f}m; realtime factor {(now-startsim)/(time.monotonic()-startwall):.2f}',flush=True)
                break
        time.sleep(.015)
    else:raise RuntimeError('Live preview validation timed out')
finally:
    if ctrl.state!='grounded':
        ctrl.land('Validation cleanup')
        end=time.monotonic()+60
        while ctrl.state!='grounded' and time.monotonic()<end:pump();ctrl.update();time.sleep(.02)
