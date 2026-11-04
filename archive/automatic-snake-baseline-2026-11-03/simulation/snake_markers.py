"""Snake roles and scene legend on the existing frame-locked MarkerArray."""
import json
import rclpy
from std_msgs.msg import String
from rclpy.qos import QoSProfile,DurabilityPolicy
from geometry_msgs.msg import Point
from visualization_msgs.msg import Marker, MarkerArray
from drone_markers import DroneMarkers
from static_shapes import DRONES
from scenes.snake import WIDTH,HEIGHT,CELL,BASE_Z,world

COLORS={'head':(1.,.72,.08),'body':(.05,.9,.65),'food':(1.,.12,.15),
        'head2':(.85,.4,1.),'body2':(.12,.65,1.),'border':(.20,.65,1.),'parked':(.2,.3,.42)}


class SnakeMarkers(DroneMarkers):
    def __init__(self):
        self.roles=('parked',)*len(DRONES)
        self.food_cells=[]
        self.head_id=None
        self.head_ids=()
        self.caption='Autonomous Snake: arm, take off, then peace / three / OK'
        super().__init__(palette='cyan',show_labels=False)
        self.destroy_publisher(self.publisher)
        qos=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.publisher=self.create_publisher(MarkerArray,'/swarmgesture/markers',qos)
        self.destroy_timer(self.timer)
        self.timer=self.create_timer(.05,self.publish_markers)
        self.scene_subscription=self.create_subscription(String,'/swarmgesture/snake/status',self.receive,qos)
        self.publish_markers()
        self.get_logger().info('Winding Snake: gold/teal and purple/blue groups, red apples, cyan border; latched MarkerArray.')

    def receive(self,message):
        try:data=json.loads(message.data)
        except (ValueError,TypeError):return
        if not isinstance(data,dict):return
        roles=data.get('roles',[])
        if len(roles)==len(DRONES) and all(r in COLORS for r in roles):self.roles=tuple(roles)
        self.food_cells=data.get('food_cells',[])
        self.head_id=data.get('head_id')
        self.head_ids=tuple(data.get('head_ids',[self.head_id] if self.head_id is not None else []))
        lengths='/'.join(str(n) for n in data.get('snake_lengths',[]))
        self.caption=f'AUTO SNAKE  |  {data.get("members",0)}/{data.get("limit",15)} drones ({lengths})  |  apples {len(self.food_cells)}  |  score {data.get("score",0)}  |  {data.get("state","grid")}'

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
        label.pose.position.x=0.;label.pose.position.z=14.;label.text=self.caption
        array.markers.append(label)
        # A fixed set of IDs also removes food highlights after collection.
        for index in range(len(DRONES)):
            pickup=self.world_marker(Marker.LINE_STRIP,2+index,(1.,.2,.2));pickup.scale.x=.025
            if index>=len(self.food_cells):pickup.action=Marker.DELETE
            else:
                x,_,z=world(self.food_cells[index]);r=CELL*.32
                pickup.points=[Point(x=x+a*r,y=.04,z=z+b*r) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1),(-1,-1))]
            array.markers.append(pickup)
        for group in range(2):
            head=self.world_marker(Marker.TEXT_VIEW_FACING,group,COLORS['head2' if group else 'head']);head.ns='snake_head_label'
            if group>=len(self.head_ids):head.action=Marker.DELETE
            else:
                head.header.frame_id=DRONES[self.head_ids[group]];head.frame_locked=True
                head.pose.position.z=.48;head.scale.z=.28;head.text='HEAD '+str(group+1)
            array.markers.append(head)
        self.publisher.publish(array)


def main():
    rclpy.init();node=SnakeMarkers()
    try:rclpy.spin(node)
    except KeyboardInterrupt:pass
    finally:node.destroy_node();rclpy.try_shutdown()


if __name__=='__main__':main()
