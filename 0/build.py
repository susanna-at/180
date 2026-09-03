#!/usr/bin/env python3
"""
Build script for Project 0.

Run from anywhere:  python3 0/build.py

What it does:
  1. Converts any .heic/.HEIC photos in 0/media/ and 0/media/dolly/ to .jpg
  2. Fixes EXIF rotation and shrinks big photos to max 1600 px (keeps the page fast)
  3. Builds 0/media/dolly_zoom.gif from every image in 0/media/dolly/ (sorted by filename)
"""
import subprocess, sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is missing. Run:  python3 -m pip install pillow")

ROOT = Path(__file__).resolve().parent
MEDIA = ROOT / "media"
DOLLY = MEDIA / "dolly"
GIF_OUT = MEDIA / "dolly_zoom.gif"

MAX_PHOTO_PX = 1600   # longest side for still photos
GIF_PX = 640          # longest side for GIF frames
FRAME_MS = 350        # time per GIF frame (short sequences)

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def convert_heic(folder: Path):
    for heic in sorted(folder.glob("*")):
        if heic.suffix.lower() != ".heic":
            continue
        jpg = heic.with_suffix(".jpg")
        if jpg.exists():
            continue
        print(f"  HEIC -> JPG: {heic.name}")
        r = subprocess.run(["magick", str(heic), "-auto-orient", "-quality", "92", str(jpg)])
        if r.returncode != 0:
            print(f"  !! could not convert {heic.name} (is ImageMagick installed?)")


def load(path: Path) -> Image.Image:
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    return im.convert("RGB")


def shrink_photos(folder: Path):
    for p in sorted(folder.iterdir()):
        if p.suffix.lower() not in IMG_EXT or p.name.startswith("."):
            continue
        im = load(p)
        if max(im.size) <= MAX_PHOTO_PX:
            continue
        im.thumbnail((MAX_PHOTO_PX, MAX_PHOTO_PX), Image.LANCZOS)
        im.save(p.with_suffix(".jpg"), "JPEG", quality=88, optimize=True)
        if p.suffix.lower() != ".jpg":
            p.unlink()
        print(f"  resized: {p.name} -> {im.size[0]}x{im.size[1]}")


def build_gif():
    frames_src = sorted(
        p for p in DOLLY.iterdir()
        if p.suffix.lower() in IMG_EXT and not p.name.startswith(".")
    )
    if not frames_src:
        print(f"  no images in {DOLLY} yet; skipping GIF")
        return
    frames = []
    for p in frames_src:
        im = load(p)
        im.thumbnail((GIF_PX, GIF_PX), Image.LANCZOS)
        frames.append(im)
    # make all frames the same size (crop to the smallest)
    w = min(f.size[0] for f in frames)
    h = min(f.size[1] for f in frames)
    frames = [ImageOps.fit(f, (w, h), Image.LANCZOS) for f in frames]
    n = len(frames)
    if n <= 12:
        # short sequence: play forward then backward so the loop is smooth
        seq = frames + frames[-2:0:-1]
        ms = FRAME_MS
    else:
        seq = frames
        ms = 100
    seq = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for f in seq]
    seq[0].save(
        GIF_OUT, save_all=True, append_images=seq[1:],
        duration=ms, loop=0, optimize=True,
    )
    print(f"  wrote {GIF_OUT.name}: {len(frames_src)} stills, {w}x{h}, "
          f"{GIF_OUT.stat().st_size/1e6:.1f} MB")


if __name__ == "__main__":
    print("Converting HEIC...")
    convert_heic(MEDIA)
    convert_heic(DOLLY)
    print("Shrinking photos for the web...")
    shrink_photos(MEDIA)
    shrink_photos(DOLLY)
    print("Building dolly zoom GIF...")
    build_gif()
    print("Done.")
