#!/usr/bin/env python3
"""Show smoothly following, colored Crazyflie spheres in RViz.

Each RViz Marker is fixed to its drone's TF frame using frame_locked=True.
Unlike the previous implementation, this node does *not* repeatedly read TF
positions and republish them in 'world': RViz transforms each sphere at its
own rendering/update rate using the same TF stream as the built-in TF display.

Visualization only; no drone flight commands or physical LEDs.
"""
from __future__ import annotations

import argparse
import colorsys

import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from tf2_ros import Buffer, TransformListener, TransformException
from rclpy.time import Time
from formation_colors import ColorAnimator
from static_shapes import DRONES as DRONE_NAMES

PALETTES = ('auto', 'rainbow', 'cyan', 'pink', 'gold', 'violet')


def get_color(index: int, palette: str):
    if palette == 'rainbow':
        return colorsys.hsv_to_rgb(index / len(DRONE_NAMES), 0.84, 1.0)
    return {
        'cyan': (0.05, 0.82, 1.0),
        'pink': (1.0, 0.18, 0.43),
        'gold': (1.0, 0.72, 0.12),
        'violet': (0.64, 0.30, 1.0),
    }[palette]


class DroneMarkers(Node):
    def __init__(self, palette='auto', show_labels=False, radius=0.20):
        super().__init__('swarmgesture_drone_markers')
        self.palette = palette
        self.show_labels = show_labels
        self.radius = radius
        self.color_animator=ColorAnimator()
        self.last_color_shape=None
        if palette=='auto':
            self.color_buffer=Buffer(node=self)
            self.color_listener=TransformListener(self.color_buffer,self)
        self.publisher = self.create_publisher(MarkerArray, '/swarmgesture/markers', 10)
        # TF is read only to select colors. Positions remain frame-locked and
        # continue following RViz's own TF/render clock at full motion rate.
        self.timer = self.create_timer(.05 if palette=='auto' else 1.0, self.publish_markers)
        self.publish_markers()
        self.get_logger().info(
            f'Smooth frame-locked markers for {len(getattr(self,"DRONE_NAMES",DRONE_NAMES))} drones on '
            f'/swarmgesture/markers (palette={palette}). '
            'Project RViz config loads the MarkerArray automatically. '
            'Auto: red heart glow, blue/cyan travelling wave, gold spiral.'
        )

    def make_marker(self, drone_name, index, color, kind):
        m = Marker()
        # IMPORTANT: the marker's frame is the *drone*, not 'world'.
        m.header.frame_id = drone_name
        # Zero stamp requests the latest available TF transform.
        # Avoid requesting an exact now() time when simulator TF may lag.
        m.header.stamp.sec = 0
        m.header.stamp.nanosec = 0
        # RViz re-transforms this marker whenever the drone's frame moves.
        m.frame_locked = True
        m.ns = f'swarmgesture_{kind}'
        m.id = index
        m.action = Marker.ADD
        m.pose.orientation.w = 1.0
        m.color.r, m.color.g, m.color.b = color

        if kind == 'label':
            m.type = Marker.TEXT_VIEW_FACING
            m.text = drone_name
            m.pose.position.z = 0.36
            m.scale.z = 0.22
            m.color.a = 0.95
        else:
            m.type = Marker.SPHERE
            diameter = 2 * self.radius * (2.0 if kind == 'halo' else 1.0)
            m.scale.x = diameter
            m.scale.y = diameter
            m.scale.z = diameter
            m.color.a = ((.06+.12*max(color)) if self.palette=='auto' else .10) if kind=='halo' else .96
        return m

    def publish_markers(self):
        markers = MarkerArray()
        if self.palette=='auto':
            now=self.get_clock().now().nanoseconds/1e9
            points=[]
            for name in DRONE_NAMES:
                try: transform=self.color_buffer.lookup_transform('world',name,Time())
                except TransformException:
                    points=None;break
                stamp=transform.header.stamp
                age=now-stamp.sec-stamp.nanosec/1e9
                if not -.1<=age<=1.0:
                    points=None;break
                p=transform.transform.translation
                points.append((p.x,p.y,p.z))
            colors=self.color_animator.update(points,now)
            shape=self.color_animator.frame.shape
            if shape!=self.last_color_shape:
                self.get_logger().info(f'Color choreography: {shape}')
                self.last_color_shape=shape
        for i, name in enumerate(DRONE_NAMES):
            color = colors[i] if self.palette=='auto' else get_color(i, self.palette)
            markers.markers.append(self.make_marker(name, i, color, 'halo'))
            markers.markers.append(self.make_marker(name, i, color, 'drone'))
            if self.show_labels:
                markers.markers.append(self.make_marker(name, i, (1., 1., 1.), 'label'))
        self.publisher.publish(markers)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--palette', choices=PALETTES, default='auto')
    p.add_argument('--labels', action='store_true', help='Show Crazyflie IDs')
    p.add_argument('--radius', type=float, default=0.20, help='Sphere radius in metres')
    args, rosargs = p.parse_known_args()
    if not 0.05 <= args.radius <= 0.8:
        p.error('--radius must be between 0.05 and 0.8')
    rclpy.init(args=rosargs)
    node = DroneMarkers(args.palette, args.labels, args.radius)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
