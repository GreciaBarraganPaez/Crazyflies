"""Snake roles and scene legend on the existing frame-locked MarkerArray."""
import json
import rclpy
from std_msgs.msg import String
from geometry_msgs.msg import Point
from visualization_msgs.msg import Marker, MarkerArray
from drone_markers import DroneMarkers
from static_shapes import DRONES
from scenes.snake import WIDTH,HEIGHT,CELL,BASE_Z,world

COLORS={'head':(1.,.72,.08),'body':(.05,.9,.65),'food':(1.,.12,.15),'parked':(.2,.3,.42)}


class SnakeMarkers(DroneMarkers):
    def __init__(self):
        self.roles=('parked',)*len(DRONES)
        self.food=None
        self.caption='Autonomous Snake: arm, take off, then peace / three / OK'
        super().__init__(palette='cyan',show_labels=False)
        self.destroy_timer(self.timer)
        self.timer=self.create_timer(.1,self.publish_markers)
        self.scene_subscription=self.create_subscription(String,'/swarmgesture/snake/status',self.receive,10)
        self.get_logger().info('Grid Snake: gold head, teal body, red food, dim parked; automatic play.')

    def receive(self,message):
        try:data=json.loads(message.data)
        except (ValueError,TypeError):return
        if not isinstance(data,dict):return
        roles=data.get('roles',[])
        if len(roles)==len(DRONES) and all(r in COLORS for r in roles):self.roles=tuple(roles)
        self.food=data.get('food')
        self.caption=f'AUTO SNAKE  |  {data.get("members",0)}/{data.get("limit",19)} drones  |  score {data.get("score",0)}  |  {data.get("state","grid")}'

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
        track=self.world_marker(Marker.LINE_LIST,0,(.15,.4,.6));track.scale.x=.018
        left,right=-WIDTH*CELL/2,WIDTH*CELL/2
        bottom,top=BASE_Z-CELL/2,BASE_Z+(HEIGHT-.5)*CELL
        for i in range(WIDTH+1):
            x=left+i*CELL
            track.points.extend((Point(x=x,y=.06,z=bottom),Point(x=x,y=.06,z=top)))
        for j in range(HEIGHT+1):
            z=bottom+j*CELL
            track.points.extend((Point(x=left,y=.06,z=z),Point(x=right,y=.06,z=z)))
        array.markers.append(track)
        label=self.world_marker(Marker.TEXT_VIEW_FACING,1,(.9,.95,1.));label.scale.z=.30
        label.pose.position.x=2.8;label.pose.position.z=8.2;label.text=self.caption
        array.markers.append(label)
        pickup=self.world_marker(Marker.LINE_STRIP,2,(1.,.2,.2));pickup.scale.x=.035
        if self.food is None:pickup.action=Marker.DELETE
        else:
            x,_,z=world(self.food);r=CELL*.42
            pickup.points=[Point(x=x+a*r,y=.04,z=z+b*r) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1),(-1,-1))]
        array.markers.append(pickup)
        self.publisher.publish(array)


def main():
    rclpy.init();node=SnakeMarkers()
    try:rclpy.spin(node)
    except KeyboardInterrupt:pass
    finally:node.destroy_node();rclpy.try_shutdown()


if __name__=='__main__':main()
