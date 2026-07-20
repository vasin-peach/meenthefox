"""Assign one sequential slug pattern per media subfolder (fully automatic)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from media_config import INDEX_HTML, MEDIA_DIR

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# Folders that already use one semantic pattern — only canonical cleanup, no slugs.
CANONICAL_ONLY = {"behide", "cinema", "family"}

# Folder → slug prefix for unified names: {prefix}-00001.jpg
UNIFY_SLUG: dict[str, str] = {
    "cars": "car",
    "foods": "food",
    "sports": "sport",
    "portrait": "portrait",
    "covers": "cover",
    "events": "event",
}

EXEMPT_NAMES = {"logo.png", ".DS_Store"}

MAP_PATH = Path(__file__).resolve().parent / "media-name-map.json"


def _is_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXT and path.name not in EXEMPT_NAMES


def _slug_pattern(prefix: str) -> re.Pattern[str]:
    return re.compile(rf"^{re.escape(prefix)}-(\d{{5}})\.(jpg|png)$", re.I)


def load_map() -> dict:
    if MAP_PATH.is_file():
        return json.loads(MAP_PATH.read_text(encoding="utf-8"))
    return {"folders": {}, "assignments": {}}


def save_map(data: dict) -> None:
    MAP_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _ext(path: Path) -> str:
    ext = path.suffix.lower()
    return ".jpg" if ext == ".jpeg" else ext


def collect_unify_renames(*, dry_run: bool = False) -> list[tuple[Path, Path]]:
    data = load_map()
    assignments: dict[str, str] = data.setdefault("assignments", {})
    renames: list[tuple[Path, Path]] = []

    map_dirty = False
    for folder, prefix in UNIFY_SLUG.items():
        dir_path = MEDIA_DIR / folder
        if not dir_path.is_dir():
            continue

        slug_re = _slug_pattern(prefix)
        files = sorted([p for p in dir_path.iterdir() if _is_image(p)], key=lambda p: p.name.lower())

        used_nums: set[int] = set()
        for p in files:
            m = slug_re.match(p.name)
            if m:
                used_nums.add(int(m.group(1)))

        def next_num() -> int:
            n = 1
            while n in used_nums:
                n += 1
            used_nums.add(n)
            return n

        for path in files:
            if slug_re.match(path.name):
                rel = f"{folder}/{path.name}"
                assignments.setdefault(rel, path.name)
                continue

            rel_old = f"{folder}/{path.name}"
            cached = assignments.get(rel_old)
            if cached:
                target_name = cached
            else:
                num = next_num()
                target_name = f"{prefix}-{num:05d}{_ext(path)}"
                assignments[rel_old] = target_name
                map_dirty = True

            dest = path.with_name(target_name)
            if path.name != dest.name:
                renames.append((path, dest))

    data["folders"] = {k: UNIFY_SLUG[k] for k in UNIFY_SLUG}
    if not dry_run and (renames or map_dirty):
        save_map(data)
    return renames


def apply_path_rewrites(renames: list[tuple[Path, Path]]) -> None:
    if not renames or not INDEX_HTML.is_file():
        return
    text = INDEX_HTML.read_text(encoding="utf-8")
    original = text
    for src, dest in renames:
        old_ref = f"/media/{src.relative_to(MEDIA_DIR).as_posix()}"
        new_ref = f"/media/{dest.relative_to(MEDIA_DIR).as_posix()}"
        text = text.replace(old_ref, new_ref)
        # Full URL in meta tags
        text = text.replace(
            f"meen-the-fox.pages.dev{old_ref}",
            f"meen-the-fox.pages.dev{new_ref}",
        )
    if text != original:
        INDEX_HTML.write_text(text, encoding="utf-8")
