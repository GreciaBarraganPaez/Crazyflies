"""Saved board and eight frame-locked drone markers for the playable mode."""
import rclpy
from snake_markers import SnakeMarkers
from scenes.play_snake import DRONES,WIDTH,HEIGHT,CELL,BASE_Z,world


class PlayerMarkers(SnakeMarkers):
    DRONE_NAMES=DRONES
    BOARD=(WIDTH,HEIGHT,CELL,BASE_Z)
    WORLD=staticmethod(world)
    TOPIC='/swarmgesture/snake_player/status'
    TITLE='HAND SNAKE'
    INITIAL_CAPTION='Hand Snake: arm, take off, peace to start; point and move hand to steer'
    LOG_DESCRIPTION='Hand Snake: eight drones; gold head, teal body, red apples; latched MarkerArray.'

    def receive(self,message):
        super().receive(message)
        self.caption=self.caption.replace('playing smoothly','point one finger: move hand to steer')


def main():
    rclpy.init();node=PlayerMarkers()
    try:rclpy.spin(node)
    except KeyboardInterrupt:pass
    finally:node.destroy_node();rclpy.try_shutdown()


if __name__=='__main__':main()
