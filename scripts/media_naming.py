"""Per-directory canonical filename rules for media/."""

from __future__ import annotations

import re
import unicodedata

MIN_SUFFIX = "-min"

THAI_REPLACEMENTS = {"แก้ไข": "edit"}

# Human-readable patterns for docs / rules (must match logic below)
DIRECTORY_PATTERNS: dict[str, str] = {
    "behide": "MTF#####-min.jpg",
    "cinema": "MTF#####.jpg",
    "family": "DSC#####.jpg",
    "portrait": "portrait-#####.jpg",
    "sports": "sport-#####.jpg",
    "foods": "food-#####.jpg",
    "events": "event-#####.jpg",
    "covers": "logo.png | cover-#####.jpg",
    "cars": "car-#####.jpg",
}


def base_cleanup(stem: str) -> str:
    name = unicodedata.normalize("NFKC", stem)
    for thai, repl in THAI_REPLACEMENTS.items():
        name = name.replace(thai, repl)
    name = name.replace("}", "").replace("{", "")
    name = re.sub(r"\s+", "-", name.strip())
    name = re.sub(r"-+", "-", name)
    name = re.sub(r"(?i)-edit", "-edit", name)
    return name


def _mtf(n: int, suffix: str = "") -> str:
    return f"MTF{n:05d}{suffix}"


def _dsc5(n: int, suffix: str = "") -> str:
    return f"DSC{n:05d}{suffix}"


def _has_edit(stem: str) -> bool:
    return bool(re.search(r"(?i)-edit", stem))


def _behide(stem: str) -> str:
    m = re.match(r"(?i)MTF(\d+)", stem)
    if m:
        return _mtf(int(m.group(1)), MIN_SUFFIX)
    return stem


def _cinema(stem: str) -> str:
    m = re.match(r"(?i)MTF(\d+)", stem)
    if m:
        return _mtf(int(m.group(1)))
    return stem


def _portrait(stem: str) -> str:
    m = re.match(r"(?i)MTF(\d+)", stem)
    if m:
        n = int(m.group(1))
        return _mtf(n, "-edit") if _has_edit(stem) else _mtf(n)
    m = re.match(r"(?i)DSC_?(\d+)", stem)
    if m:
        return _dsc5(int(m.group(1)))
    return stem


def _family(stem: str) -> str:
    m = re.match(r"(?i)DSC_?(\d+)", stem)
    if m:
        suffix = "-edit" if _has_edit(stem) else ""
        return _dsc5(int(m.group(1)), suffix)
    return stem


def _sports(stem: str) -> str:
    m = re.match(r"(?i)IMG_(\d{8})_(\d{6})(_\d+)?", stem)
    if m:
        extra = m.group(3) or ""
        return f"IMG_{m.group(1)}_{m.group(2)}{extra}".upper()
    m = re.match(r"(?i)DSC_?(\d+)", stem)
    if m:
        suffix = "-edit" if _has_edit(stem) else ""
        return _dsc5(int(m.group(1)), suffix)
    return stem


def _foods(stem: str) -> str:
    if re.match(r"(?i)^ALL_POST$", stem):
        return "ALL_POST"
    m = re.match(r"(?i)DSC_?(\d+)(-\d+)?", stem)
    if m:
        base = _dsc5(int(m.group(1)))
        return f"{base}{m.group(2)}" if m.group(2) else base
    m = re.match(r"(?i)IMG_(\d+)", stem)
    if m:
        suffix = "-edit" if _has_edit(stem) else ""
        return f"IMG_{m.group(1)}{suffix}"
    if re.match(r"^[A-Z0-9]+$", stem, re.I):
        return stem.upper()
    return stem


def _events(stem: str) -> str:
    m = re.match(r"(?i)DSC_?(\d+)", stem)
    if m:
        return f"DSC_{int(m.group(1)):04d}"
    return stem


def _covers(stem: str) -> str:
    if stem.lower() == "logo":
        return "logo"
    m = re.match(r"(?i)MTF(\d+)", stem)
    if m:
        return _mtf(int(m.group(1)))
    m = re.match(r"(?i)IMG_(\d{8})_(\d{6})", stem)
    if m:
        return f"IMG_{m.group(1)}_{m.group(2)}"
    return stem


def _cars(stem: str) -> str:
    if re.match(r"(?i)^M2_G87$", stem):
        return "M2_G87"
    m = re.match(r"(?i)BHS(\d+)", stem)
    if m:
        return f"BHS{int(m.group(1)):05d}"
    m = re.match(r"(?i)BMW-i4M50-(\d+)", stem)
    if m:
        return f"BMW-i4M50-{int(m.group(1)):02d}"
    m = re.match(r"(?i)CF_(\d+)", stem)
    if m:
        return f"CF_{int(m.group(1)):03d}"
    m = re.match(r"(?i)DSC_?(\d+)", stem)
    if m:
        return _dsc5(int(m.group(1)))
    m = re.match(r"(?i)MTF(\d+)", stem)
    if m:
        n = int(m.group(1))
        return _mtf(n, "-edit") if _has_edit(stem) else _mtf(n)
    return stem


_HANDLERS = {
    "behide": _behide,
    "cinema": _cinema,
    "portrait": _portrait,
    "family": _family,
    "sports": _sports,
    "foods": _foods,
    "events": _events,
    "covers": _covers,
    "cars": _cars,
}


def folder_key(relative_parts: tuple[str, ...]) -> str | None:
    if not relative_parts:
        return None
    top = relative_parts[0]
    return top if top in _HANDLERS else None


def canonical_stem(stem: str, folder: str | None) -> str:
    cleaned = base_cleanup(stem)
    if not folder:
        return cleaned
    handler = _HANDLERS.get(folder)
    if not handler:
        return cleaned
    return handler(cleaned)


def stem_kind(stem: str, folder: str | None) -> str:
    """Label which naming family a stem belongs to (for audit)."""
    if not folder:
        return "unknown"
    s = base_cleanup(stem)
    checks: list[tuple[str, str]] = []
    if folder == "behide":
        checks = [(r"(?i)^MTF\d{5}-min$", "MTF#####-min")]
    elif folder == "cinema":
        checks = [(r"(?i)^MTF\d{5}$", "MTF#####")]
    elif folder == "family":
        checks = [(r"(?i)^DSC\d{5}(-edit)?$", "DSC#####")]
    elif folder == "events":
        checks = [(r"(?i)^event-\d{5}$", "event-#####")]
    elif folder == "cars":
        checks = [(r"(?i)^car-\d{5}$", "car-#####")]
    elif folder == "foods":
        checks = [(r"(?i)^food-\d{5}$", "food-#####")]
    elif folder == "sports":
        checks = [(r"(?i)^sport-\d{5}$", "sport-#####")]
    elif folder == "portrait":
        checks = [(r"(?i)^portrait-\d{5}$", "portrait-#####")]
    elif folder == "covers":
        checks = [
            (r"(?i)^logo$", "logo"),
            (r"(?i)^cover-\d{5}$", "cover-#####"),
        ]
    for pattern, label in checks:
        if re.match(pattern, s):
            return label
    return "non-standard"


def audit_media_names() -> dict[str, dict[str, int]]:
    """Count naming families per folder."""
    from media_config import MEDIA_DIR

    stats: dict[str, dict[str, int]] = {}
    if not MEDIA_DIR.is_dir():
        return stats
    for path in sorted(MEDIA_DIR.rglob("*")):
        if not path.is_file() or path.name == ".DS_Store":
            continue
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            continue
        rel = path.relative_to(MEDIA_DIR)
        folder = folder_key(rel.parts) or "_root"
        kind = stem_kind(path.stem, folder if folder != "_root" else None)
        stats.setdefault(folder, {})
        stats[folder][kind] = stats[folder].get(kind, 0) + 1
    return stats

