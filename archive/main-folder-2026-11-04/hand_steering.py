"""Four webcam steering zones with a neutral center and short dwell/debounce."""
import math


class HandSteering:
    def __init__(self,hold=.15,repeat=.35):
        self.hold,self.repeat=hold,repeat
        self.candidate=None;self.since=0.;self.last_sent=-float('inf')

    def update(self,x,y,now,pointing=True):
        direction=None
        if pointing and x is not None and y is not None and all(math.isfinite(v) for v in (x,y)):
            dx,dy=x-.5,y-.5
            if max(abs(dx),abs(dy))>=.18:
                direction=('right' if dx>0 else 'left') if abs(dx)>=abs(dy) else ('down' if dy>0 else 'up')
        if direction!=self.candidate:
            self.candidate=direction;self.since=now;self.last_sent=-float('inf')
        if direction and now-self.since>=self.hold and now-self.last_sent>=self.repeat:
            self.last_sent=now;return direction
        return None
