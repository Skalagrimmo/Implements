def neighbors4(x, y, w, h):
    for dx, dy in ((1,0), (-1,0), (0,1), (0,-1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h:
            yield nx, ny

def blob_mask(width, height, rng, fill=0.32, steps=3):
    mask = [[rng.random() < fill for _ in range(width)] for _ in range(height)]
    for _ in range(steps):
        nxt = [[False] * width for _ in range(height)]
        for y in range(height):
            for x in range(width):
                score = sum(1 for nx, ny in neighbors4(x, y, width, height) if mask[ny][nx])
                if mask[y][x]:
                    nxt[y][x] = score >= 1 or rng.chance(0.25)
                else:
                    nxt[y][x] = score >= 3
        mask = nxt
    return mask

def toroidal_distance(a, b, size):
    d = abs(a - b)
    return min(d, size - d)

def wrap_line_points(x0, y0, x1, y1, size):
    # Simple Bresenham on local coords; callers can modulo-wrap.
    points = []
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        points.append((x % size, y % size))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy
    return points
