"""Opt-in Snake input adapter; reuse manual arming and measured grid landing."""
import json
import gesture_bridge as bridge
from static_shapes import HOME
from scenes.snake import validate_limit


class SnakeController(bridge.SimulationController):
    def __init__(self,swarm,grid_arrived=None):
        super().__init__(swarm,grid_arrived)
        self.limit=19
        self.seed=31
        self.moves=0
        self.members=0
        self.returning=False
        self.send_command=None

    def configure_backend(self,backend):
        if backend!='none':raise RuntimeError('Snake is preview-only; use Start-SwarmGesture-Snake.cmd')
        import rclpy
        from rclpy.parameter_client import AsyncParameterClient
        from std_msgs.msg import String
        client=AsyncParameterClient(self.swarm.allcfs,'crazyflie_server')
        if not client.wait_for_services(timeout_sec=2):raise RuntimeError('Snake server unavailable')
        future=client.get_parameters(['swarmgesture.snake_scene','swarmgesture.snake_grid'])
        rclpy.spin_until_future_complete(self.swarm.allcfs,future,timeout_sec=2)
        if not future.done() or future.exception() or not all(p.bool_value for p in future.result().values):
            raise RuntimeError('Restart the Snake ROS server to load autonomous grid Snake')
        self.publisher=self.swarm.allcfs.create_publisher(String,'/swarmgesture/snake/command',10)
        self.subscription=self.swarm.allcfs.create_subscription(String,'/swarmgesture/snake/status',self.receive_status,10)
        def send(data):
            message=String();message.data=json.dumps(data);self.publisher.publish(message)
        self.send_command=send
        print('AUTONOMOUS GRID SNAKE: one=takeoff; peace/three/OK=start; fist=grid; palm=grid then land.',flush=True)

    def request(self,action,**details):
        if self.send_command is None:raise RuntimeError('Snake transport is not configured')
        self.send_command(dict(action=action,**details))

    def start(self):
        if self.state!='ready':
            print('Take off to the grid first. Once started, Snake chooses its own route and collects automatically.',flush=True)
            return
        self.state='scene_start'
        self.request('start',limit=self.limit,seed=self.seed)

    def receive_status(self,message):
        try:data=json.loads(message.data)
        except (ValueError,TypeError):return
        if not isinstance(data,dict):return
        event=data.get('event')
        self.members=data.get('members',self.members)
        self.moves=data.get('moves',self.moves)
        if event=='grid' and self.returning:
            self.returning=False
            self.state='to_grid';self.current_goals=HOME;self.due=self.clock()
        elif event=='playing' and not self.returning:self.state='snake'
        elif event=='collected':
            print(f'SNAKE: collected without contact; chain={self.members}, score={data.get("score",0)}.',flush=True)
        elif event=='rejected':
            print('Snake request rejected: '+str(data.get('reason')),flush=True)
            if self.state=='scene_start' and data.get('action')=='start':self.state='ready'
            elif self.returning and data.get('action')=='return':
                self.returning=False;self.land_after_grid=False;self.state='snake'
        elif event=='started':
            print(f'Snake {data.get("action")}: certified center-distance bound {data.get("bound",0):.3f}m.',flush=True)

    def _return(self,land):
        if self.returning:
            self.land_after_grid=self.land_after_grid or land;return
        self.returning=True
        self.land_after_grid=land
        self.state='scene_return'
        self.request('return')

    def handle(self,label,now=None):
        if label not in ('one','palm','fist','peace','three','ok'):return
        if self.queued_gesture=='palm' and label!='palm':return
        now=self.clock() if now is None else now
        self.update(now)
        if self.state in ('scene_start','snake','scene_return'):
            if label=='palm':self.land('Open palm',now)
            elif label=='fist':self._return(False)
            elif label in ('peace','three','ok') and not self.returning:
                print('Snake is playing automatically; no steering or collect command is needed.',flush=True)
            return
        if self.state=='ready' and label in ('peace','three','ok'):
            self.start();return
        if self.state=='to_grid' and label in ('peace','three','ok'):
            if not self.land_after_grid:self.queued_gesture=label
            return
        # A shape gesture during takeoff is handled after the shared lifecycle
        # reaches ready. The six trained labels themselves stay unchanged.
        super().handle(label,now)

    def land(self,reason='Land',now=None):
        self.armed=False
        if self.state in ('scene_start','snake','scene_return'):
            self._return(True);return
        super().land(reason,now)

    def keyboard_command(self,command):
        words=command.split()
        if not words:return
        if words[0]=='count':
            try:
                if len(words)!=2:raise ValueError('Use count 3..19 while grounded')
                count=validate_limit(int(words[1]))
                if self.state!='grounded':raise ValueError('Land before changing the scene limit')
            except ValueError as error:print(str(error),flush=True);return
            self.limit=count;self.armed=False
            print(f'Snake limit={count}; initial chain=3. Arm again before takeoff.',flush=True)
        elif command=='snake':self.start()
        elif words[0]=='seed':
            try:
                if len(words)!=2 or self.state!='grounded':raise ValueError('Use seed INTEGER while grounded')
                self.seed=int(words[1]);self.armed=False
                print(f'Snake seed={self.seed}; arm again before takeoff.',flush=True)
            except ValueError as error:print(str(error),flush=True)
        elif command=='grid':self.handle('fist')
        elif command=='status':print(f'Snake state={self.state}; members={self.members}; limit={self.limit}; moves={self.moves}; armed={self.armed}.',flush=True)
        else:print('Autonomous Snake: snake=start; grid=return; count 3..19 / seed INTEGER (grounded); status. a=arm, x=land.',flush=True)


if __name__=='__main__':
    bridge.ACTIONS.update({label:'start autonomous grid Snake' for label in ('peace','three','ok')})
    bridge.main(controller_type=SnakeController)
