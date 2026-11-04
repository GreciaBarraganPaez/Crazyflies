"""Opt-in Snake scene server. The normal formation server is unchanged."""
import json
import rclpy
from rclpy.parameter import Parameter
from std_msgs.msg import String
from preview_server import ContinuousPreviewServer
from runtime.snake_scene import SnakeRuntime


class SnakePreviewServer(ContinuousPreviewServer):
    def __init__(self):
        self.snake=None
        super().__init__()
        self.set_parameters([Parameter('swarmgesture.continuous_trajectories',value=False)])
        self.declare_parameter('swarmgesture.snake_scene',True)
        self.declare_parameter('swarmgesture.snake_grid',True)
        self.scene_status=self.create_publisher(String,'/swarmgesture/snake/status',10)
        self.snake=SnakeRuntime(self)
        self.scene_command=self.create_subscription(String,'/swarmgesture/snake/command',self.receive_command,10)

    def scene_event(self,data):
        msg=String();msg.data=json.dumps(data);self.scene_status.publish(msg)

    def receive_command(self,message):
        data={}
        try:
            data=json.loads(message.data)
            if not isinstance(data,dict):raise ValueError('Expected a scene command object')
            self.snake.command(data)
        except (ValueError,TypeError,KeyError) as error:
            self.snake.emit('rejected',action=data.get('action') if isinstance(data,dict) else None,reason=str(error))

    def _timer_callback(self):
        if self.snake:self.snake.update(self.backend.time())
        super()._timer_callback()

    def _takeoff_callback(self,request,response,name='all'):
        if self.snake:self.snake.clear()
        return super()._takeoff_callback(request,response,name)

    def _land_callback(self,request,response,name='all'):
        if self.snake:self.snake.clear()
        return super()._land_callback(request,response,name)


def main():
    rclpy.init();server=SnakePreviewServer()
    if server._ros_parameters['sim']['backend']!='none':raise RuntimeError('Snake requires ideal preview')
    for cf in server.cfs.values():
        cf.setpoint.position.x,cf.setpoint.position.y,cf.setpoint.position.z=map(float,cf.initialPosition)
    try:rclpy.spin(server)
    except KeyboardInterrupt:pass
    finally:
        server.on_shutdown_callback();server.destroy_node();rclpy.try_shutdown()


if __name__=='__main__':main()
