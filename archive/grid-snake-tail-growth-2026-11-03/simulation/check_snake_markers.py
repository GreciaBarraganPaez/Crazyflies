"""Read-only marker-message smoke check, isolated from the live project."""
import json
import os
from types import SimpleNamespace
import rclpy
from snake_markers import SnakeMarkers,COLORS
from scenes.snake import SnakeScene
from static_shapes import DRONES


def main():
    if os.environ.get('ROS_DOMAIN_ID')!='89':raise SystemExit('Use ROS_DOMAIN_ID=89')
    rclpy.init();node=SnakeMarkers()
    try:
        captured=[];node.publisher=SimpleNamespace(publish=captured.append)
        scene=SnakeScene().spawn_food()
        node.receive(SimpleNamespace(data=json.dumps(dict(roles=scene.roles(),members=3,limit=19,score=0,state='playing',food=scene.food))))
        node.publish_markers()
        markers=captured[-1].markers
        drones=[m for m in markers if m.ns=='swarmgesture_drone']
        halos=[m for m in markers if m.ns=='swarmgesture_halo']
        assert len(drones)==len(halos)==19
        assert all(m.frame_locked and m.header.frame_id in DRONES and m.pose.position.x==m.pose.position.y==m.pose.position.z==0 for m in drones+halos)
        assert drones[0].color.r==COLORS['head'][0]
        assert abs(drones[3].color.g-COLORS['food'][1])<1e-6
        assert any(m.ns=='snake_scene' and len(m.points)==32 for m in markers)
        assert any(m.text.startswith('AUTO SNAKE') for m in markers)
        print('SNAKE_MARKERS_PASS: 19 frame-locked drones/halos, role colors, grid board, food highlight and score caption.')
    finally:node.destroy_node();rclpy.try_shutdown()


if __name__=='__main__':main()
