"""Generate branded NSIS installer bitmaps using the same app-logo data.
Run after the SVG exists and before the Tauri bundle build. Needs Pillow.
"""
from __future__ import annotations
import base64
from io import BytesIO
from pathlib import Path
import re
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1] / "frontend" / "src-tauri"
LOGO = ROOT / "icons" / "icon-source.svg"
OUT = ROOT / "installer"

def load_logo() -> Image.Image:
    raw = LOGO.read_text(encoding="utf-8")
    match = re.search(r"data:image/(?:png|webp);base64,([A-Za-z0-9+/=]+)", raw)
    if not match:
        raise RuntimeError("PACE logo data not embedded in icon-source.svg")
    return Image.open(BytesIO(base64.b64decode(match.group(1)))).convert("RGBA")

def build(size: tuple[int,int], name: str) -> None:
    w,h = size
    image = Image.new("RGB",size)
    px = image.load()
    for y in range(h):
        for x in range(w):
            v = x / w + y / h
            px[x,y] = (int(10 + v*11),int(10 + v*5),int(16 + v*19))
    draw=ImageDraw.Draw(image)
    draw.rectangle((0,0,5,h),fill=(125,63,191))
    mark=load_logo()
    extent=min(w-22,116 if h>200 else 44)
    mark.thumbnail((extent,extent),Image.Resampling.LANCZOS)
    image.paste(mark,((w-mark.width)//2+2,34 if h>200 else max(4,(h-mark.height)//2)),mark)
    if h>200:
        draw.text((24,168),"PACE",fill=(245,244,250))
        draw.text((24,190),"YOUR PERSONAL AI",fill=(0,222,245))
        draw.text((24,210),"WORKSPACE",fill=(0,222,245))
        draw.line((24,244,w-14,244),fill=(106,63,156),width=2)
        draw.text((24,260),"LOCAL / PRIVATE",fill=(194,185,209))
    OUT.mkdir(parents=True,exist_ok=True)
    image.save(OUT/name,"BMP")

if __name__=="__main__":
    build((164,314),"sidebar.bmp")
    build((150,57),"header.bmp")
    print("PACE installer art created")
