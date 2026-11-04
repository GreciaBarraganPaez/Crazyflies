"""Full-to-half moon outline. The right limb stays fixed; the terminator moves."""
import math

CENTER_Z=3.6
RADIUS=2.7


def geometry():
    right=tuple((RADIUS*math.cos(-math.pi/2+i*math.pi/10),0.,
                 CENTER_Z+RADIUS*math.sin(-math.pi/2+i*math.pi/10)) for i in range(11))
    left=tuple((-math.sqrt(RADIUS**2-z*z),0.,CENTER_Z+z)
               for z in (RADIUS*(1-2*i/9) for i in range(1,9)))
    return right+left


def evaluate(point,phase,velocity,acceleration):
    x,y,z=point
    if x>=-1e-8:return point,(0.,0.,0.),(0.,0.,0.)
    fraction=.5+.5*math.cos(phase)
    rate=-.5*math.sin(phase)*velocity
    change=-.5*(math.cos(phase)*velocity**2+math.sin(phase)*acceleration)
    return (x*fraction,y,z),(x*rate,0.,0.),(x*change,0.,0.)
