from collections import deque
from heapq import heappush, heappop
from .placement import reserve

DIRS = ((1,0),(-1,0),(0,1),(0,-1))


def in_bounds(scene, x, y):
    return 0 <= x < scene["width"] and 0 <= y < scene["height"]


def is_walkable(scene, x, y):
    return in_bounds(scene, x, y) and scene["collision"][y][x] == "walk"


def reachable(scene, start):
    if not is_walkable(scene, *start):
        return set()
    q = deque([start])
    seen = {start}
    while q:
        x, y = q.popleft()
        for dx, dy in DIRS:
            n = (x+dx, y+dy)
            if n not in seen and is_walkable(scene, *n):
                seen.add(n)
                q.append(n)
    return seen


def _cell_cost(scene, x, y):
    c = scene["collision"][y][x]
    if c == "solid":
        return None
    if c == "hazard":
        return 6
    return 1


def least_cost_path(scene, start, goal):
    if not (in_bounds(scene,*start) and in_bounds(scene,*goal)):
        return None
    heap = [(0, start)]
    cost = {start: 0}
    prev = {}
    while heap:
        cur_cost, cur = heappop(heap)
        if cur == goal:
            break
        if cur_cost != cost.get(cur):
            continue
        x, y = cur
        for dx, dy in DIRS:
            nx, ny = x+dx, y+dy
            if not in_bounds(scene,nx,ny):
                continue
            step = _cell_cost(scene,nx,ny)
            if step is None and (nx,ny) != goal:
                continue
            step = 1 if step is None else step
            nc = cur_cost + step
            if nc < cost.get((nx,ny), 10**18):
                cost[(nx,ny)] = nc
                prev[(nx,ny)] = cur
                heappush(heap,(nc,(nx,ny)))
    if goal not in cost:
        return None
    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    path.reverse()
    return path


def carve_path(scene, path, reserve_cells=True):
    if not path:
        return []
    for x, y in path:
        scene["ground"][y][x] = "path"
        scene["overlay"][y][x] = None
        scene["collision"][y][x] = "walk"
    if reserve_cells:
        reserve(scene, path)
    return path


def ensure_route(scene, start, goal):
    if not in_bounds(scene,*start) or not in_bounds(scene,*goal):
        raise ValueError("route endpoint out of bounds")
    scene["collision"][start[1]][start[0]] = "walk"
    scene["collision"][goal[1]][goal[0]] = "walk"
    seen = reachable(scene,start)
    if goal in seen:
        reserve(scene,{start,goal})
        return []
    path = least_cost_path(scene,start,goal)
    if path is None:
        return None
    return carve_path(scene,path,True)


def exit_cell(scene, edge, coord):
    if edge == "N": return (coord,0)
    if edge == "S": return (coord,scene["height"]-1)
    if edge == "W": return (0,coord)
    if edge == "E": return (scene["width"]-1,coord)
    raise ValueError(f"unknown edge {edge}")
