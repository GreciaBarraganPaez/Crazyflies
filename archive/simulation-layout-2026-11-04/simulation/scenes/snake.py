"""Continuous Snake with multiple apples, identity-preserving head growth and borders."""
from dataclasses import dataclass,replace
import math
import random
from functools import lru_cache
from .snake_routes import winding_cycle
from static_shapes import COUNT,HOME
from .trajectories import rest,segment,compile_states,fleet_join,certificate

WIDTH,HEIGHT=12,8
CELL=1.5
BASE_Z=1.9
TICK=2.0
BORDER_IDS=tuple(range(COUNT-4,COUNT))
MAX_MEMBERS=COUNT-4
CYCLE=((0,0),)+tuple((x,0) for x in range(1,WIDTH))+tuple(
    (x,y) for y in range(1,HEIGHT)
    for x in (range(WIDTH-1,0,-1) if y%2 else range(1,WIDTH)))+tuple((0,y) for y in range(HEIGHT-1,0,-1))
INDEX={c:i for i,c in enumerate(CYCLE)}
START_PHASE=14


def world(cell):return ((cell[0]-(WIDTH-1)/2)*CELL,0.,BASE_Z+cell[1]*CELL)

def border_points():
    x=WIDTH*CELL/2;bottom=BASE_Z-CELL/2;top=BASE_Z+(HEIGHT-.5)*CELL
    return ((-x,0.,bottom),(x,0.,bottom),(x,0.,top),(-x,0.,top))

def parking(i):return (WIDTH*CELL/2+2.+(i%3)*1.1,0.,2.+(i//3)*1.1)

def adjacent(a,b):return abs(a[0]-b[0])+abs(a[1]-b[1])==1

def delta(a,b):return (a[0]-b[0],a[1]-b[1])

def validate_limit(value):
    if isinstance(value,bool) or not isinstance(value,int) or not 3<=value<=MAX_MEMBERS:
        raise ValueError('Snake count must be an integer from 3 to 15; four drones mark the border')
    return value


def _tangent(index,course):
    a,b=world(course[(index-1)%len(course)]),world(course[(index+1)%len(course)])
    return tuple((y-x)/2 for x,y in zip(a,b))

@lru_cache(maxsize=64)
def route_pieces(course):
    return tuple(segment((world(c),_tangent(i,course),(0.,)*3),
        (world(course[(i+1)%len(course)]),_tangent(i+1,course),(0.,)*3),1.)
        for i,c in enumerate(course))


def route(phase,rate=1/TICK,acceleration=0.,course=CYCLE):
    p=phase%len(course);index=int(math.floor(p));u=p-index;piece=route_pieces(course)[index]
    position=piece.evaluate(u);v=piece.evaluate(u,1);a=piece.evaluate(u,2)
    return position,tuple(x*rate for x in v),tuple(x*rate*rate+y*acceleration for x,y in zip(a,v))


@dataclass(frozen=True)
class Snake:
    actors:tuple
    head:float
    foods:tuple
    course:tuple
    launched:int|None=None
    launch_phase:float|None=None

    def states(self):
        result={i:route(self.head-k,course=self.course) for k,i in enumerate(self.actors)}
        for i,p in self.foods:
            result[i]=route(self.launch_phase,course=self.course) if i==self.launched else rest(world(self.course[int(p)%len(self.course)]))
        return result

    def step(self,t):
        u=t/TICK
        result={i:route(self.head+u-k,course=self.course) for k,i in enumerate(self.actors)}
        for i,p in self.foods:result[i]=rest(world(self.course[int(p)%len(self.course)]))
        if self.launched is not None:
            result[self.launched]=route(self.launch_phase+u,course=self.course)
        elif self.foods and self.foods[0][1]-self.head<=1.000001:
            i,f=self.foods[0];r=6*u**3-8*u**4+3*u**5
            dr=18*u**2-32*u**3+15*u**4;ddr=36*u-96*u**2+60*u**3
            result[i]=route(f+r,dr/TICK,ddr/TICK**2,course=self.course)
        return result

    def advance(self):
        if self.launched is not None:
            return replace(self,actors=(self.launched,)+self.actors,head=self.launch_phase+1,
                foods=tuple(f for f in self.foods if f[0]!=self.launched),launched=None,launch_phase=None),'eat'
        if self.foods and self.foods[0][1]-self.head<=1.000001:
            i,f=self.foods[0]
            return replace(self,head=self.head+1,launched=i,launch_phase=f+1),'launch'
        return replace(self,head=self.head+1),'move'


def apples(actors,head,seed):
    rng=random.Random(seed)
    return tuple((i,int(head)+5+7*k+rng.randrange(2)) for k,i in enumerate(actors))


@dataclass(frozen=True)
class SnakeScene:
    limit:int=MAX_MEMBERS
    seed:int=31
    moves:int=0
    snakes:tuple=()

    def __post_init__(self):
        validate_limit(self.limit)
        ids=self.actors+tuple(i for snake in self.snakes for i,_ in snake.foods)
        if len(set(ids))!=len(ids) or any(not 0<=i<self.limit for i in ids):
            raise ValueError('Actor identities must be unique and outside border roles')
        if any(len(s.actors)<3 for s in self.snakes):raise ValueError('Each snake needs at least three drones')

    @property
    def actors(self):return tuple(i for s in self.snakes for i in s.actors) if self.snakes else (0,1,2)
    @property
    def members(self):return len(self.actors)
    @property
    def score(self):return self.members-3
    @property
    def heads(self):return tuple(s.actors[0] for s in self.snakes)
    @property
    def head(self):return self.snakes[0].head if self.snakes else START_PHASE
    @property
    def foods(self):return tuple(f for s in self.snakes for f in s.foods)
    @property
    def food_cells(self):return tuple(s.course[int(p)%len(s.course)] for s in self.snakes for _,p in s.foods)
    @property
    def body(self):return tuple(s.course[int(round(s.head-k))%len(s.course)] for s in self.snakes for k in range(len(s.actors)))

    def spawn_food(self,exclude=()):
        if self.snakes:return self
        snake=Snake((0,1,2),START_PHASE,apples(range(3,self.limit),START_PHASE,self.seed),
                    winding_cycle(WIDTH,HEIGHT,self.seed))
        return replace(self,snakes=(snake,))

    def states(self,when=0.):
        states=[rest(parking(i)) for i in range(COUNT)]
        for snake in self.spawn_food().snakes:
            for i,state in snake.states().items():states[i]=state
        for i,p in zip(BORDER_IDS,border_points()):states[i]=rest(p)
        return tuple(states)

    def roles(self):
        roles=['parked']*COUNT
        for i in BORDER_IDS:roles[i]='border'
        for group,snake in enumerate(self.spawn_food().snakes):
            for k,i in enumerate(snake.actors):roles[i]=('head' if k==0 else 'body')+('2' if group else '')
            for i,_ in snake.foods:roles[i]='food'
        return tuple(roles)


@dataclass(frozen=True)
class ScenePlan:
    paths:tuple
    after:SnakeScene|None
    kind:str
    bound:float
    cells:int=0
    actions:tuple=()

    @property
    def duration(self):return sum(p.duration for p in self.paths[0])


def arrange_plan(start,scene):
    target=scene.spawn_food();paths,bound=fleet_join(start,target.states())
    return ScenePlan(paths,target,'arrange',bound)


def return_plan(start):
    paths,bound=fleet_join(start,tuple(rest(p) for p in HOME))
    return ScenePlan(paths,None,'grid',bound)


def split_plan(scene):
    original=scene.snakes[0];cut=(len(original.actors)+1)//2
    remaining=[i for i,_ in original.foods];groups=[]
    for group,actors in enumerate((original.actors[:cut],original.actors[cut:])):
        # A wide central corridor separates the two independent game regions.
        course=winding_cycle(4,HEIGHT,scene.seed+101+group,offset=8*group)
        head=8;food_ids=remaining[group::2]
        groups.append(Snake(actors,head,apples(food_ids,head,scene.seed+group),course))
    after=replace(scene,snakes=tuple(groups))
    paths,bound=fleet_join(scene.states(),after.states(),fixed=BORDER_IDS)
    return ScenePlan(paths,after,'split',bound)


def step_plan(scene):
    scene=scene.spawn_food()
    if len(scene.snakes)==1 and scene.members>=9 and scene.limit>=9:
        return split_plan(scene)
    advances=tuple(s.advance() for s in scene.snakes)
    after=replace(scene,snakes=tuple(s for s,_ in advances),moves=scene.moves+1)
    actions=tuple(action for _,action in advances)
    kind='eat' if 'eat' in actions else 'launch' if 'launch' in actions else 'move'
    def states(t):
        result=list(scene.states())
        for snake in scene.snakes:
            for i,state in snake.step(t).items():result[i]=state
        return result
    paths=compile_states(states,TICK);bound=certificate(paths)
    if bound is None:raise ValueError('Continuous scene path failed clearance validation')
    return ScenePlan(paths,after,kind,bound,1,actions)
