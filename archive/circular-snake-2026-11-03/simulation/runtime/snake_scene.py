"""Scheduled native scene programs. No per-frame flight-command streaming."""
import math
import cffirmware as firm
from crazyflie_sim.crazyflie_sil import TrajectoryPolynomialPiece
from static_shapes import COUNT, DRONES, HOME
from scenes.snake import SnakeScene, arrange_plan, return_plan, collect_plan, loop_plan, validate_limit
from scenes.trajectories import rest

LEAD=.60


def build(kind,start,when,scene,payload):
    if kind in ('start','turn'):
        target=SnakeScene(members=scene.members if scene else 3,
                          limit=scene.limit if scene else payload['limit'],direction=payload['direction'])
        plan=arrange_plan(start,when,target)
    elif kind=='return':plan=return_plan(start)
    else:plan=collect_plan(start,when,scene,joining=kind=='join')
    loop=loop_plan(plan.after,when+plan.duration) if plan.after else None
    return plan,loop


class SnakeRuntime:
    def __init__(self,server):
        self.server=server
        self.scene=None
        self.program=None
        self.pending=None
        self.retry_after=0.
        self.last_publish=-1.

    def emit(self,event,**details):
        scene=self.scene or (self.program[0].after if self.program else None)
        kind=self.program[0].kind if self.program else 'grid'
        state=('planning' if self.pending else
               'waiting for head' if kind=='loop' and scene and scene.pickup is not None else
               {'loop':'playing','arrange':'moving to track','stage':'moving pickup',
                'join':'joining tail','grid':'grid' if not self.program else 'returning to grid'}[kind])
        self.server.scene_event(dict(event=event,state=state,members=scene.members if scene else 0,
            limit=scene.limit if scene else 5,direction=scene.direction if scene else -1,
            roles=scene.roles() if scene else ('parked',)*COUNT,
            score=scene.members-3 if scene else 0,**details))

    def future_states(self,when):
        if self.program:
            plan,start,_=self.program
            until=start+plan.duration
            if when>=until:
                if plan.after:return plan.after.states(when)
                return tuple(rest(p) for p in HOME)
            # Forecast using the installed firmware representation, including
            # its coefficient precision, just as commitment verification does.
        states=[]
        for name in DRONES:
            ev=firm.plan_current_goal(self.server.cfs[name].planner,when)
            states.append(tuple(tuple(getattr(v,k) for k in ('x','y','z')) for v in (ev.pos,ev.vel,ev.acc)))
        return tuple(states)

    def command(self,data):
        kind=data.get('action')
        if kind not in ('start','turn','collect','return'):raise ValueError('Unknown Snake action')
        if kind=='return':
            if self.pending:self.pending[0].cancel();self.pending=None
            self.submit('return',{})
            return
        if self.pending or (self.program and self.program[0].kind!='loop'):
            raise ValueError('Scene move in progress; wait for it to finish')
        if kind in ('start','turn'):
            if data.get('direction') not in (-1,1):raise ValueError('Direction must be -1 or 1')
        if kind=='start':
            if self.scene is not None:raise ValueError('Snake is already running')
            validate_limit(data.get('limit'))
            points=self.future_states(self.server.backend.time())
            if max(math.dist(s[0],p) for s,p in zip(points,HOME))>.2:
                raise ValueError('Take off to the airborne grid before starting Snake')
        elif not self.scene:raise ValueError('Start Snake first')
        elif kind=='collect' and self.scene.pickup is not None:raise ValueError('Pickup already pending')
        if kind=='collect':kind='stage'
        self.submit(kind,data)

    def submit(self,kind,payload,attempt=0):
        when=self.server.backend.time()+LEAD
        states=self.future_states(when)
        future=self.server.blend_worker.submit(build,kind,states,when,self.scene,payload)
        self.pending=(future,when,kind,payload,states,attempt)
        self.emit('planning',action=kind)

    def install(self,plan,start,next_loop):
        trajectory_id=110 if len(plan.paths[0])==3 else 111
        for name,path in zip(DRONES,plan.paths):
            cf=self.server.cfs[name]
            if trajectory_id not in cf.trajectories:
                cf.uploadTrajectory(trajectory_id,0,
                    [TrajectoryPolynomialPiece(*p.axes,(0.,)*8,p.duration) for p in path])
            else:
                native=cf.trajectories[trajectory_id]
                for i,piece in enumerate(path):
                    item=firm.piecewise_get(native,i);item.duration=piece.duration
                    for axis,coefficients in enumerate((*piece.axes,(0.,)*8)):
                        for j,value in enumerate(coefficients):firm.poly4d_set(item,axis,j,value)
            trajectory=cf.trajectories[trajectory_id]
            trajectory.t_begin=start;trajectory.timescale=1.
            firm.plan_start_trajectory(cf.planner,trajectory,False,False,cf.cmdHl_pos)
        self.program=(plan,start,next_loop)

    def advance(self,now):
        if self.program:
            plan,start,next_loop=self.program
            until=start+plan.duration
            if now+1e-8>=until:
                self.scene=plan.after
                if next_loop:self.install(next_loop,until,next_loop)
                else:self.program=None
                if plan.kind!='loop':
                    self.emit('grid' if plan.kind=='grid' else 'collected' if plan.kind=='join' else
                              'pickup_ready' if plan.kind=='stage' else 'playing')

    def update(self,now):
        self.advance(now)
        if self.pending:
            future,start,kind,payload,expected,attempt=self.pending
            if future.done():
                try:plan,next_loop=future.result()
                except Exception as error:
                    self.pending=None;self.retry_after=now+2.
                    self.emit('rejected',action=kind,reason=str(error))
                else:
                    if now>start+.01:
                        self.pending=None
                        if attempt<2:self.submit(kind,payload,attempt+1)
                        else:self.emit('rejected',action=kind,reason='Planner missed scheduled join; motion retained')
                    elif now+1e-8>=start:
                        actual=[]
                        for name in DRONES:
                            ev=firm.plan_current_goal(self.server.cfs[name].planner,now)
                            actual.append(tuple(tuple(getattr(v,k) for k in ('x','y','z')) for v in (ev.pos,ev.vel,ev.acc)))
                        error=max(math.dist(a[d],b[d]) for a,b in zip(expected,actual) for d in range(3))
                        self.pending=None
                        if error>1e-5:
                            if attempt<2:self.submit(kind,payload,attempt+1)
                            else:self.emit('rejected',action=kind,reason=f'Source state changed ({error:.6g}); motion retained')
                        else:
                            self.install(plan,start,next_loop)
                            self.emit('started',action=kind,bound=plan.bound)
        if (self.scene and self.program and self.program[0].kind=='loop' and not self.pending
                and now>=self.retry_after and self.scene.can_collect(now+LEAD)):
            self.submit('join',{})
        if now-self.last_publish>=.2:
            self.last_publish=now;self.emit('state')

    def clear(self):
        if self.pending:self.pending[0].cancel()
        self.pending=self.program=self.scene=None
