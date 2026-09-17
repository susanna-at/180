#!/usr/bin/env python3
"""
Build script for Project 1.

Run from anywhere:  python3 1/build.py

What it does:
  Copies the colorized results from proj1/out/<folder>/ into 1/media/<folder>/,
  shrinking them to max 1200 px so the page stays fast.
"""
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is missing. Run:  python3 -m pip install pillow")

ROOT = Path(__file__).resolve().parent
MEDIA = ROOT / "media"
OUT = ROOT.parent / "proj1" / "out"

MAX_PX = 1200         # longest side for result images
# folders in proj1/out/ to publish (each becomes 1/media/<folder>/)
FOLDERS = ["single_scale", "pyramid"]


def copy_folder(name: str):
    src = OUT / name
    if not src.is_dir():
        print(f"  no {src} yet; skipping")
        return
    dst = MEDIA / name
    dst.mkdir(parents=True, exist_ok=True)
    for p in sorted(src.glob("*.jpg")):
        im = Image.open(p).convert("RGB")
        im.thumbnail((MAX_PX, MAX_PX), Image.LANCZOS)
        im.save(dst / p.name, "JPEG", quality=88, optimize=True)
        print(f"  {name}/{p.name} -> {im.size[0]}x{im.size[1]}")


if __name__ == "__main__":
    print("Copying results...")
    for folder in FOLDERS:
        copy_folder(folder)
    print("Done.")
