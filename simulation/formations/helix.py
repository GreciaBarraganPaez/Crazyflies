"""A travelling 3D corkscrew along X, with continuous motion in Y and Z."""
import math

RADIUS=1.4
CENTER_Z=3.4
WAVELENGTH=5.4


def geometry(count=19):
    return tuple((-5.4+i*10.8/(count-1),
                  RADIUS*math.cos(2*math.pi*(-5.4+i*10.8/(count-1))/WAVELENGTH),
                  CENTER_Z+RADIUS*math.sin(2*math.pi*(-5.4+i*10.8/(count-1))/WAVELENGTH))
                 for i in range(count))


def evaluate(point,phase,velocity,acceleration):
    x,_,_=point
    angle=2*math.pi*x/WAVELENGTH-phase
    c,s=math.cos(angle),math.sin(angle)
    return ((x,RADIUS*c,CENTER_Z+RADIUS*s),
            (0.,RADIUS*s*velocity,-RADIUS*c*velocity),
            (0.,-RADIUS*c*velocity**2+RADIUS*s*acceleration,
             -RADIUS*s*velocity**2-RADIUS*c*acceleration))
