"""Autonomous grid-game scheduler with finite certified native trajectories."""
import math
import cffirmware as firm
from crazyflie_sim.crazyflie_sil import TrajectoryPolynomialPiece
from static_shapes import COUNT,DRONES,HOME
from scenes.snake import SnakeScene,arrange_plan,return_plan,step_plan,validate_limit
from scenes.trajectories import rest

LEAD=.60


def build(kind,start,scene,payload):
    if kind=='start':return arrange_plan(start,SnakeScene(limit=payload['limit'],seed=payload.get('seed',31)))
    if kind=='return':return return_plan(start)
    return step_plan(scene)


class SnakeRuntime:
    def __init__(self,server):
        self.server=server
        self.scene=self.program=self.pending=None
        self.return_requested=False
        self.paused=False
        self.last_publish=-1.

    def emit(self,event,**details):
        scene=self.scene or (self.program[0].after if self.program else None)
        kind=self.program[0].kind if self.program else None
        state=('returning to grid' if self.return_requested or kind=='grid' else
               'eating and growing' if kind=='eat' else 'playing automatically' if kind=='move' else
               'moving onto board' if kind=='arrange' else 'holding safely' if self.paused else
               'planning' if self.pending else 'grid')
        self.server.scene_event(dict(event=event,state=state,members=scene.members if scene else 0,
            limit=scene.limit if scene else 19,roles=scene.roles() if scene else ('parked',)*COUNT,
            score=scene.score if scene else 0,moves=scene.moves if scene else 0,
            food=scene.food if scene else None,body=scene.body if scene else (),**details))

    def native_states(self,when):
        result=[]
        for name in DRONES:
            ev=firm.plan_current_goal(self.server.cfs[name].planner,when)
            result.append(tuple(tuple(getattr(v,k) for k in ('x','y','z')) for v in (ev.pos,ev.vel,ev.acc)))
        return tuple(result)

    def future_states(self,when):
        if self.program:
            plan,start=self.program
            if when>=start+plan.duration:
                return plan.after.states() if plan.after else tuple(rest(p) for p in HOME)
        return self.native_states(when)

    def command(self,data):
        kind=data.get('action')
        if kind=='return':
            self.return_requested=True
            if self.pending:self.pending[0].cancel();self.pending=None
            if not self.program:self.submit('return',{})
            return
        if kind!='start':raise ValueError('Grid Snake plays and collects automatically; use start or return')
        if self.program or self.pending or self.scene:raise ValueError('Snake is already running')
        validate_limit(data.get('limit'))
        if isinstance(data.get('seed',31),bool) or not isinstance(data.get('seed',31),int):raise ValueError('Seed must be an integer')
        states=self.native_states(self.server.backend.time())
        if max(math.dist(s[0],p) for s,p in zip(states,HOME))>.2:
            raise ValueError('Take off to the airborne grid before starting Snake')
        self.paused=False;self.return_requested=False
        self.submit('start',data)

    def submit(self,kind,payload,when=None,scene=None):
        when=self.server.backend.time()+LEAD if when is None else when
        states=scene.states() if kind=='step' else self.future_states(when)
        future=self.server.blend_worker.submit(build,kind,states,scene,payload)
        self.pending=(future,when,kind,payload,states)
        if kind!='step':self.emit('planning',action=kind)

    def install(self,plan,start):
        trajectory_id=110 if len(plan.paths[0])==3 else 111
        for name,path in zip(DRONES,plan.paths):
            cf=self.server.cfs[name]
            if trajectory_id not in cf.trajectories:
                cf.uploadTrajectory(trajectory_id,0,[TrajectoryPolynomialPiece(*p.axes,(0.,)*8,p.duration) for p in path])
            else:
                native=cf.trajectories[trajectory_id]
                for i,piece in enumerate(path):
                    item=firm.piecewise_get(native,i);item.duration=piece.duration
                    for axis,coefficients in enumerate((*piece.axes,(0.,)*8)):
                        for j,value in enumerate(coefficients):firm.poly4d_set(item,axis,j,value)
            trajectory=cf.trajectories[trajectory_id]
            trajectory.t_begin=start;trajectory.timescale=1.
            firm.plan_start_trajectory(cf.planner,trajectory,False,False,cf.cmdHl_pos)
        self.program=(plan,start)
        if plan.after is not None and not self.return_requested:
            self.submit('step',{},when=start+plan.duration,scene=plan.after)

    def update(self,now):
        if self.program:
            plan,start=self.program
            if now+1e-8>=start+plan.duration:
                self.program=None;self.scene=plan.after
                self.emit('grid' if plan.kind=='grid' else 'collected' if plan.kind=='eat' else 'playing')
                if plan.kind=='grid':self.return_requested=False
                elif self.return_requested and not self.pending:self.submit('return',{})
        if self.pending:
            future,start,kind,payload,expected=self.pending
            if future.done():
                try:plan=future.result()
                except Exception as error:
                    self.pending=None;self.paused=True
                    self.emit('rejected',action=kind,reason=str(error))
                else:
                    # Firmware stores piece durations at lower precision.
                    # Allow one 50 Hz rest tick at a grid node so a nominal
                    # endpoint is not sampled just before the native endpoint.
                    if now+1e-8>=start+(.02 if kind=='step' else 0.):
                        # Grid nodes are C2 rest states. A late worker may hold
                        # there safely; it never skips into the middle of a move.
                        actual=self.native_states(now)
                        error=max(math.dist(a[d],b[d]) for a,b in zip(expected,actual) for d in range(3))
                        self.pending=None
                        if error>1e-4:
                            self.paused=True
                            self.emit('rejected',action=kind,reason=f'Source state changed ({error:.6g}); board held safely')
                        else:
                            self.install(plan,now)
                            if kind!='step':self.emit('started',action=kind,bound=plan.bound)
        if now-self.last_publish>=.2:
            self.last_publish=now;self.emit('state')

    def clear(self):
        if self.pending:self.pending[0].cancel()
        self.pending=self.program=self.scene=None
        self.return_requested=False;self.paused=False
