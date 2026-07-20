from pathlib import Path

from media_naming import DIRECTORY_PATTERNS

ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = ROOT / "media"
INDEX_HTML = ROOT / "public" / "index.html"
MAX_KB = 100
MAX_BYTES = MAX_KB * 1024
MIN_SUFFIX = "-min"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

MEDIA_DIRECTORY_PATTERNS = DIRECTORY_PATTERNS
