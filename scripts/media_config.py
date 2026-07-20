from pathlib import Path

from media_naming import DIRECTORY_PATTERNS

ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = ROOT / "media"
INDEX_HTML = ROOT / "public" / "index.html"
MAX_KB = 100
MAX_BYTES = MAX_KB * 1024
# โฟลเดอร์ที่ต้องการเพดานใหญ่กว่า default (เช่น ปก/hero)
MAX_KB_BY_FOLDER: dict[str, int] = {
    "covers": 500,
}
MIN_SUFFIX = "-min"


def max_kb_for_media_path(path: Path) -> int:
    try:
        rel = path.resolve().relative_to(MEDIA_DIR.resolve())
        if rel.parts:
            return MAX_KB_BY_FOLDER.get(rel.parts[0], MAX_KB)
    except ValueError:
        pass
    return MAX_KB


def max_bytes_for_media_path(path: Path) -> int:
    return max_kb_for_media_path(path) * 1024

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

MEDIA_DIRECTORY_PATTERNS = DIRECTORY_PATTERNS
