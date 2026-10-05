from .rng import SeededRNG

def grow_branch(size, rng, start=None, length=8, bias=(0,1), branch_chance=0.18):
    """Return a set of wrapped pixel coordinates describing an organic branch/root."""
    if start is None:
        x, y = rng.randint(0, size-1), rng.randint(0, size-1)
    else:
        x, y = start
    points = []
    dirs = [(-1,0),(1,0),(0,-1),(0,1)]
    bx, by = bias
    for _ in range(max(1, length)):
        points.append((x % size, y % size))
        candidates = dirs[:]
        if bx:
            candidates += [(1 if bx > 0 else -1, 0)] * 2
        if by:
            candidates += [(0, 1 if by > 0 else -1)] * 2
        dx, dy = rng.choice(candidates)
        x = (x + dx) % size
        y = (y + dy) % size
        if rng.chance(branch_chance):
            points.append(((x + rng.choice((-1,1))) % size, y % size))
    return points

def crack_path(size, rng, start=None, length=7):
    """Sharper directional path for stone/ice cracks."""
    if start is None:
        x, y = rng.randint(1, size-2), rng.randint(1, size-2)
    else:
        x, y = start
    points = []
    dx, dy = rng.choice(((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1)))
    for i in range(max(1, length)):
        if 0 <= x < size and 0 <= y < size:
            points.append((x,y))
        if rng.chance(0.28):
            dx += rng.choice((-1,0,1))
            dy += rng.choice((-1,0,1))
            dx = max(-1, min(1, dx))
            dy = max(-1, min(1, dy))
            if dx == 0 and dy == 0:
                dx = 1
        x += dx
        y += dy
    return points

def cluster(size, rng, count=6, radius=2):
    """Small local organic cluster, useful for moss/paper/debris."""
    cx, cy = rng.randint(0,size-1), rng.randint(0,size-1)
    pts = set()
    for _ in range(max(1,count)):
        x = (cx + rng.randint(-radius,radius)) % size
        y = (cy + rng.randint(-radius,radius)) % size
        pts.add((x,y))
    return list(pts)

def hex_fragment(size, rng):
    """Tiny incomplete hex-like machine geometry fragment."""
    x = rng.randint(2, max(2,size-5))
    y = rng.randint(2, max(2,size-4))
    pts = [(x,y),(x+2,y),(x+3,y+1),(x+2,y+2),(x,y+2),(x-1,y+1)]
    # randomly remove a couple pixels so it reads as buried/subtle geometry
    return [p for p in pts if rng.chance(0.78) and 0 <= p[0] < size and 0 <= p[1] < size]
