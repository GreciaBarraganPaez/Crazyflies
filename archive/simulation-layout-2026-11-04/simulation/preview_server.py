"""Installed ideal-motion server with idle setpoints initialized to the home grid."""
import rclpy
import cffirmware as firm
import json
from concurrent.futures import ThreadPoolExecutor
import math
from std_msgs.msg import String
from crazyflie_sim.crazyflie_server import CrazyflieServer
from crazyflie_sim.crazyflie_sil import TrajectoryPolynomialPiece
from continuous_trajectories import LOOP_IDS, TRAJECTORY_IDS, PERIODS, Piece
from blended_transitions import BLEND_REQUESTS, BLEND_TRAJECTORY_ID, compile_blend
from static_shapes import DRONES


class ContinuousPreviewServer(CrazyflieServer):
    """Repeat reserved high-level trajectories at exact simulation-time boundaries."""
    def __init__(self):
        self.loops = {}
        self.durations = {}
        self.paths = {}
        self.blend_job = None
        self.blend_active = None
        self.blend_worker = ThreadPoolExecutor(max_workers=1)
        super().__init__()
        self.declare_parameter('swarmgesture.continuous_trajectories', True)
        self.declare_parameter('swarmgesture.blended_transitions', True)
        self.declare_parameter('swarmgesture.spiral_animation', True)
        self.declare_parameter('swarmgesture.playback_controls', True)
        self.declare_parameter('swarmgesture.moon_animation', True)
        self.declare_parameter('swarmgesture.helix_animation', True)
        self.blend_status = self.create_publisher(String,'/swarmgesture/transition_status',10)
        self.backend.dt = .02

    def _names(self, name):
        return tuple(self.cfs) if name == 'all' else (name,)

    def _upload_trajectory_callback(self, request, response, name='all'):
        result = super()._upload_trajectory_callback(request, response, name)
        duration = sum(p.duration.sec+p.duration.nanosec/1e9 for p in request.pieces)
        for key in self._names(name):
            self.durations[key, request.trajectory_id] = duration
            self.paths[key, request.trajectory_id] = tuple(
                Piece(p.duration.sec+p.duration.nanosec/1e9,
                      (tuple(p.poly_x),tuple(p.poly_y),tuple(p.poly_z))) for p in request.pieces)
        return result

    def _start_trajectory_callback(self, request, response, name='all'):
        if request.trajectory_id in BLEND_REQUESTS:
            target=BLEND_REQUESTS[request.trajectory_id]
            if name!='all' or request.relative or request.reversed or request.timescale!=1.0:
                self._blend_event('rejected',target,reason='Blend requires an absolute complete-fleet request')
            elif self.blend_job or self.blend_active:
                self._blend_event('rejected',target,reason='A blend is already pending/running')
            else:
                self._submit_blend(target)
            return response
        result = super()._start_trajectory_callback(request, response, name)
        for key in self._names(name):
            self.loops.pop(key, None)
            if request.trajectory_id in LOOP_IDS:
                loop = LOOP_IDS[request.trajectory_id]
                if (key, loop) not in self.durations:
                    raise RuntimeError('Upload both entry and loop before starting continuous playback')
                due = self.backend.time() + self.durations[key, request.trajectory_id]
                self.loops[key] = (loop, due)
        return result

    def _blend_event(self, state, target, **details):
        message=String()
        message.data=json.dumps(dict(state=state,target=target,**details))
        self.blend_status.publish(message)

    def _future_state(self, key, when):
        if key in self.loops:
            loop,due=self.loops[key]
            if when>=due:
                t=(when-due)%self.durations[key,loop]
                for piece in self.paths[key,loop]:
                    if t<=piece.duration+1e-9:
                        return tuple(piece.evaluate(min(t,piece.duration),d) for d in range(3))
                    t-=piece.duration
        ev=firm.plan_current_goal(self.cfs[key].planner,when)
        return tuple(tuple(getattr(v,axis) for axis in ('x','y','z')) for v in (ev.pos,ev.vel,ev.acc))

    def _submit_blend(self, target, attempt=0):
        try:
            start=self.backend.time()+.30
            states=tuple(self._future_state(key,start) for key in DRONES)
            loop=TRAJECTORY_IDS[target][1]
            durations=[self.durations[key,loop] for key in DRONES]
            if max(durations)-min(durations)>1e-7:
                raise ValueError('Fleet loop durations disagree; re-upload all animations while grounded')
            speed=round(PERIODS[target]/durations[0],9)
            future=self.blend_worker.submit(compile_blend,states,target,speed)
            self.blend_job=(future,start,target,attempt)
            self._blend_event('planning',target)
        except Exception as error:
            self._blend_event('rejected',target,reason=str(error))

    def _install_blend(self, key, path):
        cf=self.cfs[key]
        if BLEND_TRAJECTORY_ID not in cf.trajectories:
            cf.uploadTrajectory(BLEND_TRAJECTORY_ID,0,
                [TrajectoryPolynomialPiece(*p.axes,(0.,)*8,p.duration) for p in path])
        else:
            trajectory=cf.trajectories[BLEND_TRAJECTORY_ID]
            # Three pieces are reused, avoiding a native allocation on each switch.
            for i,piece in enumerate(path):
                native=firm.piecewise_get(trajectory,i)
                native.duration=piece.duration
                for axis,coefficients in enumerate((*piece.axes,(0.,)*8)):
                    for j,value in enumerate(coefficients):firm.poly4d_set(native,axis,j,value)
        cf.startTrajectory(BLEND_TRAJECTORY_ID,relative=False)

    def _update_blend(self, now):
        if self.blend_job:
            future,start,target,attempt=self.blend_job
            if future.done():
                try: plan=future.result()
                except Exception as error:
                    self.blend_job=None
                    self._blend_event('rejected',target,reason=str(error))
                else:
                    if now>start+.01:
                        self.blend_job=None
                        if attempt<2:self._submit_blend(target,attempt+1)
                        else:self._blend_event('rejected',target,reason='Planner missed the scheduled join; old motion retained')
                    elif now+1e-8>=start:
                        actual=tuple(self._future_state(key,now) for key in DRONES)
                        error=max(math.dist(path[0].evaluate(0,d),state[d])
                                  for path,state in zip(plan.paths,actual) for d in range(3))
                        if error>1e-5:
                            self.blend_job=None
                            if attempt<2:self._submit_blend(target,attempt+1)
                            else:self._blend_event('rejected',target,reason='Source state changed before the join; old motion retained')
                            return
                        self.blend_job=None
                        self.loops.clear()
                        for key,path in zip(DRONES,plan.paths):self._install_blend(key,path)
                        until=now+plan.duration
                        self.blend_active=(until,target)
                        self._blend_event('started',target,start=now,until=until,
                                          clearance_bound=plan.clearance_bound,lanes=plan.lane_count)
        if self.blend_active:
            until,target=self.blend_active
            if now+1e-8>=until:
                # At the first 50 Hz tick after the exact join, start the new
                # loop with its original time origin (no frozen endpoint tick).
                if target in TRAJECTORY_IDS:
                    loop=TRAJECTORY_IDS[target][1]
                    for key in DRONES:
                        cf=self.cfs[key]
                        trajectory=cf.trajectories[loop]
                        trajectory.t_begin=until
                        trajectory.timescale=1.0
                        firm.plan_start_trajectory(cf.planner,trajectory,False,False,cf.cmdHl_pos)
                        self.loops[key]=(loop,until+self.durations[key,loop])
                self.blend_active=None
                self._blend_event('completed',target,until=until)

    def _clear_loops(self, name):
        if self.blend_job:
            future,_,target,_=self.blend_job
            future.cancel()
            self.blend_job=None
            self._blend_event('rejected',target,reason='Superseded by a high-level command')
        if self.blend_active:
            _,target=self.blend_active
            self.blend_active=None
            self._blend_event('rejected',target,reason='Superseded by a high-level command')
        for key in self._names(name):
            self.loops.pop(key, None)

    def _go_to_callback(self, request, response, name='all'):
        self._clear_loops(name)
        return super()._go_to_callback(request, response, name)

    def _land_callback(self, request, response, name='all'):
        self._clear_loops(name)
        return super()._land_callback(request, response, name)

    def _takeoff_callback(self, request, response, name='all'):
        self._clear_loops(name)
        return super()._takeoff_callback(request, response, name)

    def _timer_callback(self):
        now = self.backend.time()
        self._update_blend(now)
        for key, (loop, due) in tuple(self.loops.items()):
            if now + 1e-8 >= due:
                duration = self.durations[key, loop]
                while due + duration <= now + 1e-8:
                    due += duration
                cf = self.cfs[key]
                trajectory = cf.trajectories[loop]
                trajectory.t_begin = due
                trajectory.timescale = 1.0
                firm.plan_start_trajectory(cf.planner, trajectory, False, False, cf.cmdHl_pos)
                self.loops[key] = (loop, due+duration)
        super()._timer_callback()

    def on_shutdown_callback(self):
        self.blend_worker.shutdown(wait=False,cancel_futures=True)
        super().on_shutdown_callback()


def main():
    rclpy.init()
    server = ContinuousPreviewServer()
    if server._ros_parameters['sim']['backend'] != 'none':
        raise RuntimeError('This entry point is only for the ideal preview backend')
    # The installed ideal backend follows even idle setpoints. Firmware's default
    # zero-valued setpoint otherwise collapses the idle fleet at the world origin.
    for cf in server.cfs.values():
        cf.setpoint.position.x = float(cf.initialPosition[0])
        cf.setpoint.position.y = float(cf.initialPosition[1])
        cf.setpoint.position.z = float(cf.initialPosition[2])
    rclpy.get_default_context().on_shutdown(server.on_shutdown_callback)
    try:
        rclpy.spin(server)
    except KeyboardInterrupt:
        server.on_shutdown_callback()
    finally:
        rclpy.try_shutdown()
        server.destroy_node()


if __name__ == '__main__':
    main()
