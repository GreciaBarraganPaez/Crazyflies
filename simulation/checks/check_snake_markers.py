"""ROS MarkerArray smoke check with a genuine late-joining subscriber."""
import json
import os
import time
from types import SimpleNamespace
import rclpy
from rclpy.qos import QoSProfile,DurabilityPolicy
from visualization_msgs.msg import MarkerArray
from simulation.visualization.snake_markers import SnakeMarkers,COLORS
from simulation.scenes.snake import SnakeScene,WIDTH,HEIGHT,CYCLE,step_plan
from simulation.core.static_shapes import DRONES


def payload(scene):
    return SimpleNamespace(data=json.dumps(dict(roles=scene.roles(),members=scene.members,limit=scene.limit,
        score=scene.score,state='playing',head_id=scene.actors[0],head_ids=scene.heads,
        snake_lengths=[len(s.actors) for s in scene.snakes],food_cells=scene.food_cells)))


def main():
    if os.environ.get('ROS_DOMAIN_ID')!='89':raise SystemExit('Use ROS_DOMAIN_ID=89')
    rclpy.init();node=SnakeMarkers();observer=None
    try:
        scene=SnakeScene().spawn_food()
        node.receive(payload(scene));node.publish_markers()
        assert node.publisher.qos_profile.durability==DurabilityPolicy.TRANSIENT_LOCAL
        # Subscribe only after publication; spinning the observer alone cannot
        # trigger another marker timer publish, so receipt proves retention.
        observer=rclpy.create_node('snake_marker_late_join_probe')
        captured=[]
        sub=observer.create_subscription(MarkerArray,'/swarmgesture/markers',captured.append,
            QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL))
        deadline=time.monotonic()+5
        while not captured and time.monotonic()<deadline:rclpy.spin_once(observer,timeout_sec=.1)
        assert captured,'Late subscriber did not receive the retained marker snapshot'
        markers=captured[-1].markers
        drones=[m for m in markers if m.ns=='swarmgesture_drone']
        halos=[m for m in markers if m.ns=='swarmgesture_halo']
        assert len(drones)==len(halos)==19
        assert all(m.frame_locked and m.header.frame_id in DRONES and m.pose.position.x==m.pose.position.y==m.pose.position.z==0 for m in drones+halos)
        assert sum(abs(m.color.b-COLORS['border'][2])<1e-6 and abs(m.color.r-COLORS['border'][0])<1e-6 for m in drones)==4
        assert sum(abs(m.color.r-COLORS['food'][0])<1e-6 and abs(m.color.g-COLORS['food'][1])<1e-6 for m in drones)==12
        assert any(m.ns=='snake_scene' and len(m.points)==2*(WIDTH+HEIGHT+2) for m in markers)
        assert any(m.text.startswith('AUTO SNAKE') for m in markers)
        while True:
            plan=step_plan(scene);scene=plan.after
            if plan.kind=='eat':break
        node.receive(payload(scene));node.publish_markers()
        captured.clear();deadline=time.monotonic()+3
        while not captured and time.monotonic()<deadline:rclpy.spin_once(observer,timeout_sec=.1)
        assert any(m.ns=='snake_head_label' and m.header.frame_id==DRONES[scene.actors[0]] for m in captured[-1].markers)
        drones=[m for m in captured[-1].markers if m.ns=='swarmgesture_drone']
        for marker in drones:
            expected=COLORS[scene.roles()[marker.id]]
            assert all(abs(a-b)<1e-6 for a,b in zip(
                (marker.color.r,marker.color.g,marker.color.b),expected))
        while len(scene.snakes)<2:scene=step_plan(scene).after
        node.receive(payload(scene));node.publish_markers()
        captured.clear();deadline=time.monotonic()+3
        while not captured and time.monotonic()<deadline:rclpy.spin_once(observer,timeout_sec=.1)
        labels=[m for m in captured[-1].markers if m.ns=='snake_head_label' and m.action==m.ADD]
        assert len(labels)==2 and {m.header.frame_id for m in labels}=={DRONES[i] for i in scene.heads}
        print('SNAKE_MARKERS_PASS: retained late-join delivery; 19 frame-locked drones/halos; fixed role colors; 12 apples; 4 borders; both head labels follow their actual drones.')
    finally:
        if observer:observer.destroy_node()
        node.destroy_node();rclpy.try_shutdown()


if __name__=='__main__':main()
