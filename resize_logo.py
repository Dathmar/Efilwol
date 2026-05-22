#!/usr/bin/env python3
"""
Generate resized logo variants from base/static/img/logo.png.
Preserves aspect ratio and alpha channel (RGBA).
"""
from pathlib import Path
from PIL import Image

SRC = Path('base/static/img/logo.png')
OUT = Path('base/static/img')

img = Image.open(SRC).convert('RGBA')
orig_w, orig_h = img.size
aspect = orig_w / orig_h

print(f"Source: {orig_w}x{orig_h}px  ({SRC.stat().st_size / 1024:.0f} KB)  mode={img.mode}")

variants = [
    # (filename,        target_height)
    ('logo-navbar.png',  48),   # navbar
    ('logo-sm.png',      96),   # small auth headers / footer
    ('logo-md.png',     192),   # medium — login/signup hero panels
    ('logo-lg.png',     384),   # large — splash / future use
    ('logo-web.png',    None),  # web-optimised, max 800px wide
]

for filename, target_h in variants:
    if target_h is None:
        max_w = 800
        new_w = min(orig_w, max_w)
        new_h = round(new_w / aspect)
    else:
        new_h = target_h
        new_w = round(target_h * aspect)

    resized = img.resize((new_w, new_h), Image.LANCZOS)
    out_path = OUT / filename
    resized.save(out_path, 'PNG', optimize=True)
    size_kb = out_path.stat().st_size / 1024
    print(f"  {filename:25s}  {new_w:4d}x{new_h:3d}px  {size_kb:.0f} KB")

print("Done.")
