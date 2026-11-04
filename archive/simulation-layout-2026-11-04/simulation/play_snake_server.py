"""Independent eight-drone ideal simulator for hand-controlled Snake."""
import rclpy
from rclpy.parameter import Parameter
from snake_preview_server import SnakePreviewServer
from runtime.play_snake import PlayerRuntime


class PlayerServer(SnakePreviewServer):
    RUNTIME_CLASS=PlayerRuntime
    TOPIC='/swarmgesture/snake_player'

    def __init__(self):
        super().__init__()
        self.declare_parameter('swarmgesture.snake_player',True)
        self.set_parameters([Parameter('swarmgesture.snake_split',value=False)])


def main():
    rclpy.init();server=PlayerServer()
    if server._ros_parameters['sim']['backend']!='none':raise RuntimeError('Hand Snake requires ideal preview')
    for cf in server.cfs.values():
        cf.setpoint.position.x,cf.setpoint.position.y,cf.setpoint.position.z=map(float,cf.initialPosition)
    try:rclpy.spin(server)
    except KeyboardInterrupt:pass
    finally:server.on_shutdown_callback();server.destroy_node();rclpy.try_shutdown()


if __name__=='__main__':main()
