"""Preview-only C2 shape changes, certified over whole polynomial segments.

Start with the outgoing position/velocity/acceleration; fan out in depth while
turning into the morph, then join the next animation's moving loop. No separate
stop, return-to-stop-point, or waypoint hover. Bernstein hull subdivision gives
a conservative center-separation bound for the continuous polynomial paths.
"""
from dataclasses import dataclass
import math
import numpy as np
from continuous_trajectories import Piece, hermite, motion, PERIODS
from static_shapes import COUNT, targets, MIN_PLANNED_SEPARATION, minimum_distance
from formation_registry import BLEND_REQUESTS, validate_speed

BLEND_TRAJECTORY_ID = 90
_LEFT, _RIGHT = np.triu_indices(COUNT, 1)
_POWER_TO_BEZIER = np.array([[math.comb(k,i)/math.comb(5,i) if i<=k else 0.
                              for i in range(6)] for k in range(6)])


def bezier_controls(pieces):
    if any(any(abs(c)>1e-12 for c in axis[6:]) for p in pieces for axis in p.axes):
        raise ValueError('The blend clearance certificate requires degree-five pieces')
    power = np.array([p.axes for p in pieces]).transpose(0,2,1)[:,:6,:]
    duration = pieces[0].duration
    power *= np.array([duration**i for i in range(6)])[None,:,None]
    return np.einsum('ki,nij->nkj',_POWER_TO_BEZIER,power)


def certify_relative(curves, clearance, max_depth=14):
    """Return a per-pair certificate. Unresolved curves fail closed."""
    result = np.ones(len(curves), dtype=bool)
    lower = float('inf')
    stack = [(curves, np.arange(len(curves)), 0)]
    while stack:
        controls, indexes, depth = stack.pop()
        lo,hi = controls.min(axis=1),controls.max(axis=1)
        nearest = np.where(lo>0,lo,np.where(hi<0,-hi,0.))
        bound = np.linalg.norm(nearest,axis=1)
        safe = bound >= clearance + 1e-10
        if safe.any(): lower = min(lower,float(bound[safe].min()))
        controls,indexes = controls[~safe],indexes[~safe]
        if not len(indexes): continue
        unsafe = ((np.linalg.norm(controls[:,0],axis=1)<clearance+1e-10) |
                  (np.linalg.norm(controls[:,-1],axis=1)<clearance+1e-10))
        result[indexes[unsafe]] = False
        controls,indexes = controls[~unsafe],indexes[~unsafe]
        if not len(indexes): continue
        if depth>=max_depth:
            result[indexes]=False
            continue
        left,right=np.empty_like(controls),np.empty_like(controls)
        left[:,0],right[:,-1]=controls[:,0],controls[:,-1]
        work=controls
        for k in range(1,6):
            work=(work[:,:-1]+work[:,1:])*.5
            left[:,k],right[:,-k-1]=work[:,0],work[:,-1]
        stack.append((right,indexes,depth+1))
        stack.append((left,indexes,depth+1))
    return result,lower


@dataclass(frozen=True)
class BlendPlan:
    target: str
    paths: tuple
    duration: float
    clearance_bound: float
    lane_count: int


def _paths(start, end, durations, lanes):
    p0,v0,a0 = (np.array([s[k] for s in start],dtype=float) for k in range(3))
    p3,v3,a3 = (np.array([s[k] for s in end],dtype=float) for k in range(3))
    first,middle,last=durations
    p1=p0+v0*first*.3
    p2=p3-.12*(p3-p1)-v3*last*.1
    p1[:,1]=lanes;p2[:,1]=lanes
    v1=.65*(p2-p0)/(first+middle)
    v2=.65*(p3-p1)/(middle+last)
    v1[:,1]=0.;v2[:,1]=0.
    zero=np.zeros_like(p0)
    knots=((p0,v0,a0),(p1,v1,zero),(p2,v2,zero),(p3,v3,a3))
    paths=[[] for _ in range(COUNT)]
    for k,duration in enumerate(durations):
        a,b=knots[k],knots[k+1]
        for i in range(COUNT):
            axes=tuple(hermite(a[0][i,j],a[1][i,j],a[2][i,j],
                               b[0][i,j],b[1][i,j],b[2][i,j],duration) for j in range(3))
            paths[i].append(Piece(duration,axes))
    return tuple(tuple(path) for path in paths)


def certify_paths(paths):
    bound=float('inf')
    for k in range(3):
        controls=bezier_controls([p[k] for p in paths])
        pending=[(controls[:,:,2],0)]
        while pending:
            z,depth=pending.pop()
            z=z[z.min(axis=1)<=.6+1e-10]
            if not len(z): continue
            if (z[:,(0,-1)]<=.6+1e-10).any() or depth>=14: return None
            left,right=np.empty_like(z),np.empty_like(z)
            left[:,0],right[:,-1]=z[:,0],z[:,-1]
            work=z
            for j in range(1,6):
                work=(work[:,:-1]+work[:,1:])*.5
                left[:,j],right[:,-j-1]=work[:,0],work[:,-1]
            pending.extend(((left,depth+1),(right,depth+1)))
        safe,lower=certify_relative(controls[_LEFT]-controls[_RIGHT],MIN_PLANNED_SEPARATION)
        if not safe.all(): return None
        bound=min(bound,lower)
    return bound


def compile_blend(start, target, speed=1.0):
    if target not in PERIODS or len(start)!=COUNT:
        raise ValueError('Unsupported complete-fleet blend')
    values=np.array(start,dtype=float)
    if values.shape!=(COUNT,3,3) or not np.isfinite(values).all():
        raise ValueError('Invalid source position/velocity/acceleration')
    if np.abs(values[:,0,1]).max()>1e-6 or np.abs(values[:,1:,1]).max()>1e-6:
        raise ValueError('Blend must begin in the front formation plane')
    if minimum_distance(values[:,0])<MIN_PLANNED_SEPARATION:
        raise ValueError('Source spacing is too small')
    speed=validate_speed(speed)
    end=motion(target,0.,speed=speed) if target in PERIODS else tuple((p,(0.,)*3,(0.,)*3) for p in targets(target))
    distance=max(math.dist(a[0],b[0]) for a,b in zip(start,end))
    for first in (.55,.35,.8,.2,.15):
        durations=(first,max(1.2,distance/1.8),.65)
        projected=_paths(start,end,durations,np.zeros(COUNT))
        conflicts=np.zeros(len(_LEFT),dtype=bool)
        for k in range(3):
            controls=bezier_controls([p[k] for p in projected])
            safe,_=certify_relative(controls[_LEFT]-controls[_RIGHT],.75)
            conflicts|=~safe
        neighbors=[set() for _ in range(COUNT)]
        for i,j in zip(_LEFT[conflicts],_RIGHT[conflicts]):
            neighbors[i].add(j);neighbors[j].add(i)
        colors={}
        for i in sorted(range(COUNT),key=lambda i:(-len(neighbors[i]),i)):
            used={colors[j] for j in neighbors[i] if j in colors}
            colors[i]=next(c for c in range(COUNT) if c not in used)
        count=max(colors.values())+1
        for spacing in (.85,1.2,1.6,2.2):
            lanes=np.array([(colors[i]-(count-1)/2)*spacing for i in range(COUNT)])
            paths=_paths(start,end,durations,lanes)
            bound=certify_paths(paths)
            if bound is not None:
                return BlendPlan(target,paths,sum(durations),bound,count)
    raise ValueError('No continuously separated blend found; outgoing formation kept running')
