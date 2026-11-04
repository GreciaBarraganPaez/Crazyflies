"""Pose-synchronized visualization colors. Never sends flight commands."""
from dataclasses import dataclass
import math
import colorsys
from static_shapes import COUNT, HOME, targets
from continuous_trajectories import SPIRAL_CENTER_Z, SPIRAL_TURN_AMPLITUDE
from formations.helix import CENTER_Z as HELIX_Z,WAVELENGTH as HELIX_WAVELENGTH

_HEART = targets('heart')
_SINE = targets('sine')
_SPIRAL = targets('spiral')
_MOON = targets('moon')
_HELIX = targets('helix')
_SIN = tuple(math.sin(2*math.pi*x/5.4) for x,_,_ in _SINE)
_COS = tuple(math.cos(2*math.pi*x/5.4) for x,_,_ in _SINE)
_SS = sum(s*s for s in _SIN)
_CC = sum(c*c for c in _COS)
_SC = sum(s*c for s,c in zip(_SIN,_COS))
_DET = _SS*_CC-_SC*_SC


def _clamp(value):
    return max(0.,min(1.,value))


def _mix(a,b,u):
    return tuple(x+(y-x)*u for x,y in zip(a,b))


@dataclass(frozen=True)
class ColorFrame:
    shape: str = 'neutral'
    scale: float = 1.0
    phase: float = 0.0
    error: float = float('inf')


def infer_frame(points, previous='neutral'):
    """Recognize the assigned formation geometry, not a hand gesture.

    Read actual TF poses only for colors; RViz still positions frame-locked
    markers directly. Fit heart size and sine phase, including entry ramps,
    so there is no independent animation timer that can drift out of sync.
    """
    if points is None or len(points)!=COUNT:
        return ColorFrame()
    if any(len(p)!=3 or not all(math.isfinite(v) for v in p) for p in points):
        return ColorFrame()
    frames=[]
    denominator=sum(x*x+(z-2.7)**2 for x,_,z in _HEART)
    scale=sum(x*a+(z-2.7)*(c-2.7) for (x,_,z),(a,_,c) in zip(points,_HEART))/denominator
    if .72<=scale<=1.28:
        model=tuple((x*scale,y,2.7+(z-2.7)*scale) for x,y,z in _HEART)
        error=max(math.dist(a,b) for a,b in zip(points,model))
        frames.append(ColorFrame('heart',scale=scale,error=error))
    sy=sum(s*(z-2.9) for s,(_,_,z) in zip(_SIN,points))
    cy=sum(c*(z-2.9) for c,(_,_,z) in zip(_COS,points))
    a=(sy*_CC-cy*_SC)/_DET
    b=(cy*_SS-sy*_SC)/_DET
    if 1.2<=math.hypot(a,b)<=1.6:
        model=tuple((x,y,2.9+a*s+b*c) for (x,y,_),s,c in zip(_SINE,_SIN,_COS))
        error=max(math.dist(p,q) for p,q in zip(points,model))
        frames.append(ColorFrame('sine',phase=math.atan2(-b,a),error=error))
    denominator=sum(x*x+(z-SPIRAL_CENTER_Z)**2 for x,_,z in _SPIRAL)
    a=sum(x*u+(z-SPIRAL_CENTER_Z)*(v-SPIRAL_CENTER_Z)
          for (x,_,z),(u,_,v) in zip(points,_SPIRAL))/denominator
    b=sum((z-SPIRAL_CENTER_Z)*u-x*(v-SPIRAL_CENTER_Z)
          for (x,_,z),(u,_,v) in zip(points,_SPIRAL))/denominator
    scale,angle=math.hypot(a,b),math.atan2(b,a)
    if .96<=scale<=1.04 and -.08<=angle<=1.08:
        model=tuple((a*x-b*(z-SPIRAL_CENTER_Z),y,SPIRAL_CENTER_Z+b*x+a*(z-SPIRAL_CENTER_Z))
                    for x,y,z in _SPIRAL)
        error=max(math.dist(p,q) for p,q in zip(points,model))
        phase=math.acos(max(-1.,min(1.,1-angle/SPIRAL_TURN_AMPLITUDE)))
        frames.append(ColorFrame('spiral',scale=scale,phase=phase,error=error))
    denominator=sum(x*x for x,_,_ in _MOON if x<-1e-8)
    fraction=sum(p[0]*q[0] for p,q in zip(points,_MOON) if q[0]<-1e-8)/denominator
    if -.04<=fraction<=1.04:
        model=tuple((x*fraction if x<-1e-8 else x,y,z) for x,y,z in _MOON)
        frames.append(ColorFrame('moon',scale=fraction,
                                 error=max(math.dist(p,q) for p,q in zip(points,model))))
    denominator=sum(y*y+(z-HELIX_Z)**2 for x,y,z in _HELIX)
    a=sum(y*v+(z-HELIX_Z)*(w-HELIX_Z) for (x,y,z),(u,v,w) in zip(_HELIX,points))/denominator
    b=sum((z-HELIX_Z)*v-y*(w-HELIX_Z) for (x,y,z),(u,v,w) in zip(_HELIX,points))/denominator
    model=tuple((x,a*y+b*(z-HELIX_Z),HELIX_Z+a*(z-HELIX_Z)-b*y) for x,y,z in _HELIX)
    if .96<=math.hypot(a,b)<=1.04:
        frames.append(ColorFrame('helix',phase=math.atan2(b,a),error=max(math.dist(p,q) for p,q in zip(points,model))))
    frames.append(ColorFrame('grid',error=max(math.dist(a,b) for a,b in zip(points,HOME))))
    # Hysteresis keeps small fitting variations from flashing between palettes.
    old=next((f for f in frames if f.shape==previous and f.error<=.18),None)
    if old is not None:return old
    best=min(frames,key=lambda f:f.error)
    return best if best.error<=.10 else ColorFrame()


def frame_colors(frame):
    if frame.shape=='helix':
        return tuple(colorsys.hsv_to_rgb((x/HELIX_WAVELENGTH-frame.phase/(2*math.pi))%1.,.82,
                     .82+.18*(1+math.cos(2*math.pi*x/HELIX_WAVELENGTH-frame.phase))/2) for x,y,z in _HELIX)
    if frame.shape=='heart':
        intensity=_clamp((frame.scale-.8)/.4)
        intensity=intensity*intensity*(3-2*intensity)
        color=_mix((.28,.008,.035),(1.,.33,.22),intensity)
        return (color,)*COUNT
    if frame.shape=='sine':
        result=[]
        for x,_,_ in _SINE:
            angle=2*math.pi*x/5.4-frame.phase
            crest=(math.sin(angle)+1)/2
            hue=(angle/(2*math.pi))%1.
            result.append(colorsys.hsv_to_rgb(hue,.88,.70+.30*crest**2))
        return tuple(result)
    if frame.shape=='spiral':
        brightness=.95
        result=[]
        for x,_,z in _SPIRAL:
            along=(math.hypot(x,z-SPIRAL_CENTER_Z)-1.4)/2.2
            blend=.5-.5*math.cos(2*math.pi*along-frame.phase)
            color=_mix((1.,.60,.07),(.55,.10,1.),blend)
            result.append(tuple(v*brightness for v in color))
        return tuple(result)
    if frame.shape=='moon':
        color=_mix((.58,.72,1.),(1.,.92,.69),_clamp(frame.scale))
        return (color,)*COUNT
    color={'grid':(.08,.65,.8),'neutral':(.20,.32,.50)}[frame.shape]
    return (color,)*COUNT


class ColorAnimator:
    def __init__(self,fade_sec=.6):
        self.fade_sec=fade_sec
        self.frame=ColorFrame()
        self.colors=frame_colors(self.frame)
        self.fade_from=self.colors
        self.fade_start=-float('inf')
        self.last_time=None

    def update(self,points,now):
        if self.last_time is not None and now<self.last_time:
            self.fade_from=self.colors
            self.fade_start=now
        self.last_time=now
        frame=infer_frame(points,self.frame.shape)
        if frame.shape!=self.frame.shape:
            self.fade_from=self.colors
            self.fade_start=now
        self.frame=frame
        wanted=frame_colors(frame)
        amount=_clamp((now-self.fade_start)/self.fade_sec) if self.fade_sec>0 else 1.
        amount=amount*amount*(3-2*amount)
        self.colors=wanted if amount>=1. else tuple(_mix(a,b,amount) for a,b in zip(self.fade_from,wanted))
        return self.colors
