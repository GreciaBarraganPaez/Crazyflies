"""Seeded winding grid cycles built by joining loops along a maze tree."""
from functools import lru_cache
import random


@lru_cache(maxsize=64)
def winding_cycle(width,height,seed,offset=0):
    if width%2 or height%2:raise ValueError('Maze dimensions must be even')
    graph={}
    def link(a,b):
        graph.setdefault(a,set()).add(b);graph.setdefault(b,set()).add(a)
    def unlink(a,b):graph[a].remove(b);graph[b].remove(a)
    for y in range(0,height,2):
        for x in range(0,width,2):
            cells=((x,y),(x+1,y),(x+1,y+1),(x,y+1))
            for a,b in zip(cells,cells[1:]+cells[:1]):link(a,b)
    rng=random.Random(seed);seen={(0,0)};stack=[(0,0)]
    while stack:
        branch=rng.randrange(len(stack));x,y=stack[branch]
        neighbors=[(a,b) for a,b in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))
                   if 0<=a<width//2 and 0<=b<height//2 and (a,b) not in seen]
        if not neighbors:stack.pop(branch);continue
        a,b=rng.choice(neighbors);seen.add((a,b));stack.append((a,b))
        if a!=x:
            edge=2*min(a,x)+1;row=2*y
            p,q,r,s=(edge,row),(edge,row+1),(edge+1,row),(edge+1,row+1)
        else:
            edge=2*min(b,y)+1;col=2*x
            p,q,r,s=(col,edge),(col+1,edge),(col,edge+1),(col+1,edge+1)
        unlink(p,q);unlink(r,s);link(p,r);link(q,s)
    result=[(0,0)];previous=None;current=result[0]
    while True:
        following=next(p for p in sorted(graph[current]) if p!=previous)
        if following==result[0]:break
        result.append(following);previous,current=current,following
    if len(result)!=width*height:raise ValueError('Maze did not produce a single cycle')
    return tuple((x+offset,y) for x,y in result)
