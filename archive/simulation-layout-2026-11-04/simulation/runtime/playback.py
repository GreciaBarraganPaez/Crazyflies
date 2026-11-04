"""Native continuous playback and canonical normalization before grid return."""
from continuous_trajectories import TRAJECTORY_IDS, motion
from static_shapes import DRONES, targets
import gesture_bridge as bridge


class ContinuousPlayback:
    def __init__(self,flight):
        self.flight=flight
        self.running=False
        self.started=0.
        self.stop_request=None
        self.normalizing=False
        self.due=0.

    def start(self,now):
        c=self.flight
        c.swarm.allcfs.startTrajectory(TRAJECTORY_IDS[c.shape][0],relative=False)
        self.started=now
        self.running=True
        print(f'CONTINUOUS {c.shape.upper()} started; period={c.period(c.shape):.1f}s.',flush=True)

    def request_stop(self,label):
        if self.stop_request!='palm':self.stop_request=label
        if self.stop_request=='palm':self.flight.armed=False

    def update(self,now):
        c=self.flight
        if self.normalizing:
            if now<self.due:return True
            feedback=getattr(c.grid_arrived,'at',None)
            if feedback is not None and not feedback(c.current_goals,tolerance=.10):return True
            self.normalizing=False
            label,self.stop_request=self.stop_request,None
            queued,c.queued_gesture=c.queued_gesture,None
            c._start_grid(now,next_shape=bridge.SHAPE_GESTURES.get(queued) if label!='palm' else None,
                          land=label=='palm')
            return True
        if not self.running:return False
        elapsed=max(0.,now-self.started)
        period=c.period(c.shape)
        entry=elapsed<period
        phase=elapsed if entry else (elapsed-period)%period
        c.current_goals=tuple(s[0] for s in motion(c.shape,phase,entry,c.speed))
        if self.stop_request:
            # Native high-level goTo starts from the firmware's current p/v/a.
            # Its intermediate curves are verified by the firmware stop checks.
            goals=targets(c.shape)
            for name,point in zip(DRONES,goals):
                c.by_name[name].goTo(list(point),yaw=0.,duration=1.)
            c.current_goals=goals
            self.running=False
            self.normalizing=True
            self.due=now+1.+bridge.MARGIN_SEC
            c.due=self.due
            print('Restoring canonical outline, then verified grid return.',flush=True)
        return True
