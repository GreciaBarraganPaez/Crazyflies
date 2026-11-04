"""Time-aligned scene trajectories with conservative full-curve validation."""
import numpy as np
from continuous_trajectories import Piece, hermite
from blended_transitions import bezier_controls, certify_relative

PIECES=96
CLEARANCE=.52
FLOOR=.6
ZERO=(0.,0.,0.)


def rest(point):return tuple(point),ZERO,ZERO


def segment(a,b,duration):
    return Piece(duration,tuple(hermite(a[0][k],a[1][k],a[2][k],
                                        b[0][k],b[1][k],b[2][k],duration) for k in range(3)))


def evaluate(path,t):
    t=max(0.,t)
    for p in path:
        if t<=p.duration+1e-9:return tuple(p.evaluate(min(t,p.duration),d) for d in range(3))
        t-=p.duration
    return tuple(path[-1].evaluate(path[-1].duration,d) for d in range(3))


def compile_functions(functions,duration,start=None):
    step=duration/PIECES
    paths=[]
    for i,fn in enumerate(functions):
        knots=[fn(k*step) for k in range(PIECES+1)]
        if start is not None:knots[0]=start[i]
        paths.append(tuple(segment(a,b,step) for a,b in zip(knots,knots[1:])))
    return tuple(paths)


def certificate(paths):
    if len(paths)<2 or any(len(p)!=len(paths[0]) for p in paths):
        raise ValueError('Scene paths must have aligned pieces')
    left,right=np.triu_indices(len(paths),1)
    lower=float('inf')
    for k in range(len(paths[0])):
        pieces=[p[k] for p in paths]
        if any(abs(p.duration-pieces[0].duration)>1e-9 for p in pieces):
            raise ValueError('Scene piece durations disagree')
        controls=bezier_controls(pieces)
        if not np.isfinite(controls).all() or controls[:,:,2].min()<=FLOOR:
            return None
        safe,bound=certify_relative(controls[left]-controls[right],CLEARANCE)
        if not safe.all():return None
        lower=min(lower,bound)
    return lower


def detour(a,b,depth,duration):
    first,last=duration*.20,duration*.20
    middle=duration-first-last
    p0,v0,_=a;p3,v3,_=b
    p1=(p0[0]+v0[0]*first*.25,depth,p0[2]+v0[2]*first*.25)
    p2=(p3[0]-v3[0]*last*.15,depth,p3[2]-v3[2]*last*.15)
    v1=tuple(.5*(p2[k]-p0[k])/(first+middle) if k!=1 else 0. for k in range(3))
    v2=tuple(.5*(p3[k]-p1[k])/(middle+last) if k!=1 else 0. for k in range(3))
    knots=(a,(p1,v1,ZERO),(p2,v2,ZERO),b)
    return tuple(segment(knots[i],knots[i+1],d) for i,d in enumerate((first,middle,last)))


def fleet_join(start,end,duration=8.):
    """Sorted depth lanes preserve ordering at overlapping home-grid projections."""
    n=len(start)
    start_order=sorted(range(n),key=lambda i:(start[i][0][1],start[i][0][0],i))
    end_order=sorted(range(n),key=lambda i:(end[i][0][1],end[i][0][0],i))
    for seconds in (duration,duration*1.4):
        for order in (start_order,end_order):
            for spacing in (.7,1.,1.4):
                lanes={i:(rank-(n-1)/2)*spacing for rank,i in enumerate(order)}
                paths=tuple(detour(a,b,lanes[i],seconds) for i,(a,b) in enumerate(zip(start,end)))
                bound=certificate(paths)
                if bound is not None:return paths,bound
    raise ValueError('No certified scene route; current motion retained')
