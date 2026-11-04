#!/usr/bin/env python3
"""Show colored sphere + halo markers at each Crazyflie TF pose in RViz.

Pure visualization: does not command drones and does not represent hardware LEDs.
Uses Crazyswarm2's 'world' -> cf231..cf249 transforms (simulation may show
setpoint positions rather than independently measured physical poses).
"""
from __future__ import annotations

import argparse
import colorsys

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformException, TransformListener
from visualization_msgs.msg import Marker, MarkerArray

DRONE_NAMES = tuple(f'cf{i}' for i in range(231, 250))
PALETTES = ('rainbow', 'cyan', 'pink', 'gold', 'violet')


def get_color(index: int, palette: str):
    if palette == 'rainbow':
        return colorsys.hsv_to_rgb((index / len(DRONE_NAMES)) % 1.0, 0.84, 1.0)
    return {
        'cyan': (0.05, 0.82, 1.0),
        'pink': (1.0, 0.18, 0.43),
        'gold': (1.0, 0.72, 0.12),
        'violet': (0.64, 0.30, 1.0),
    }[palette]


class DroneMarkers(Node):
    def __init__(self, palette='rainbow', show_labels=False, radius=0.20):
        super().__init__('swarmgesture_drone_markers')
        self.palette = palette
        self.show_labels = show_labels
        self.radius = radius
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)
        self.publisher = self.create_publisher(MarkerArray, '/swarmgesture/markers', 10)
        self.timer = self.create_timer(0.1, self.tick)
        self.warned = False
        self.get_logger().info(
            f'Publishing colored drones to /swarmgesture/markers; palette={palette}, '
            f'labels={show_labels}. In RViz add display MarkerArray, topic /swarmgesture/markers.')

    def marker(self, name, marker_id, position, color, kind):
        m = Marker()
        m.header.frame_id = 'world'
        m.header.stamp = self.get_clock().now().to_msg()
        m.ns = f'swarmgesture_{kind}'
        m.id = marker_id
        m.action = Marker.ADD
        m.pose.position.x = position.x
        m.pose.position.y = position.y
        m.pose.position.z = position.z
        m.pose.orientation.w = 1.0
        m.color.r, m.color.g, m.color.b = color
        if kind == 'label':
            m.type = Marker.TEXT_VIEW_FACING
            m.text = name
            m.pose.position.z += 0.36
            m.scale.z = 0.22
            m.color.a = 0.95
        else:
            m.type = Marker.SPHERE
            diameter = self.radius * 2 * (2.0 if kind == 'halo' else 1.0)
            m.scale.x = diameter
            m.scale.y = diameter
            m.scale.z = diameter
            m.color.a = 0.10 if kind == 'halo' else 0.96
        return m

    def tick(self):
        arr = MarkerArray()
        found = 0
        for i, name in enumerate(DRONE_NAMES):
            try:
                tf = self.buffer.lookup_transform('world', name, Time())
            except TransformException:
                continue
            found += 1
            pos = tf.transform.translation
            color = get_color(i, self.palette)
            arr.markers.append(self.marker(name, i, pos, color, 'halo'))
            arr.markers.append(self.marker(name, i, pos, color, 'drone'))
            if self.show_labels:
                arr.markers.append(self.marker(name, i, pos, (1., 1., 1.), 'label'))
        if found:
            self.publisher.publish(arr)
            self.warned = False
        elif not self.warned:
            self.get_logger().warning('No Crazyflie TF frames yet. Start the simulator and wait for /tf.')
            self.warned = True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--palette', choices=PALETTES, default='rainbow')
    p.add_argument('--labels', action='store_true', help='Also show cf231...cf249 labels')
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
