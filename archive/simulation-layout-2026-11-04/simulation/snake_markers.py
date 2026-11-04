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
    DRONE_NAMES=DRONES
    BOARD=(WIDTH,HEIGHT,CELL,BASE_Z)
    WORLD=staticmethod(world)
    TOPIC='/swarmgesture/snake/status'
    TITLE='AUTO SNAKE'
    INITIAL_CAPTION='Autonomous Snake: arm, take off, then peace / three / OK'
    LOG_DESCRIPTION='Winding Snake: gold/teal and purple/blue groups, red apples, cyan border; latched MarkerArray.'


    def __init__(self):
        self.drone_names=self.DRONE_NAMES
        self.width,self.height,self.cell,self.base_z=self.BOARD
        self.roles=('parked',)*len(self.drone_names)
        self.food_cells=[]
        self.head_id=None
        self.head_ids=()
        self.caption=self.INITIAL_CAPTION
        super().__init__(palette='cyan',show_labels=False)
        self.destroy_publisher(self.publisher)
        qos=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.publisher=self.create_publisher(MarkerArray,'/swarmgesture/markers',qos)
        self.destroy_timer(self.timer)
        self.timer=self.create_timer(.05,self.publish_markers)
        self.scene_subscription=self.create_subscription(String,self.TOPIC,self.receive,qos)
        self.publish_markers()
        self.get_logger().info(self.LOG_DESCRIPTION)

    def receive(self,message):
        try:data=json.loads(message.data)
        except (ValueError,TypeError):return
        if not isinstance(data,dict):return
        roles=data.get('roles',[])
        if len(roles)==len(self.drone_names) and all(r in COLORS for r in roles):self.roles=tuple(roles)
        self.food_cells=data.get('food_cells',[])
        self.head_id=data.get('head_id')
        self.head_ids=tuple(data.get('head_ids',[self.head_id] if self.head_id is not None else []))
        lengths='/'.join(str(n) for n in data.get('snake_lengths',[]))
        self.caption=f'{self.TITLE}  |  {data.get("members",0)}/{data.get("limit",15)} drones ({lengths})  |  apples {len(self.food_cells)}  |  score {data.get("score",0)}  |  {data.get("state","grid")}'

    def world_marker(self,kind,marker_id,color):
        m=Marker();m.header.frame_id='world';m.ns='snake_scene';m.id=marker_id
        m.type=kind;m.action=Marker.ADD;m.pose.orientation.w=1.
        m.color.r,m.color.g,m.color.b=color;m.color.a=.85
        return m

    def publish_markers(self):
        array=MarkerArray()
        for i,name in enumerate(self.drone_names):
            color=COLORS[self.roles[i]]
            array.markers.append(self.make_marker(name,i,color,'drone'))
            array.markers.append(self.make_marker(name,i,color,'halo'))
        track=self.world_marker(Marker.LINE_LIST,0,(.15,.4,.6));track.scale.x=.018
        left,right=-self.width*self.cell/2,self.width*self.cell/2
        bottom,top=self.base_z-self.cell/2,self.base_z+(self.height-.5)*self.cell
        for i in range(self.width+1):
            x=left+i*self.cell
            track.points.extend((Point(x=x,y=.06,z=bottom),Point(x=x,y=.06,z=top)))
        for j in range(self.height+1):
            z=bottom+j*self.cell
            track.points.extend((Point(x=left,y=.06,z=z),Point(x=right,y=.06,z=z)))
        array.markers.append(track)
        label=self.world_marker(Marker.TEXT_VIEW_FACING,1,(.9,.95,1.));label.scale.z=.30
        label.pose.position.x=0.;label.pose.position.z=self.base_z+self.height*self.cell+.1;label.text=self.caption
        array.markers.append(label)
        # A fixed set of IDs also removes food highlights after collection.
        for index in range(len(self.drone_names)):
            pickup=self.world_marker(Marker.LINE_STRIP,2+index,(1.,.2,.2));pickup.scale.x=.025
            if index>=len(self.food_cells):pickup.action=Marker.DELETE
            else:
                x,_,z=self.WORLD(self.food_cells[index]);r=self.cell*.32
                pickup.points=[Point(x=x+a*r,y=.04,z=z+b*r) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1),(-1,-1))]
            array.markers.append(pickup)
        for group in range(2):
            head=self.world_marker(Marker.TEXT_VIEW_FACING,group,COLORS['head2' if group else 'head']);head.ns='snake_head_label'
            if group>=len(self.head_ids):head.action=Marker.DELETE
            else:
                head.header.frame_id=self.drone_names[self.head_ids[group]];head.frame_locked=True
                head.pose.position.z=.48;head.scale.z=.28;head.text='HEAD '+str(group+1)
            array.markers.append(head)
        self.publisher.publish(array)


def main():
    rclpy.init();node=SnakeMarkers()
    try:rclpy.spin(node)
    except KeyboardInterrupt:pass
    finally:node.destroy_node();rclpy.try_shutdown()


if __name__=='__main__':main()
