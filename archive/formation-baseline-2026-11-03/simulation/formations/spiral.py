"""Spiral position, velocity and acceleration for one assigned drone."""
import math

SPIRAL_CENTER_Z = 3.8
SPIRAL_TURN_AMPLITUDE = .5


def evaluate(point, phase, velocity, acceleration):
    x,y,z=point
    # Preserve size and spacing; retain the established winding rotation.
    scale,ds,dds=1.,0.,0.
    angle=SPIRAL_TURN_AMPLITUDE*(1-math.cos(phase))
    turn=SPIRAL_TURN_AMPLITUDE*math.sin(phase)*velocity
    dturn=SPIRAL_TURN_AMPLITUDE*(math.cos(phase)*velocity**2+math.sin(phase)*acceleration)
    c,s=math.cos(angle),math.sin(angle)
    qx,qz=c*x-s*(z-SPIRAL_CENTER_Z),s*x+c*(z-SPIRAL_CENTER_Z)
    position=(scale*qx,y,SPIRAL_CENTER_Z+scale*qz)
    vel=(ds*qx-scale*turn*qz,0.,ds*qz+scale*turn*qx)
    radial=dds-scale*turn**2
    tangent=2*ds*turn+scale*dturn
    acc=(radial*qx-tangent*qz,0.,radial*qz+tangent*qx)
    return position,vel,acc
