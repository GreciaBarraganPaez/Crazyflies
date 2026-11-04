"""Snake roles and scene legend on the existing frame-locked MarkerArray."""
import json
import math
import rclpy
from std_msgs.msg import String
from geometry_msgs.msg import Point
from visualization_msgs.msg import Marker, MarkerArray
from drone_markers import DroneMarkers
from static_shapes import DRONES
from scenes.snake import RADIUS,CENTER_Z,PICKUP,COLLECTION_RADIUS

COLORS={'head':(1.,.72,.08),'body':(.05,.9,.65),'waiting':(.6,.25,.95),
        'pickup':(.25,1.,.2),'parked':(.2,.3,.42)}


class SnakeMarkers(DroneMarkers):
    def __init__(self):
        self.roles=('parked',)*len(DRONES)
        self.caption='Snake: arm, take off, then peace / three to start'
        super().__init__(palette='cyan',show_labels=False)
        self.destroy_timer(self.timer)
        self.timer=self.create_timer(.1,self.publish_markers)
        self.scene_subscription=self.create_subscription(String,'/swarmgesture/snake/status',self.receive,10)
        self.get_logger().info('Snake roles: gold head, teal body, purple waiting, green pickup, dim parked.')

    def receive(self,message):
        try:data=json.loads(message.data)
        except (ValueError,TypeError):return
        if not isinstance(data,dict):return
        roles=data.get('roles',[])
        if len(roles)==len(DRONES) and all(r in COLORS for r in roles):self.roles=tuple(roles)
        direction='CW' if data.get('direction',-1)==-1 else 'CCW'
        self.caption=f'SNAKE  |  {data.get("members",0)}/{data.get("limit",5)} in chain  |  score {data.get("score",0)}  |  {direction}  |  {data.get("state","grid")}'

    def world_marker(self,kind,marker_id,color):
        m=Marker();m.header.frame_id='world';m.ns='snake_scene';m.id=marker_id
        m.type=kind;m.action=Marker.ADD;m.pose.orientation.w=1.
        m.color.r,m.color.g,m.color.b=color;m.color.a=.85
        return m

    def publish_markers(self):
        array=MarkerArray()
        for i,name in enumerate(DRONES):
            color=COLORS[self.roles[i]]
            array.markers.append(self.make_marker(name,i,color,'drone'))
            array.markers.append(self.make_marker(name,i,color,'halo'))
        track=self.world_marker(Marker.LINE_STRIP,0,(.15,.4,.6));track.scale.x=.025
        track.points=[Point(x=RADIUS*math.cos(i*2*math.pi/96),y=0.,z=CENTER_Z+RADIUS*math.sin(i*2*math.pi/96)) for i in range(97)]
        array.markers.append(track)
        label=self.world_marker(Marker.TEXT_VIEW_FACING,1,(.9,.95,1.));label.scale.z=.30
        label.pose.position.x=2.8;label.pose.position.z=7.5;label.text=self.caption
        array.markers.append(label)
        pickup=self.world_marker(Marker.SPHERE,2,(.3,1.,.2));pickup.color.a=.10
        pickup.pose.position.x,pickup.pose.position.y,pickup.pose.position.z=PICKUP
        pickup.scale.x=pickup.scale.y=pickup.scale.z=2*COLLECTION_RADIUS
        array.markers.append(pickup)
        self.publisher.publish(array)


def main():
    rclpy.init();node=SnakeMarkers()
    try:rclpy.spin(node)
    except KeyboardInterrupt:pass
    finally:node.destroy_node();rclpy.try_shutdown()


if __name__=='__main__':main()
