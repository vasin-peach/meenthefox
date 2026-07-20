#!/usr/bin/env python3
"""Resize and compress images to a target max file size (default 100 KB)."""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from PIL import Image, ImageOps

from media_config import IMAGE_EXTENSIONS, MAX_KB, MEDIA_DIR

MIN_QUALITY = 20
MAX_QUALITY = 92
MIN_DIMENSION = 320


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resize and compress images so each output file is at most MAX_KB."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=[str(MEDIA_DIR)],
        help="Files or directories (default: media)",
    )
    parser.add_argument(
        "--max-kb",
        type=int,
        default=MAX_KB,
        help=f"Maximum output size in kilobytes (default: {MAX_KB})",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=1920,
        help="Starting max width/height in pixels (default: 1920)",
    )
    parser.add_argument(
        "--suffix",
        default="",
        help='Output suffix before extension. Empty with --replace overwrites in place.',
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Overwrite the input file instead of writing a suffixed copy",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recompress even if already under the size limit (default: skip OK files)",
    )
    return parser.parse_args()


def collect_images(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    exts = {e.lower() for e in IMAGE_EXTENSIONS} | IMAGE_EXTENSIONS
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            print(f"⚠️  Skip (not found): {path}", file=sys.stderr)
            continue
        if path.is_file():
            if path.suffix.lower() in {e.lower() for e in IMAGE_EXTENSIONS}:
                files.append(path)
            continue
        for p in sorted(path.rglob("*")):
            if p.is_file() and p.suffix.lower() in {e.lower() for e in IMAGE_EXTENSIONS}:
                if p.name != ".DS_Store":
                    files.append(p)
    return files


def flatten_rgba(img: Image.Image, background: tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        base = Image.new("RGB", img.size, background)
        converted = img.convert("RGBA")
        base.paste(converted, mask=converted.split()[-1])
        return base
    return img.convert("RGB")


def encode_jpeg(img: Image.Image, quality: int) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", optimize=True, quality=quality, progressive=True)
    return buf.getvalue()


def compress_png(img: Image.Image, max_bytes: int) -> bytes | None:
    working = ImageOps.exif_transpose(img)
    for compress_level in (9, 6, 3):
        buf = io.BytesIO()
        working.save(buf, format="PNG", optimize=True, compress_level=compress_level)
        if buf.tell() <= max_bytes:
            return buf.getvalue()
    w, h = working.size
    side = max(w, h)
    while side >= MIN_DIMENSION:
        if max(w, h) > side:
            scale = side / max(w, h)
            resized = working.resize(
                (max(1, int(w * scale)), max(1, int(h * scale))),
                Image.Resampling.LANCZOS,
            )
        else:
            resized = working
        buf = io.BytesIO()
        resized.save(buf, format="PNG", optimize=True, compress_level=9)
        if buf.tell() <= max_bytes:
            return buf.getvalue()
        side = int(side * 0.85)
    return None


def compress_to_target(img: Image.Image, max_bytes: int, start_max_side: int) -> tuple[bytes, int, int]:
    working = ImageOps.exif_transpose(img)
    working = flatten_rgba(working)

    max_side = start_max_side
    best: bytes | None = None
    best_q = MIN_QUALITY
    best_side = max_side

    while max_side >= MIN_DIMENSION:
        w, h = working.size
        if max(w, h) > max_side:
            scale = max_side / max(w, h)
            new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
            resized = working.resize(new_size, Image.Resampling.LANCZOS)
        else:
            resized = working

        lo, hi = MIN_QUALITY, MAX_QUALITY
        candidate: bytes | None = None
        candidate_q = lo

        while lo <= hi:
            mid = (lo + hi) // 2
            data = encode_jpeg(resized, mid)
            if len(data) <= max_bytes:
                candidate = data
                candidate_q = mid
                lo = mid + 1
            else:
                hi = mid - 1

        if candidate is not None:
            best = candidate
            best_q = candidate_q
            best_side = max_side
            break

        max_side = int(max_side * 0.85)

    if best is None:
        tiny = working.copy()
        if max(tiny.size) > MIN_DIMENSION:
            scale = MIN_DIMENSION / max(tiny.size)
            tiny = tiny.resize(
                (max(1, int(tiny.width * scale)), max(1, int(tiny.height * scale))),
                Image.Resampling.LANCZOS,
            )
        best = encode_jpeg(tiny, MIN_QUALITY)
        best_q = MIN_QUALITY
        best_side = max(tiny.size)

    return best, best_q, best_side


def output_path(src: Path, suffix: str, replace: bool) -> Path:
    if replace:
        if src.suffix.lower() in (".png", ".webp", ".gif") and suffix == "":
            return src
        if src.suffix.lower() in (".png", ".webp", ".gif"):
            return src.with_suffix(".jpg")
        return src
    stem = src.stem
    if suffix and stem.endswith(suffix):
        return src
    out_name = f"{stem}{suffix}.jpg" if suffix else f"{stem}.jpg"
    return src.with_name(out_name)


def process_file(
    src: Path,
    max_bytes: int,
    start_max_side: int,
    suffix: str,
    replace: bool,
    dry_run: bool,
    force: bool,
) -> bool:
    if src.suffix.lower() == ".png":
        size = src.stat().st_size
        if not force and size <= max_bytes:
            print(f"⏭️  OK (PNG): {src.name} ({size // 1024} KB)")
            return True
        try:
            with Image.open(src) as img:
                data = compress_png(img, max_bytes)
        except OSError as exc:
            print(f"❌ Failed to read {src}: {exc}", file=sys.stderr)
            return False
        if data is None:
            print(f"❌ PNG still too large: {src}", file=sys.stderr)
            return False
        if dry_run:
            print(f"🔍 PNG: {src} ({len(data) / 1024:.1f} KB)")
            return True
        src.write_bytes(data)
        print(f"✅ PNG {src.name} ({len(data) / 1024:.1f} KB)")
        return True

    dest = output_path(src, suffix, replace)
    if not force:
        check = src if replace else (dest if dest.exists() else src)
        if check.exists() and check.stat().st_size <= max_bytes:
            print(f"⏭️  OK: {check.name} ({check.stat().st_size // 1024} KB)")
            return True

    try:
        with Image.open(src) as img:
            data, quality, side = compress_to_target(img, max_bytes, start_max_side)
    except OSError as exc:
        print(f"❌ Failed to read {src}: {exc}", file=sys.stderr)
        return False

    size_kb = len(data) / 1024
    ok = len(data) <= max_bytes

    if dry_run:
        print(f"🔍 {src} -> {dest} ({size_kb:.1f} KB, q={quality})")
        return ok

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    if replace and dest != src and src.exists():
        src.unlink()

    if ok:
        print(f"✅ {src.name} -> {dest.name} ({size_kb:.1f} KB, q={quality})")
    else:
        print(f"⚠️  {src.name} ({size_kb:.1f} KB, over limit)", file=sys.stderr)
    return ok


def main() -> int:
    args = parse_args()
    max_bytes = args.max_kb * 1024
    images = collect_images(args.paths)

    if not images:
        print("No images found.", file=sys.stderr)
        return 1

    print(f"🖼️  บีบอัด {len(images)} รูป — เป้าหมาย ≤ {args.max_kb} KB\n")

    ok_count = 0
    fail_count = 0
    for src in images:
        if process_file(
            src,
            max_bytes,
            args.max_width,
            args.suffix,
            args.replace,
            args.dry_run,
            args.force,
        ):
            ok_count += 1
        else:
            fail_count += 1

    print(f"\nเสร็จ: {ok_count} สำเร็จ, {fail_count} ล้มเหลว")
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
