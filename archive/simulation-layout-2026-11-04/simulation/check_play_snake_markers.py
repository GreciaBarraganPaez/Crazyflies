"""Retained MarkerArray check for the eight-drone playable board, ROS domain 89."""
import json
import os
import time
from types import SimpleNamespace
import rclpy
from rclpy.qos import QoSProfile,DurabilityPolicy
from visualization_msgs.msg import MarkerArray
from play_snake_markers import PlayerMarkers
from snake_markers import COLORS
from scenes.play_snake import DRONES,PlayerScene,WIDTH,HEIGHT,step_plan


def main():
    if os.environ.get('ROS_DOMAIN_ID')!='89':raise SystemExit('Use ROS_DOMAIN_ID=89')
    rclpy.init();node=PlayerMarkers();observer=None
    try:
        scene=PlayerScene()
        def payload(scene):return SimpleNamespace(data=json.dumps(dict(roles=scene.roles(),members=scene.members,
            limit=8,score=scene.score,state='playing smoothly',head_id=scene.actors[0],head_ids=scene.heads,
            snake_lengths=[scene.members],food_cells=scene.food_cells)))
        node.receive(payload(scene));node.publish_markers()
        observer=rclpy.create_node('hand_snake_late_marker_probe');captured=[]
        sub=observer.create_subscription(MarkerArray,'/swarmgesture/markers',captured.append,
            QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL))
        deadline=time.monotonic()+5
        while not captured and time.monotonic()<deadline:rclpy.spin_once(observer,timeout_sec=.1)
        assert captured,'Retained marker snapshot was not delivered'
        markers=captured[-1].markers
        spheres=[m for m in markers if m.ns=='swarmgesture_drone']
        halos=[m for m in markers if m.ns=='swarmgesture_halo']
        assert len(spheres)==len(halos)==8
        assert all(m.frame_locked and m.header.frame_id in DRONES for m in spheres+halos)
        assert sum(abs(m.color.r-1)<1e-6 and abs(m.color.g-.12)<1e-6 for m in spheres)==5
        assert any(m.ns=='snake_scene' and len(m.points)==2*(WIDTH+HEIGHT+2) for m in markers)
        assert any(m.text.startswith('HAND SNAKE') for m in markers)
        while scene.members==3:scene=step_plan(scene,'right').after
        node.receive(payload(scene));node.publish_markers();captured.clear()
        deadline=time.monotonic()+3
        while not captured and time.monotonic()<deadline:rclpy.spin_once(observer,timeout_sec=.1)
        labels=[m for m in captured[-1].markers if m.ns=='snake_head_label' and m.action==m.ADD]
        assert len(labels)==1 and labels[0].header.frame_id==DRONES[scene.actors[0]]
        print('PLAY_SNAKE_MARKERS_PASS: eight retained frame-locked drones, five apples, board, one identity-preserving head label.')
    finally:
        if observer:observer.destroy_node()
        node.destroy_node();rclpy.try_shutdown()


if __name__=='__main__':main()
