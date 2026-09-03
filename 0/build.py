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
GIF_PX = 440          # longest side for GIF frames
FRAME_MS = 150        # time per GIF frame
PAUSE_MS = 700        # hold at the end of each take before reversing / moving on
# Each take is a (first, last) filename range (without extension). Each take plays
# forward, pauses, plays backward, pauses, then the next take starts.
# Set to None to treat every image in the dolly folder as one take.
DOLLY_RUNS = [
    ("IMG_5434", "IMG_5447"),
    ("IMG_5522", "IMG_5533"),
    ("IMG_5616", "IMG_5636"),
    ("IMG_5643", "IMG_5664"),
    ("IMG_5672", "IMG_5690"),
]

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
    all_src = sorted(
        p for p in DOLLY.iterdir()
        if p.suffix.lower() in IMG_EXT and not p.name.startswith(".")
    )
    if not all_src:
        print(f"  no images in {DOLLY} yet; skipping GIF")
        return
    runs = DOLLY_RUNS or [(all_src[0].stem, all_src[-1].stem)]
    cache = {}
    def frame(p):
        if p not in cache:
            im = load(p)
            im.thumbnail((GIF_PX, GIF_PX), Image.LANCZOS)
            cache[p] = im
        return cache[p]
    takes = []
    for a, b in runs:
        take = [frame(p) for p in all_src if a <= p.stem <= b]
        if take:
            takes.append(take)
    # make all frames the same size (crop to the smallest)
    w = min(f.size[0] for t in takes for f in t)
    h = min(f.size[1] for t in takes for f in t)
    seq, durs = [], []
    for take in takes:
        fwd = [ImageOps.fit(f, (w, h), Image.LANCZOS) for f in take]
        for f in fwd:                       # forward
            seq.append(f); durs.append(FRAME_MS)
        durs[-1] = PAUSE_MS                 # hold at far end
        for f in fwd[-2::-1]:               # backward
            seq.append(f); durs.append(FRAME_MS)
        durs[-1] = PAUSE_MS                 # hold at near end
    seq = [f.quantize(colors=96, method=Image.Quantize.MEDIANCUT) for f in seq]
    seq[0].save(
        GIF_OUT, save_all=True, append_images=seq[1:],
        duration=durs, loop=0, optimize=True,
    )
    n = sum(len(t) for t in takes)
    print(f"  wrote {GIF_OUT.name}: {len(takes)} takes, {n} stills, {len(seq)} frames, "
          f"{w}x{h}, {GIF_OUT.stat().st_size/1e6:.1f} MB")


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
