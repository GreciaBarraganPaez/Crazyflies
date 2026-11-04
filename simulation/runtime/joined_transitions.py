"""Joined-transition protocol and queued input, separate from flight lifecycle."""
import json
import math
from collections import deque
from simulation.core.formation_registry import FORMATIONS
from simulation.core.static_shapes import targets


class JoinedTransitions:
    def __init__(self,flight):
        self.flight=flight
        self.target=None
        self.queued=None
        self.origin=None
        self.events=deque()

    def begin(self,target):
        c=self.flight;p=c.playback
        self.origin=(c.shape,p.running,p.started,c.current_goals)
        self.target=target
        self.queued=None
        self.events.clear()
        c.state='blending'
        p.running=False
        p.stop_request=None
        c.swarm.allcfs.startTrajectory(FORMATIONS[target].blend_id,relative=False)
        print(f'JOINED TRANSITION: {c.shape} -> {target}; outgoing motion continues until the scheduled join.',flush=True)

    def queue(self,label):
        if self.queued!='palm':self.queued=label

    def receive(self,message):
        try:event=json.loads(message.data)
        except (ValueError,TypeError):return
        if not isinstance(event,dict) or event.get('target')!=self.target:return
        if event.get('state') not in ('planning','started','completed','rejected'):return
        if event['state']=='completed':
            until=event.get('until')
            if not isinstance(until,(int,float)) or not math.isfinite(until):return
        self.events.append(event)

    def update(self,now):
        c=self.flight;p=c.playback
        while self.events:
            event=self.events.popleft()
            if event['state']=='started':
                print(f"Joined trajectory running: {event.get('lanes')} depth lanes; "
                      f"certified center-distance bound {event.get('clearance_bound',0):.3f}m.",flush=True)
            elif event['state'] in ('completed','rejected'):
                queued,self.queued=self.queued,None
                c.state='showing'
                if event['state']=='completed':
                    c.shape=event['target']
                    c.current_goals=targets(c.shape)
                    p.running=True
                    p.started=event['until']-c.period(c.shape)
                    print(f'Joined {c.shape}; playback continues without a waypoint hover.',flush=True)
                else:
                    c.demo.stop()
                    c.shape,p.running,p.started,c.current_goals=self.origin
                    print('Blend refused; outgoing formation retained: '+str(event.get('reason')),flush=True)
                self.target=self.origin=None
                if queued:c.handle(queued,now)
                return
