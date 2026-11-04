"""Hand input updates only a future cell; current native motion stays committed."""
from simulation.runtime.snake_scene import SnakeRuntime
from simulation.scenes.play_snake import DRONES,HOME,DIRECTIONS,enter_plan,exit_plan,step_plan


def build(kind,start,scene,payload):
    plan=enter_plan(start) if kind=='start' else exit_plan(start) if kind=='return' else step_plan(scene,payload.get('direction'))
    exit=exit_plan(plan.after.states()) if plan.after is not None else None
    return plan,exit


class PlayerRuntime(SnakeRuntime):
    def __init__(self,server):
        super().__init__(server,DRONES,HOME,build)
        self.scene_limit=8
        self.direction=None;self.queued_scene=None

    def command(self,data):
        if data.get('action')=='turn':
            direction=data.get('direction')
            if direction not in DIRECTIONS:raise ValueError('Use left, right, up or down')
            if self.return_requested or not self.program:return
            if direction==self.direction:return
            self.direction=direction
            if self.pending and self.pending[2]=='step' and self.pending[1]-self.server.backend.time()>.65:
                future,when,*_=self.pending;future.cancel();self.pending=None
                self.submit('step',{},when,self.queued_scene)
            self.emit('direction',direction=direction)
            return
        if data.get('action')=='start':
            if data.get('limit')!=8:raise ValueError('Hand-controlled Snake uses exactly eight drones')
            self.direction=None
        return super().command(data)

    def submit(self,kind,payload,when=None,scene=None):
        if kind=='step':
            self.queued_scene=scene;payload=dict(payload,direction=self.direction)
        return super().submit(kind,payload,when,scene)

    def install(self,plan,start,exit_plan):
        if plan.kind=='grid' and not self.return_requested:
            self.return_requested=True
            self.emit('returning',reason='No clear forward path: returning to the airborne grid')
        super().install(plan,start,exit_plan)

    def clear(self):
        super().clear();self.direction=None;self.queued_scene=None
