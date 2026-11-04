"""Eight-drone hand-steered Snake; keep the existing animation mode separate."""
from simulation.controllers.snake_controller import SnakeController
from simulation.scenes.play_snake import DRONES,HOME,DIRECTIONS
from simulation.core.static_shapes import minimum_distance
import simulation.controllers.gesture_bridge as bridge


class PlayerController(SnakeController):
    DRONE_NAMES=DRONES
    HOME_POINTS=HOME
    TOPIC='/swarmgesture/snake_player'
    CAPABILITIES=('swarmgesture.snake_player',)
    INPUT_ACTIONS={name:'steer snake '+name for name in DIRECTIONS}
    MODE_DESCRIPTION='HAND SNAKE: peace=start; point one finger and move hand left/right/up/down; fist=grid; palm=land.'
    LAUNCHER='Start-SwarmGesture-Snake-Player.cmd'
    RESTART_MESSAGE='Restart all programs using Start-SwarmGesture-Snake-Player.cmd for the eight-drone hand-controlled game'

    def __init__(self,swarm,grid_arrived=None):
        super().__init__(swarm,grid_arrived);self.limit=8

    @staticmethod
    def geometry_checks():return {'player_drones':8,'grid_spacing':minimum_distance(HOME)}

    def handle(self,label,now=None):
        if label in DIRECTIONS:
            if self.state in ('snake','scene_start') and not self.returning and self.queued_gesture!='palm':
                self.request('turn',direction=label)
            return
        if label in ('peace','three','ok') and self.state in ('snake','scene_start'):
            print('Hand Snake already running: point one finger and move your hand to steer.',flush=True)
            return
        super().handle(label,now)

    def keyboard_command(self,command):
        if command in DIRECTIONS:self.handle(command)
        elif command=='snake':self.start()
        elif command=='grid':self.handle('fist')
        elif command=='status':print(f'Hand Snake: state={self.state}; snake={self.members}/8; score={max(0,self.members-3)}',flush=True)
        else:print(self.MODE_DESCRIPTION+' Arm with a + Enter; enable webcam sending with E.',flush=True)


if __name__=='__main__':bridge.main(controller_type=PlayerController)
