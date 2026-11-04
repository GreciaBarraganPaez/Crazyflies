"""Pure Snake scene: time-delayed path following and noncontact collection."""
from dataclasses import dataclass, replace
import math
from static_shapes import COUNT, HOME
from .trajectories import rest, evaluate, compile_functions, detour, fleet_join, certificate

RADIUS=3.
CENTER_Z=4.
PERIOD=24.
TRAIL_ANGLE=.30
PICKUP=(4.1,0.,4.)
COLLECTION_RADIUS=1.16
INITIAL_MEMBERS=3


def parking(index):
    return (6.2+.85*(index%4),0.,1.2+.85*(index//4))


def validate_limit(value):
    if isinstance(value,bool) or not isinstance(value,int) or not 3<=value<=COUNT:
        raise ValueError('Snake count must be an integer from 3 to 19')
    return value


@dataclass(frozen=True)
class SnakeScene:
    members:int=3
    limit:int=5
    direction:int=-1
    origin:float=0.
    pickup:int|None=None

    def __post_init__(self):
        validate_limit(self.limit)
        if not 3<=self.members<=self.limit or self.direction not in (-1,1):
            raise ValueError('Invalid Snake scene')
        if self.pickup is not None and (self.pickup!=self.members or self.members>=self.limit):
            raise ValueError('Only the next waiting drone may be collected')

    def state(self,index,when):
        if index<self.members:
            w=self.direction*2*math.pi/PERIOD
            angle=w*(when-self.origin)-self.direction*index*TRAIL_ANGLE
            c,s=math.cos(angle),math.sin(angle)
            return ((RADIUS*c,0.,CENTER_Z+RADIUS*s),
                    (-RADIUS*s*w,0.,RADIUS*c*w),(-RADIUS*c*w*w,0.,-RADIUS*s*w*w))
        return rest(PICKUP if index==self.pickup else parking(index))

    def states(self,when):return tuple(self.state(i,when) for i in range(COUNT))

    def roles(self):
        return tuple('head' if i==0 else 'body' if i<self.members else
                     'pickup' if i==self.pickup else 'waiting' if i<self.limit else 'parked'
                     for i in range(COUNT))

    def can_collect(self,when):
        return self.pickup is not None and math.dist(self.state(0,when)[0],PICKUP)<=COLLECTION_RADIUS


@dataclass(frozen=True)
class ScenePlan:
    paths:tuple
    after:SnakeScene|None
    kind:str
    bound:float

    @property
    def duration(self):return sum(p.duration for p in self.paths[0])


def loop_plan(scene,start):
    functions=tuple(lambda t,i=i:scene.state(i,start+t) for i in range(COUNT))
    paths=compile_functions(functions,PERIOD)
    bound=certificate(paths)
    if bound is None:raise ValueError('Snake loop failed clearance validation')
    return ScenePlan(paths,scene,'loop',bound)


def arrange_plan(start,when,scene):
    # Destination phase zero starts at the exact end of the entry/turn route.
    for seconds in (8.,11.2):
        after=replace(scene,origin=when+seconds,pickup=None)
        end=after.states(when+seconds)
        try:paths,bound=fleet_join(start,end,seconds)
        except ValueError:continue
        actual=sum(p.duration for p in paths[0])
        after=replace(after,origin=when+actual)
        return ScenePlan(paths,after,'arrange',bound)
    raise ValueError('No certified entry/direction route')


def return_plan(start):
    paths,bound=fleet_join(start,tuple(rest(p) for p in HOME))
    return ScenePlan(paths,None,'grid',bound)


def collect_plan(start,when,scene,joining=False):
    if scene.members>=scene.limit:raise ValueError('All available drones have joined the chain')
    actor=scene.members
    if joining:
        if not scene.can_collect(when):raise ValueError('Head has not reached the pickup zone')
        after=replace(scene,members=scene.members+1,pickup=None)
    else:after=replace(scene,pickup=actor)
    for seconds in (5.,7.,9.):
        end=after.state(actor,when+seconds)
        for depth in (-2.,-3.5,2.,4.):
            path=detour(start[actor],end,depth,seconds)
            functions=tuple((lambda t,path=path:evaluate(path,t)) if i==actor else
                            (lambda t,i=i:scene.state(i,when+t)) for i in range(COUNT))
            paths=compile_functions(functions,seconds,start=start)
            bound=certificate(paths)
            if bound is not None:
                return ScenePlan(paths,after,'join' if joining else 'stage',bound)
    raise ValueError('No certified pickup route; current motion retained')
