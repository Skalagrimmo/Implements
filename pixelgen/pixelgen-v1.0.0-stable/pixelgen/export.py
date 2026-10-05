from pathlib import Path
from PIL import Image
from .constraints import require_int, MAX_PREVIEW_SCALE, MAX_ATLAS_COLUMNS


def ensure_dir(path):
    p=Path(path); p.mkdir(parents=True,exist_ok=True); return p


def save_numbered(images,out_dir,prefix):
    out=ensure_dir(out_dir); paths=[]
    for i,img in enumerate(images,1):
        path=out/f"{prefix}_{i:02d}.png"; img.save(path); paths.append(path)
    return paths


def collect_pngs(folder):
    p=Path(folder)
    if not p.is_dir():
        raise FileNotFoundError(f"folder not found: {p}")
    return sorted(x for x in p.glob("*.png") if x.name not in ("preview.png","atlas.png"))


def make_atlas(folder,out_path=None,columns=8,padding=0):
    columns=require_int("columns",columns,1,MAX_ATLAS_COLUMNS)
    padding=require_int("padding",padding,0,1024)
    files=collect_pngs(folder)
    if not files: raise ValueError(f"No PNG files found in {folder}")
    imgs=[]
    for p in files:
        with Image.open(p) as im: imgs.append(im.convert("RGBA").copy())
    tw=max(i.width for i in imgs); th=max(i.height for i in imgs)
    rows=(len(imgs)+columns-1)//columns
    atlas=Image.new("RGBA",(columns*tw+(columns-1)*padding,rows*th+(rows-1)*padding),(0,0,0,0))
    for idx,img in enumerate(imgs):
        x=(idx%columns)*(tw+padding); y=(idx//columns)*(th+padding)
        atlas.alpha_composite(img,(x,y))
    out_path=Path(out_path) if out_path else Path(folder)/"atlas.png"
    out_path.parent.mkdir(parents=True,exist_ok=True); atlas.save(out_path); return out_path


def make_preview(folder,out_path=None,scale=8,columns=8,gap=2):
    scale=require_int("scale",scale,1,MAX_PREVIEW_SCALE)
    columns=require_int("columns",columns,1,MAX_ATLAS_COLUMNS)
    gap=require_int("gap",gap,0,1024)
    files=collect_pngs(folder)
    if not files: raise ValueError(f"No PNG files found in {folder}")
    imgs=[]
    for p in files:
        with Image.open(p) as im: imgs.append(im.convert("RGBA").copy())
    sw=max(i.width for i in imgs)*scale; sh=max(i.height for i in imgs)*scale
    rows=(len(imgs)+columns-1)//columns; bg=(26,26,30,255)
    out=Image.new("RGBA",(columns*(sw+gap)+gap,rows*(sh+gap)+gap),bg)
    for idx,img in enumerate(imgs):
        img=img.resize((img.width*scale,img.height*scale),Image.Resampling.NEAREST)
        x=gap+(idx%columns)*(sw+gap); y=gap+(idx//columns)*(sh+gap)
        out.alpha_composite(img,(x,y))
    out_path=Path(out_path) if out_path else Path(folder)/"preview.png"
    out_path.parent.mkdir(parents=True,exist_ok=True); out.save(out_path); return out_path
