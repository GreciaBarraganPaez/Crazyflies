"""Autonomous grid-game scheduler with finite certified native trajectories."""
import math
import cffirmware as firm
from crazyflie_sim.crazyflie_sil import TrajectoryPolynomialPiece
from static_shapes import COUNT,DRONES,HOME
from scenes.snake import SnakeScene,arrange_plan,return_plan,step_plan,validate_limit,MAX_MEMBERS,BORDER_IDS
from scenes.trajectories import rest

LEAD=.60


def build(kind,start,scene,payload):
    if kind=='start':plan=arrange_plan(start,SnakeScene(limit=payload['limit'],seed=payload.get('seed',31)))
    elif kind=='return':plan=return_plan(start)
    else:plan=step_plan(scene)
    exit_plan=return_plan(plan.after.states()) if plan.after is not None else None
    return plan,exit_plan


class SnakeRuntime:
    def __init__(self,server,drone_names=DRONES,home=HOME,builder=build):
        self.server=server
        self.drone_names,self.home,self.builder=drone_names,home,builder
        self.scene_limit=MAX_MEMBERS
        self.scene=self.program=self.pending=None
        self.deadline_fallbacks=0
        self.return_requested=False
        self.paused=False
        self.last_publish=-1.

    def emit(self,event,**details):
        scene=self.scene or (self.program[0].after if self.program else None)
        kind=self.program[0].kind if self.program else None
        display=self.program[0].after if kind in ('eat','split') else scene
        state=('returning to grid' if self.return_requested or kind=='grid' else
               'apple becomes head' if kind=='eat' else 'apple starts moving' if kind=='launch' else
               'splitting into two snakes' if kind=='split' else
               'two snakes hunting' if scene and len(scene.snakes)==2 else
               'playing smoothly' if kind=='move' else 'moving onto board' if kind=='arrange' else
               'holding safely' if self.paused else 'planning' if self.pending else 'grid')
        idle_roles=tuple('border' if i in BORDER_IDS else 'parked' for i in range(len(self.drone_names)))
        self.server.scene_event(dict(event=event,state=state,members=display.members if display else 0,
            limit=display.limit if display else self.scene_limit,roles=display.roles() if display else idle_roles,
            head_id=display.actors[0] if display else None,body_ids=display.actors if display else (),
            head_ids=display.heads if display else (),snake_lengths=[len(s.actors) for s in display.snakes] if display else [],
            score=scene.score if scene else 0,moves=scene.moves if scene else 0,
            food_cells=display.food_cells if display else [],
            body=scene.body if scene else (),**details))

    def native_states(self,when):
        result=[]
        for name in self.drone_names:
            ev=firm.plan_current_goal(self.server.cfs[name].planner,when)
            result.append(tuple(tuple(getattr(v,k) for k in ('x','y','z')) for v in (ev.pos,ev.vel,ev.acc)))
        return tuple(result)

    def future_states(self,when):
        if self.program:
            plan,start,_=self.program
            if when>=start+plan.duration:
                return plan.after.states() if plan.after else tuple(rest(p) for p in self.home)
        return self.native_states(when)

    def command(self,data):
        kind=data.get('action')
        if kind=='return':
            self.return_requested=True
            if self.pending:self.pending[0].cancel();self.pending=None
            if not self.program:
                if self.scene is None:self.return_requested=False;self.emit('grid')
                else:self.submit('return',{})
            return
        if kind!='start':raise ValueError('Grid Snake plays and collects automatically; use start or return')
        if self.program or self.pending or self.scene:raise ValueError('Snake is already running')
        validate_limit(data.get('limit'))
        if isinstance(data.get('seed',31),bool) or not isinstance(data.get('seed',31),int):raise ValueError('Seed must be an integer')
        states=self.native_states(self.server.backend.time())
        if max(math.dist(s[0],p) for s,p in zip(states,self.home))>.2:
            raise ValueError('Take off to the airborne grid before starting Snake')
        self.paused=False;self.return_requested=False
        self.submit('start',data)

    def submit(self,kind,payload,when=None,scene=None):
        when=self.server.backend.time()+LEAD if when is None else when
        states=scene.states() if kind=='step' else self.future_states(when)
        future=self.server.blend_worker.submit(self.builder,kind,states,scene,payload)
        self.pending=(future,when,kind,payload,states)
        if kind!='step':self.emit('planning',action=kind)

    def install(self,plan,start,exit_plan):
        trajectory_id=110 if len(plan.paths[0])==3 else 111
        for name,path in zip(self.drone_names,plan.paths):
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
        self.program=(plan,start,exit_plan)
        if plan.after is not None and plan.after.foods and not self.return_requested:
            self.submit('step',{},when=start+plan.duration,scene=plan.after)

    def _boundary_matches(self,old,new):
        return max(math.dist(a[-1].evaluate(a[-1].duration,d),b[0].evaluate(0,d))
                   for a,b in zip(old.paths,new.paths) for d in range(3))<1e-6

    def update(self,now):
        # Commit the prepared program before the backend evaluates this tick.
        # Its original time origin preserves motion across exact boundaries.
        if self.program:
            old,start,exit_plan=self.program
            until=start+old.duration
            if now+1e-8>=until:
                self.scene=old.after
                if old.kind=='grid':
                    self.program=None;self.return_requested=False;self.emit('grid')
                else:
                    collected=[s.actors[0] for s,a in zip(old.after.snakes,old.actions) if a=='eat']
                    self.emit('collected' if collected else 'split' if old.kind=='split' else 'playing',collected_ids=collected)
                    if not old.after.foods and not self.return_requested:
                        self.return_requested=True
                        if self.pending:self.pending[0].cancel();self.pending=None
                        self.emit('returning',reason='All apples collected; returning to the airborne grid')
                    next_result=None
                    if not self.return_requested and self.pending and self.pending[0].done():
                        try:next_result=self.pending[0].result()
                        except Exception as error:self.emit('rejected',action='step',reason=str(error))
                    if self.return_requested:
                        self.program=None;self.install(exit_plan,until,None)
                    elif next_result and self._boundary_matches(old,next_result[0]):
                        self.pending=None
                        self.install(next_result[0],until,next_result[1])
                    else:
                        # A pre-certified exit is always ready. A slow/rejected
                        # planner cannot leave moving drones frozen at an endpoint.
                        if self.pending:self.pending[0].cancel()
                        self.pending=None;self.return_requested=True;self.deadline_fallbacks+=1
                        self.emit('returning',reason='Next path not ready; returning through the certified exit')
                        self.install(exit_plan,until,None)
        if self.pending:
            future,start,kind,payload,expected=self.pending
            if kind!='step' and future.done():
                try:plan,exit_plan=future.result()
                except Exception as error:
                    self.pending=None;self.paused=True
                    self.emit('rejected',action=kind,reason=str(error))
                else:
                    if now+1e-8>=start:
                        actual=self.native_states(now)
                        error=max(math.dist(a[d],b[d]) for a,b in zip(expected,actual) for d in range(3))
                        self.pending=None
                        if error>1e-4:
                            self.paused=True;self.emit('rejected',action=kind,reason=f'Source state changed ({error:.6g})')
                        else:
                            self.install(plan,now,exit_plan)
                            self.emit('started',action=kind,bound=plan.bound)
        if now-self.last_publish>=.05:
            self.last_publish=now;self.emit('state')

    def clear(self):
        if self.pending:self.pending[0].cancel()
        self.pending=self.program=self.scene=None
        self.return_requested=False;self.paused=False
