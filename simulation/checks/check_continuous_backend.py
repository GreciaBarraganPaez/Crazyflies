"""Isolated installed-firmware planner checks. No ROS services or fleet commands."""
import math
from crazyflie_sim.crazyflie_sil import CrazyflieSIL, TrajectoryPolynomialPiece
from simulation.core.continuous_trajectories import compile_trajectories, PERIODS, motion
from simulation.core.static_shapes import DRONES, HOME, targets, minimum_distance


def check(count, speed=1.0):
    worst = float('inf')
    for shape in PERIODS:
        clock = [0.0]
        fleet = [CrazyflieSIL(name,point,'none',lambda:clock[0])
                 for name,point in zip(DRONES[:count],targets(shape)[:count])]
        for trajectory_id, entry in ((70,True),(71,False)):
            for cf,path in zip(fleet,compile_trajectories(shape,entry,speed=speed)):
                cf.uploadTrajectory(trajectory_id,0,[TrajectoryPolynomialPiece(*p.axes,(0.,)*8,p.duration) for p in path])
        for cf in fleet:cf.startTrajectory(70,relative=False)
        period = PERIODS[shape]/speed
        for cycle in range(4):
            if cycle:
                clock[0] = cycle*period
                for cf in fleet:cf.startTrajectory(71,relative=False)
            for step in range(160):
                clock[0] = cycle*period + period*step/160
                states = [cf.getSetpoint() for cf in fleet]
                assert min(s.pos[2] for s in states)>.6,(shape,cycle,step)
                expected = motion(shape,period*step/160,entry=cycle==0,speed=speed)
                for cf,state,goal in zip(fleet,states,expected):
                    cf.setState(state)
                    assert math.dist(state.pos,goal[0])<1e-4
                    assert math.dist(state.vel,goal[1])<1e-4, (shape,cycle,step,state.vel,goal[1])
                worst = min(worst,minimum_distance([tuple(s.pos) for s in states]))
        # Stop at several moving phases, normalize via native high-level goTo.
        for phase in range(16):
            for brake_in_place in (False, True):
                clock[0] += .5
                for cf in fleet:cf.startTrajectory(71,relative=False)
                clock[0] += period*phase/16
                before=[cf.getSetpoint() for cf in fleet]
                for cf,state in zip(fleet,before):cf.setState(state)
                goals=tuple(tuple(s.pos) for s in before) if brake_in_place else targets(shape)
                seconds=.4 if brake_in_place else 1.0
                for cf,goal in zip(fleet,goals):cf.goTo(goal,0.,seconds)
                start=clock[0]
                for frame in range(101):
                    clock[0]=start+seconds*frame/100
                    states=[cf.getSetpoint() for cf in fleet]
                    assert min(s.pos[2] for s in states)>.6,(shape,phase,brake_in_place)
                    for cf,state in zip(fleet,states):cf.setState(state)
                    worst=min(worst,minimum_distance([tuple(s.pos) for s in states]))
        for cf,goal in zip(fleet,HOME):cf.goTo(goal,0.,4.8)
        clock[0]+=5
        for cf in fleet:
            cf.setState(cf.getSetpoint())
            cf.land(.04,3.2)
    assert worst>=.52,worst
    print(f'{count} isolated planners at {speed:g}x: continuous joins, 16 stop phases per shape and high-level landing passed; minimum spacing {worst:.3f}m')


if __name__ == '__main__':
    for speed in (.5,1.,1.25):
        check(3,speed)
        check(19,speed)
