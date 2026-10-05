from PIL import Image, ImageDraw
from .rng import SeededRNG
from .grammar import crack_path, grow_branch

def rgba(rgb, a=255):
    return tuple(rgb) + (a,)

def new_canvas(w, h, transparent=True):
    return Image.new("RGBA", (w,h), (0,0,0,0) if transparent else (26,26,30,255))

def rect(img, xy, color):
    ImageDraw.Draw(img).rectangle(xy, fill=color)

def line(img, pts, color, width=1):
    ImageDraw.Draw(img).line(pts, fill=color, width=width)

def pixel(img, x, y, color):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x,y), color)

def jagged_vertical_face(img, x0, y0, w, h, rng, dark, mid, light):
    # Fill main face.
    rect(img, (x0,y0,x0+w-1,y0+h-1), mid)
    # Dark base stroke.
    rect(img, (x0,y0+h-2,x0+w-1,y0+h-1), dark)
    # Top-light edge.
    rect(img, (x0,y0,x0+w-1,y0), light)

    # Layering bands / cracks.
    for yy in range(y0+5, y0+h-3, 7):
        for xx in range(x0, x0+w):
            if rng.chance(0.55):
                pixel(img, xx, yy, dark)

    for _ in range(max(1,w//8)):
        sx = x0 + rng.randint(1,max(1,w-2))
        sy = y0 + rng.randint(2,max(2,h-6))
        for px,py in crack_path(max(w,h), rng, start=(sx-x0,sy-y0), length=rng.randint(4,8)):
            tx,ty=x0+px,y0+py
            if x0 <= tx < x0+w and y0 <= ty < y0+h:
                pixel(img,tx,ty,dark)

def timber_face(img, x0, y0, w, h, rng, dark, mid, light, iron, wax):
    rect(img,(x0,y0,x0+w-1,y0+h-1),mid)
    rect(img,(x0,y0,x0+w-1,y0),light)
    rect(img,(x0,y0+h-2,x0+w-1,y0+h-1),dark)

    # plank seams
    for xx in range(x0+7, x0+w, 8):
        for yy in range(y0,y0+h):
            if rng.chance(0.9):
                pixel(img,xx,yy,dark)

    # horizontal iron bindings
    for yy in (y0+10, y0+h-12):
        if y0 <= yy < y0+h:
            rect(img,(x0,yy,x0+w-1,min(y0+h-1,yy+1)),iron)

    # wood grain
    for _ in range(max(3,w//3)):
        x=x0+rng.randint(1,max(1,w-2))
        y=y0+rng.randint(2,max(2,h-4))
        length=rng.randint(2,5)
        for i in range(length):
            pixel(img,x,min(y0+h-3,y+i),dark)

    # sparse wax seals
    if rng.chance(0.7):
        wx=x0+rng.randint(2,max(2,w-3))
        wy=y0+rng.choice((11,max(11,h-12)))
        pixel(img,wx,wy,wax)
        if wx+1 < x0+w: pixel(img,wx+1,wy,wax)

def draw_rope(img, x0, y0, x1, y1, color):
    # dotted rope for low-res readability
    pts=[]
    steps=max(abs(x1-x0),abs(y1-y0),1)
    for i in range(steps+1):
        t=i/steps
        x=round(x0+(x1-x0)*t)
        y=round(y0+(y1-y0)*t)
        if i%2==0:
            pts.append((x,y))
    for x,y in pts:
        pixel(img,x,y,color)

def draw_paper(img, x, y, w, h, vellum, ink, wax=None):
    rect(img,(x,y,x+w-1,y+h-1),vellum)
    if h >= 3:
        for ix in range(x+1,x+w-1):
            if (ix-x)%2==0:
                pixel(img,ix,y+1,ink)
    if wax:
        pixel(img,x+w-1,y+h-1,wax)

def draw_skull_hint(img, cx, cy, bone, dark):
    # Tiny readable skull symbol, not detailed anatomy.
    rect(img,(cx-2,cy-2,cx+2,cy+1),bone)
    pixel(img,cx-1,cy,dark)
    pixel(img,cx+1,cy,dark)
    rect(img,(cx-1,cy+2,cx+1,cy+3),bone)

def draw_nanolith(img, x, y, w, h, silt, oil, glow):
    rect(img,(x,y,x+w-1,y+h-1),silt)
    # inner geometric traces
    for yy in range(y+3,y+h-2,5):
        for xx in range(x+2,x+w-2,4):
            if (xx+yy)%3==0:
                pixel(img,xx,yy,oil)
    # restrained center filament
    cx=x+w//2
    for yy in range(y+3,y+h-3):
        if yy%3 != 0:
            pixel(img,cx,yy,glow)

def draw_silt_creep(img, rng, x, y, w, h, deep, oil, glow, coverage=0.12):
    count=max(1,int(w*h*coverage))
    for _ in range(count):
        px=x+rng.randint(0,max(0,w-1))
        py=y+rng.randint(0,max(0,h-1))
        pixel(img,px,py,deep if rng.chance(0.75) else oil)
    # one short filament
    sx=x+rng.randint(0,max(0,w-1))
    sy=y+rng.randint(0,max(0,h-1))
    for _ in range(max(2,min(6,h//4))):
        pixel(img,sx,sy,glow)
        sy=min(y+h-1,sy+1)
        sx=max(x,min(x+w-1,sx+rng.choice((-1,0,1))))
