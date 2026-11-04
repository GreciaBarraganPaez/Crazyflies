#!/usr/bin/env python3
"""Preview flight lifecycle with separate playback and transition components."""
import gesture_bridge as bridge
from continuous_trajectories import PERIODS, TRAJECTORY_IDS, compile_trajectories, as_ros_trajectory
from static_shapes import DRONES
from formation_registry import FORMATIONS, GESTURES_BY_SHAPE, validate_speed
from playback_controls import DemoSequence
from runtime.playback import ContinuousPlayback
from runtime.joined_transitions import JoinedTransitions


class SmoothAnimationController(bridge.SimulationController):
    def __init__(self,swarm,grid_arrived=None):
        super().__init__(swarm,grid_arrived)
        self.continuous=False
        self.use_blends=False
        self.speed=1.
        self.demo=DemoSequence()
        self._demo_dispatch=False
        self.playback=ContinuousPlayback(self)
        self.transitions=JoinedTransitions(self)

    # Compatibility for the existing preview checks; storage belongs to playback.
    smooth_running=property(lambda s:s.playback.running,lambda s,v:setattr(s.playback,'running',v))
    program_started=property(lambda s:s.playback.started,lambda s,v:setattr(s.playback,'started',v))
    stop_request=property(lambda s:s.playback.stop_request,lambda s,v:setattr(s.playback,'stop_request',v))
    pulse_busy=property(lambda s:s.playback.running or s.playback.normalizing,
                        lambda s,v:setattr(s.playback,'running',v))
    blend_queued=property(lambda s:s.transitions.queued)

    def period(self, shape):
        return PERIODS[shape]/self.speed

    def keyboard_command(self, command):
        words=command.split()
        if not words:return
        if words[0]=='speed':
            if len(words)!=2:
                print('Use speed 0.75, speed 1, or speed 1.25 while grounded.',flush=True)
                return
            try: speed=validate_speed(words[1])
            except ValueError as error:
                print(str(error),flush=True);return
            if not self.continuous or self.state!='grounded':
                print('Speed changes require the continuous preview and grounded drones. Land first.',flush=True)
                return
            self.armed=False
            self.demo.stop()
            self._upload_animations(speed)
            print(f'Animation speed={self.speed:g}x. Takeoff, transitions and landing keep their normal timing. Arm again with a.',flush=True)
        elif words[0]=='demo':
            if words in (['demo','off'],['demo','stop']):
                self.demo.stop()
                print('Demo off; current formation keeps running.',flush=True)
            elif words in (['demo'],['demo','on']):
                if not self.use_blends or self.state not in ('ready','showing') or self.stop_request:
                    print('Demo requires the continuous preview and an airborne grid or running formation. Arm and take off manually first.',flush=True)
                    return
                self.demo.start()
                print(f"Demo on: {' -> '.join(FORMATIONS)}. Any gesture or landing request cancels it.",flush=True)
            else:print('Use demo or demo off.',flush=True)
        elif words[0] in FORMATIONS and len(words)==1:
            self.handle(GESTURES_BY_SHAPE[words[0]])
        elif words[0]=='status':
            print(f'State={self.state}; formation={self.shape}; speed={self.speed:g}x; demo={"on" if self.demo.active else "off"}.',flush=True)
        else:
            print('Preview controls: speed 0.5..1.25 (grounded); demo / demo off (airborne); moon / helix (airborne); status. Enter each command on its own line.',flush=True)

    def configure_backend(self, backend):
        if backend != 'none':
            from formation_animation_bridge import FormationAnimationController
            fallback=FormationAnimationController(self.swarm,self.grid_arrived)
            fallback.configure_backend(backend)
            return fallback
        import rclpy
        from rclpy.parameter_client import AsyncParameterClient
        client = AsyncParameterClient(self.swarm.allcfs, 'crazyflie_server')
        if not client.wait_for_services(timeout_sec=2):
            raise RuntimeError('Preview parameter services unavailable')
        future = client.get_parameters(['swarmgesture.continuous_trajectories','swarmgesture.blended_transitions','swarmgesture.spiral_animation','swarmgesture.playback_controls','swarmgesture.moon_animation','swarmgesture.helix_animation'])
        rclpy.spin_until_future_complete(self.swarm.allcfs, future, timeout_sec=2)
        if not future.done() or future.exception() or not all(p.bool_value for p in future.result().values):
            raise RuntimeError('Restart the ROS preview terminal to load the 3D helix and formation playback support')
        from std_msgs.msg import String
        self.blend_subscription=self.swarm.allcfs.create_subscription(String,'/swarmgesture/transition_status',self._receive_blend,10)
        self._upload_animations(self.speed)
        self.continuous = True
        self.use_blends = True
        print('CONTINUOUS PREVIEW: 50 Hz playback; heart passes through middle size; '
              'wave flows continuously; spiral rotates at constant size; moon waxes and wanes; helix flows in 3D.', flush=True)

    def _upload_animations(self, speed):
        for shape, (entry, loop) in TRAJECTORY_IDS.items():
            for trajectory_id, is_entry in ((loop, False), (entry, True)):
                paths = compile_trajectories(shape, entry=is_entry, speed=speed)
                for name, pieces in zip(DRONES, paths):
                    self.by_name[name].uploadTrajectory(trajectory_id, 0, as_ros_trajectory(pieces))
            print(f'Uploaded continuous {shape}: period={PERIODS[shape]/speed:.1f}s, '
                  'position/velocity/acceleration joined across pieces.', flush=True)
        self.speed=speed

    def _receive_blend(self,message):
        self.transitions.receive(message)

    def handle(self,label,now=None,_from_demo=False):
        if not _from_demo:self.demo.stop()
        now=self.clock() if now is None else now
        if self.state=='blending':
            if label in bridge.SHAPE_GESTURES or label in ('palm','fist'):
                self.transitions.queue(label)
            return
        if self.playback.normalizing or self.playback.stop_request:
            if label in ('palm','fist'):
                self.playback.request_stop(label)
                if label=='palm':self.queued_gesture=None
            elif label in bridge.SHAPE_GESTURES and self.playback.stop_request!='palm':
                self.queued_gesture=label
            return
        if self.queued_gesture=='palm' and label!='palm':return
        if self.state=='to_shape' and (label in bridge.SHAPE_GESTURES or label in ('palm','fist')):
            self.queued_gesture=label
            self.update(now)
            return
        if self.state=='showing' and not self.playback.running and label in bridge.SHAPE_GESTURES:
            target=bridge.SHAPE_GESTURES[label]
            if target!=self.shape:
                self.transitions.begin(target)
                return
        self.update(now)
        if self.playback.normalizing:return
        if self.state=='showing' and self.shape:
            target=bridge.SHAPE_GESTURES.get(label)
            if target and target!=self.shape:self.transitions.begin(target)
            elif label in ('palm','fist'):self.playback.request_stop(label)
            return
        super().handle(label,now)

    def land(self,reason='Land',now=None):
        self.demo.stop()
        self.armed=False
        if self.state=='blending':
            self.transitions.queue('palm')
            return
        if self.playback.running or self.playback.normalizing:
            self.playback.request_stop('palm')
            return
        if self.state=='to_shape':
            self.queued_gesture='palm'
            return
        if self.state=='showing' and self.shape:
            self._start_grid(self.clock() if now is None else now,land=True)
            return
        super().land(reason,now)

    def _start_grid(self,now,next_shape=None,land=False):
        if next_shape and not land and self.state=='showing' and self.shape:
            self.transitions.begin(next_shape)
            return
        super()._start_grid(now,next_shape,land)

    def update(self,now=None):
        now=self.clock() if now is None else now
        if self.state=='to_shape' and now>=self.due and self.queued_gesture:
            label,self.queued_gesture=self.queued_gesture,None
            self.state='showing'
            target=bridge.SHAPE_GESTURES.get(label)
            if target and target!=self.shape:self.transitions.begin(target)
            elif label in ('palm','fist'):self._start_grid(now,land=label=='palm')
        if self.state=='blending':self.transitions.update(now)
        elif not self.playback.update(now):
            super().update(now)
            if (self.continuous and self.state=='showing' and self.shape in FORMATIONS
                    and not self.playback.running and not self.queued_gesture):
                self.playback.start(now)
        if self._demo_dispatch:return
        label=self.demo.poll(self.state,self.shape,self.playback.running,now,
                             self.period(self.shape) if self.shape in PERIODS else 0.)
        if label:
            self._demo_dispatch=True
            try:self.handle(label,now,_from_demo=True)
            finally:self._demo_dispatch=False


if __name__=='__main__':
    bridge.ACTIONS.update({f.gesture:f'continuous {f.name}' for f in FORMATIONS.values()})
    bridge.main(controller_type=SmoothAnimationController)
