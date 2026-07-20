#!/usr/bin/env python3
"""Normalize media filenames per directory rules and sync public/index.html."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from media_config import INDEX_HTML, MEDIA_DIR, MEDIA_DIRECTORY_PATTERNS
from media_naming import audit_media_names, canonical_stem, folder_key
from media_unify import apply_path_rewrites, collect_unify_renames


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Organize media filenames using per-folder naming patterns."
    )
    parser.add_argument("--dry-run", action="store_true", help="Show renames without applying")
    parser.add_argument(
        "--list-rules",
        action="store_true",
        help="Print naming pattern per media/ subdirectory",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Show naming families per folder (why names may look mixed)",
    )
    return parser.parse_args()


def normalize_extension(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".jpeg":
        return ".jpg"
    return ext


def normalize_path(path: Path) -> Path | None:
    if path.name == ".DS_Store":
        return None
    ext = normalize_extension(path)
    if ext not in {".jpg", ".png", ".webp", ".gif"}:
        return None

    rel = path.relative_to(MEDIA_DIR)
    folder = folder_key(rel.parts)
    new_stem = canonical_stem(path.stem, folder)
    new_name = f"{new_stem}{ext}"
    if new_name == path.name:
        return None
    return path.with_name(new_name)


def same_file(a: Path, b: Path) -> bool:
    if a == b:
        return True
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


def safe_rename(src: Path, dest: Path) -> None:
    if same_file(src, dest):
        if src.name == dest.name:
            return
        tmp = dest.with_name(f".__rename_tmp_{dest.stem}{dest.suffix}")
        if tmp.exists():
            tmp.unlink()
        src.rename(tmp)
        tmp.rename(dest)
        return
    if dest.exists():
        raise FileExistsError(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dest)


def normalize_index_html() -> bool:
    if not INDEX_HTML.exists():
        return False
    text = INDEX_HTML.read_text(encoding="utf-8")
    updated = text
    updated = re.sub(r"(/media/[^\"']+)\.JPG", r"\1.jpg", updated)
    updated = re.sub(r"(/media/[^\"']+)\.JPEG", r"\1.jpg", updated)
    updated = updated.replace("-Edit.jpg", "-edit.jpg").replace("-Edit.JPG", "-edit.jpg")
    if updated != text:
        INDEX_HTML.write_text(updated, encoding="utf-8")
        return True
    return False


def print_audit() -> None:
    stats = audit_media_names()
    print("📊 สรุปชื่อไฟล์ตามโฟลเดอร์ (แต่ละแถว = รูปแบบชื่อที่อนุญาต)\n")
    for folder in sorted(stats):
        kinds = stats[folder]
        total = sum(kinds.values())
        labels = ", ".join(f"{k} ({n})" for k, n in sorted(kinds.items()))
        print(f"  media/{folder}/ — {total} ไฟล์")
        print(f"    {labels}\n")
    print(
        "หมายเหตุ: โฟลเดอร์ car/food/… ใช้ชื่อ slug อัตโนมัติ (car-00001.jpg)\n"
        "        behide/cinema/family ใช้ MTF/DSC ตามเดิม\n"
    )


def apply_renames(renames: list[tuple[Path, Path]], dry_run: bool, *, step: str = "") -> list[tuple[Path, Path]]:
    if not renames:
        return []

    applied: list[tuple[Path, Path]] = []
    for src, dest in renames:
        if dest.exists() and not same_file(src, dest):
            print(f"❌ ข้าม (มีไฟล์ปลายทางแล้ว): {src} -> {dest}", file=sys.stderr)
            continue
        rel = src.relative_to(MEDIA_DIR)
        folder = rel.parts[0] if rel.parts else "?"
        tag = step or MEDIA_DIRECTORY_PATTERNS.get(folder, "—")
        print(f"📝 [{folder}] {rel.name} -> {dest.name}  ({tag})")
        if not dry_run:
            try:
                safe_rename(src, dest)
                applied.append((src, dest))
            except OSError as exc:
                print(f"❌ ไม่สามารถเปลี่ยนชื่อ {src}: {exc}", file=sys.stderr)
                continue
        else:
            applied.append((src, dest))

    if not dry_run and applied:
        apply_path_rewrites(applied)
        if INDEX_HTML.exists():
            print(f"🔗 อัปเดต path ใน {INDEX_HTML.relative_to(MEDIA_DIR.parent)}")
    return applied


def collect_renames() -> list[tuple[Path, Path]]:
    renames: list[tuple[Path, Path]] = []
    if not MEDIA_DIR.is_dir():
        return renames
    for path in sorted(MEDIA_DIR.rglob("*")):
        if not path.is_file():
            continue
        dest = normalize_path(path)
        if dest is not None:
            renames.append((path, dest))
    return renames


def print_rules() -> None:
    print("📋 Pattern ชื่อไฟล์ตามโฟลเดอร์ (media/):\n")
    for folder in sorted(MEDIA_DIRECTORY_PATTERNS):
        print(f"  media/{folder}/")
        print(f"    → {MEDIA_DIRECTORY_PATTERNS[folder]}\n")


def main() -> int:
    args = parse_args()
    if args.audit:
        print_audit()
        return 0

    if args.list_rules:
        print_rules()
        return 0

    if not MEDIA_DIR.is_dir():
        print(f"❌ ไม่พบโฟลเดอร์ {MEDIA_DIR}", file=sys.stderr)
        return 1

    print("📂 จัดระเบียบชื่อไฟล์อัตโนมัติ\n")
    canonical = collect_renames()
    applied = apply_renames(canonical, args.dry_run, step="canonical")
    unify = collect_unify_renames(dry_run=args.dry_run)
    applied += apply_renames(unify, args.dry_run, step="slug")

    if not applied:
        print("✅ ชื่อไฟล์เรียบร้อยแล้ว")
    if not args.dry_run and normalize_index_html():
        print(f"🔗 อัปเดต path ใน {INDEX_HTML.relative_to(MEDIA_DIR.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
