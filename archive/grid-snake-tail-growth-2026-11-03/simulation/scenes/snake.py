"""Autonomous grid Snake: legal forward/left/right moves and physical growth."""
from dataclasses import dataclass, replace
import random
from static_shapes import COUNT, HOME
from .trajectories import rest, segment, evaluate, compile_functions, detour, fleet_join, certificate

WIDTH,HEIGHT=8,6
CELL=1.2
BASE_Z=1.1
MOVE_SECONDS=1.4
INITIAL_BODY=((5,1),(6,1),(7,1))
# Hamiltonian ordering supplies a collision-free fallback; safe shortcuts seek food.
CYCLE=((0,0),)+tuple((x,0) for x in range(1,WIDTH))+tuple(
    (x,y) for y in range(1,HEIGHT)
    for x in (range(WIDTH-1,0,-1) if y%2 else range(1,WIDTH)))+tuple((0,y) for y in range(HEIGHT-1,0,-1))
INDEX={cell:i for i,cell in enumerate(CYCLE)}
DIRECTIONS=((1,0),(0,1),(-1,0),(0,-1))


def world(cell):return ((cell[0]-(WIDTH-1)/2)*CELL,0.,BASE_Z+cell[1]*CELL)
def parking(index):return (6.6+.85*(index%4),0.,1.2+.85*(index//4))
def delta(a,b):return (a[0]-b[0],a[1]-b[1])
def adjacent(a,b):return sum(abs(v) for v in delta(a,b))==1


def validate_limit(value):
    if isinstance(value,bool) or not isinstance(value,int) or not 3<=value<=COUNT:
        raise ValueError('Snake count must be an integer from 3 to 19')
    return value


@dataclass(frozen=True)
class SnakeScene:
    body:tuple=INITIAL_BODY
    limit:int=19
    food:tuple|None=None
    seed:int=31
    moves:int=0

    def __post_init__(self):
        validate_limit(self.limit)
        if not 3<=len(self.body)<=self.limit or len(set(self.body))!=len(self.body):
            raise ValueError('Invalid Snake body')
        if any(c not in INDEX for c in self.body) or any(not adjacent(a,b) for a,b in zip(self.body,self.body[1:])):
            raise ValueError('Snake body must occupy adjacent board cells')
        if self.food is not None and (self.food not in INDEX or self.food in self.body):
            raise ValueError('Food must occupy a free board cell')

    @property
    def members(self):return len(self.body)
    @property
    def score(self):return self.members-3
    @property
    def heading(self):return delta(self.body[0],self.body[1])

    def spawn_food(self,exclude=()):
        if self.food is not None or self.members>=self.limit:return self
        h,t=INDEX[self.body[0]],INDEX[self.body[-1]]
        gap=(t-h)%len(CYCLE)
        cells=[CYCLE[(h+d)%len(CYCLE)] for d in range(1,gap)
               if CYCLE[(h+d)%len(CYCLE)] not in self.body and CYCLE[(h+d)%len(CYCLE)] not in exclude]
        if not cells:return self
        rng=random.Random(self.seed+self.moves*104729+self.members*7919)
        return replace(self,food=rng.choice(cells))

    def next_cell(self):
        head=self.body[0];h=INDEX[head];gap=(INDEX[self.body[-1]]-h)%len(CYCLE)
        food_distance=(INDEX[self.food]-h)%len(CYCLE) if self.food is not None else len(CYCLE)
        options=[]
        for dx,dy in DIRECTIONS:
            cell=(head[0]+dx,head[1]+dy)
            if cell not in INDEX or (dx,dy)==tuple(-v for v in self.heading):continue
            growing=cell==self.food
            if cell in (self.body if growing else self.body[:-1]):continue
            forward=(INDEX[cell]-h)%len(CYCLE)
            if not 0<forward<=food_distance:continue
            if forward>gap or (forward==gap and growing):continue
            options.append((forward,cell))
        if not options:raise ValueError('No legal forward/left/right move; game held safely')
        # No-food completion uses the fallback traversal; otherwise choose the
        # largest safe shortcut toward food without overtaking the tail.
        return (min(options) if self.food is None else max(options))[1]

    def advance(self):
        cell=self.next_cell();growing=cell==self.food
        body=(cell,)+self.body if growing else (cell,)+self.body[:-1]
        after=replace(self,body=body,food=None if growing else self.food,moves=self.moves+1)
        return after.spawn_food(exclude=self.body)

    def states(self,when=0.):
        return tuple(rest(world(self.body[i])) if i<self.members else
                     rest(world(self.food)) if i==self.members and self.food is not None else
                     rest(parking(i)) for i in range(COUNT))

    def roles(self):
        return tuple('head' if i==0 else 'body' if i<self.members else
                     'food' if i==self.members and self.food is not None else 'parked' for i in range(COUNT))


@dataclass(frozen=True)
class ScenePlan:
    paths:tuple
    after:SnakeScene|None
    kind:str
    bound:float
    cells:int=0

    @property
    def duration(self):return sum(p.duration for p in self.paths[0])


def arrange_plan(start,scene):
    target=scene.spawn_food()
    paths,bound=fleet_join(start,target.states())
    return ScenePlan(paths,target,'arrange',bound)


def return_plan(start):
    end=tuple(rest(p) for p in HOME)
    if max(sum((a-b)**2 for a,b in zip(s[0],p)) for s,p in zip(start,HOME))<1e-8:
        paths=compile_functions(tuple(lambda t,p=p:rest(p) for p in HOME),.2)
        return ScenePlan(paths,None,'grid',certificate(paths))
    paths,bound=fleet_join(start,end)
    return ScenePlan(paths,None,'grid',bound)


def step_plan(scene):
    after=scene.advance();cells=1
    growing=after.members>scene.members
    spawning=after.food!=scene.food and after.food is not None
    vectors=tuple(delta(after.body[i],scene.body[i]) for i in range(scene.members))
    # Merge straight runs. No body drone may cut a corner or skip a pickup.
    if not growing and not spawning:
        for _ in range(2):
            following=after.advance()
            if following.members!=scene.members or following.food!=scene.food:break
            if tuple(delta(following.body[i],after.body[i]) for i in range(scene.members))!=vectors:break
            after=following;cells+=1
    start,end=scene.states(),after.states()
    kind='eat' if growing else 'move'
    seconds=4.8 if growing or spawning else MOVE_SECONDS*cells
    for duration in (seconds,seconds*1.3):
        moving_food=scene.members if growing else None
        new_food=after.members if spawning else None
        for side in (-1,1):
            functions=[]
            for i,(a,b) in enumerate(zip(start,end)):
                if i==moving_food:
                    path=detour(a,b,side*2.8,duration)
                elif i==new_food:
                    path=detour(a,b,-side*3.4,duration)
                else:path=(segment(a,b,duration),)
                functions.append(lambda t,path=path:evaluate(path,t))
            paths=compile_functions(tuple(functions),duration)
            bound=certificate(paths)
            if bound is not None:return ScenePlan(paths,after,kind,bound,cells)
    raise ValueError('No certified grid step; current board held safely')
