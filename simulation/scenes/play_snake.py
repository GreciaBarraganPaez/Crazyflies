"""One hand-steered snake: eight actual drones, no splitting or automatic steering."""
from dataclasses import dataclass,replace
from functools import lru_cache
import math
from .snake import ScenePlan
from .trajectories import rest,segment,compile_states,certificate,fleet_join

DRONES=tuple(f'cf{i}' for i in range(231,239))
HOME=tuple(((col-1.5)*1.1,(row-.5)*1.3,2.7) for row in range(2) for col in range(4))
WIDTH,HEIGHT,CELL,BASE_Z=10,8,1.5,1.9
TICK=2.4
DIRECTIONS={'left':(-1,0),'right':(1,0),'up':(0,1),'down':(0,-1)}


def world(cell):return ((cell[0]-(WIDTH-1)/2)*CELL,0.,BASE_Z+cell[1]*CELL)
def add(a,b):return (a[0]+b[0],a[1]+b[1])
def subtract(a,b):return (a[0]-b[0],a[1]-b[1])


def knot(trail,i):
    a,b=world(trail[i-1]),world(trail[i+1])
    return world(trail[i]),tuple((y-x)/2 for x,y in zip(a,b)),(0.,)*3


@lru_cache(maxsize=256)
def curve(trail,i):return segment(knot(trail,i),knot(trail,i+1),1.)


def follow(trail,phase,rate=1/TICK,acceleration=0.):
    if abs(phase-round(phase))<1e-9:
        p,v,a=knot(trail,int(round(phase)))
    else:
        i=int(math.floor(phase));piece=curve(trail,i);u=phase-i
        p,v,a=(piece.evaluate(u,d) for d in range(3))
    return p,tuple(x*rate for x in v),tuple(x*rate*rate+y*acceleration for x,y in zip(a,v))


@dataclass(frozen=True)
class PlayerScene:
    actors:tuple=(0,1,2)
    trail:tuple=((0,3),(1,3),(2,3),(3,3),(4,3))
    head:int=3
    foods:tuple=((3,(6,3)),(4,(7,6)),(5,(2,6)),(6,(7,1)),(7,(1,1)))
    moves:int=0
    limit:int=8

    @property
    def snakes(self):return (self,)
    @property
    def heads(self):return (self.actors[0],)
    @property
    def members(self):return len(self.actors)
    @property
    def score(self):return self.members-3
    @property
    def body(self):return tuple(self.trail[self.head-k] for k in range(self.members))
    @property
    def food_cells(self):return tuple(cell for _,cell in self.foods)
    @property
    def heading(self):return subtract(self.trail[-1],self.trail[-2])

    def states(self):
        result=[None]*8
        for k,i in enumerate(self.actors):result[i]=follow(self.trail,self.head-k)
        for i,cell in self.foods:result[i]=rest(world(cell))
        return tuple(result)

    def roles(self):
        roles=['food']*8
        for k,i in enumerate(self.actors):roles[i]='head' if k==0 else 'body'
        return tuple(roles)


def exit_plan(start):
    paths,bound=fleet_join(start,tuple(rest(p) for p in HOME))
    return ScenePlan(paths,None,'grid',bound)


def enter_plan(start):
    scene=PlayerScene();paths,bound=fleet_join(start,scene.states())
    return ScenePlan(paths,scene,'arrange',bound)


def extend(trail,heading,requested,blocked):
    desired=DIRECTIONS.get(requested,heading)
    def allowed(d):
        cell=add(trail[-1],d)
        return d!=(-heading[0],-heading[1]) and 0<=cell[0]<WIDTH and 0<=cell[1]<HEIGHT and cell not in blocked
    # Invalid turns are ignored. If continuing is blocked too, exit to the grid.
    direction=desired if allowed(desired) else heading
    if not allowed(direction):return None
    return trail+(add(trail[-1],direction),)


def step_plan(scene,direction=None):
    food=next((i for i,c in scene.foods if c==scene.trail[-1]),None)
    blocked=set(scene.body)|{scene.trail[-2]}
    trail=extend(scene.trail,scene.heading,direction,blocked)
    if trail is None:return exit_plan(scene.states())
    if food is not None:
        # Launch space must be free of every other apple and the body.
        if trail[-1] in scene.food_cells:return exit_plan(scene.states())
        blocked|=set(scene.food_cells)|{trail[-2]}
        next_trail=extend(trail,subtract(trail[-1],trail[-2]),None,blocked)
        if next_trail is None:return exit_plan(scene.states())
        trail=next_trail
    actors=((food,)+scene.actors) if food is not None else scene.actors
    head=scene.head+(2 if food is not None else 1)
    trim=max(0,head-len(actors))
    after=replace(scene,actors=actors,head=head-trim,trail=trail[trim:],moves=scene.moves+1,
                  foods=tuple(f for f in scene.foods if f[0]!=food))
    def states(t):
        u=t/TICK;result=list(scene.states())
        for k,i in enumerate(scene.actors):result[i]=follow(trail,scene.head+u-k)
        if food is not None:
            r=6*u**3-8*u**4+3*u**5;dr=18*u**2-32*u**3+15*u**4;ddr=36*u-96*u**2+60*u**3
            result[food]=follow(trail,scene.head+1+r,dr/TICK,ddr/TICK**2)
        return result
    paths=compile_states(states,TICK);bound=certificate(paths)
    if bound is None:return exit_plan(scene.states())
    return ScenePlan(paths,after,'launch' if food is not None else 'move',bound,1,
                     ('eat' if food is not None else 'move',))
