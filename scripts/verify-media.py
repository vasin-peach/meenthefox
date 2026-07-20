#!/usr/bin/env python3
"""Fail if any image under media/ exceeds the size limit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from media_config import IMAGE_EXTENSIONS, MAX_KB, MEDIA_DIR, max_bytes_for_media_path, max_kb_for_media_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify all media images are under the size cap.")
    parser.add_argument(
        "paths",
        nargs="*",
        default=[str(MEDIA_DIR)],
        help="Files or directories to check (default: media)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="No output when all files pass",
    )
    return parser.parse_args()


def collect_images(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if not path.exists():
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


def main() -> int:
    args = parse_args()
    targets = collect_images(args.paths)
    if not targets:
        print(f"❌ ไม่พบรูปที่ตรวจ", file=sys.stderr)
        return 1

    too_large: list[tuple[Path, int, int]] = []
    for path in targets:
        size = path.stat().st_size
        limit_bytes = max_bytes_for_media_path(path)
        if size > limit_bytes:
            too_large.append((path, size, max_kb_for_media_path(path)))

    if not too_large:
        if not args.quiet:
            print(f"✅ รูปทั้งหมดผ่านเพดานขนาด ({len(targets)} ไฟล์, default ≤ {MAX_KB} KB)")
        return 0

    print(f"❌ มีรูป {len(too_large)} ไฟล์ที่ใหญ่เกินเพดาน:\n", file=sys.stderr)
    for path, size, limit_kb in too_large[:30]:
        try:
            rel = path.relative_to(MEDIA_DIR.parent)
        except ValueError:
            rel = path
        print(f"   • {rel} ({size / 1024:.1f} KB, ต้อง ≤ {limit_kb} KB)", file=sys.stderr)
    if len(too_large) > 30:
        print(f"   … และอีก {len(too_large) - 30} ไฟล์", file=sys.stderr)
    print("\n💡 รัน: pnpm run media", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
