"""Adapters invoke this check process's own simulator, never another ROS fleet."""
from rclpy.duration import Duration
from crazyflie_interfaces import srv
from crazyflie_interfaces.msg import TrajectoryPolynomialPiece
from simulation.core.static_shapes import DRONES

class Drone:
    def __init__(self,fleet,name):self.fleet,self.name=fleet,name
    def goTo(self,point,yaw,duration):
        self.fleet.go_to_count+=1
        request=srv.GoTo.Request()
        request.goal.x,request.goal.y,request.goal.z=point
        request.yaw=yaw;request.duration=Duration(seconds=duration).to_msg()
        self.fleet.server._go_to_callback(request,srv.GoTo.Response(),self.name)
    def uploadTrajectory(self,trajectory_id,offset,trajectory):
        request=srv.UploadTrajectory.Request()
        request.trajectory_id=trajectory_id;request.piece_offset=offset
        for polynomial in trajectory.polynomials:
            piece=TrajectoryPolynomialPiece()
            piece.duration=Duration(seconds=polynomial.duration).to_msg()
            piece.poly_x=polynomial.px.p.tolist();piece.poly_y=polynomial.py.p.tolist()
            piece.poly_z=polynomial.pz.p.tolist();piece.poly_yaw=polynomial.pyaw.p.tolist()
            request.pieces.append(piece)
        self.fleet.server._upload_trajectory_callback(request,srv.UploadTrajectory.Response(),self.name)


class Fleet:
    def __init__(self,server):
        self.server=server;self.go_to_count=0
        self.crazyfliesByName={name:Drone(self,name) for name in DRONES}
    def takeoff(self,targetHeight,duration):
        request=srv.Takeoff.Request();request.height=targetHeight
        request.duration=Duration(seconds=duration).to_msg()
        self.server._takeoff_callback(request,srv.Takeoff.Response())
    def land(self,targetHeight,duration):
        request=srv.Land.Request();request.height=targetHeight
        request.duration=Duration(seconds=duration).to_msg()
        self.server._land_callback(request,srv.Land.Response())
    def startTrajectory(self,trajectory_id,relative=False):
        request=srv.StartTrajectory.Request();request.trajectory_id=trajectory_id
        request.relative=relative;request.timescale=1.
        self.server._start_trajectory_callback(request,srv.StartTrajectory.Response())
