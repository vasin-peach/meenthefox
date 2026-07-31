#!/usr/bin/env python3
"""Download thumbnails for external video links (Facebook reels, etc.)."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THUMBS_DIR = ROOT / "media" / "video-thumbs"
INDEX_HTML = ROOT / "public" / "index.html"

REEL_ID_RE = re.compile(r"facebook\.com/reel/(\d+)")


def find_yt_dlp() -> str:
    for candidate in (
        shutil.which("yt-dlp"),
        str(Path.home() / "Library/Python/3.9/bin/yt-dlp"),
        str(Path.home() / "Library/Python/3.10/bin/yt-dlp"),
        str(Path.home() / "Library/Python/3.11/bin/yt-dlp"),
        str(Path.home() / "Library/Python/3.12/bin/yt-dlp"),
    ):
        if candidate and Path(candidate).is_file():
            return candidate
    raise RuntimeError("yt-dlp not found — run: python3 -m pip install yt-dlp")


def thumb_filename(reel_id: str) -> str:
    return f"facebook-{reel_id}.jpg"


def fetch_reel_thumbnail(reel_url: str, yt_dlp: str, *, force: bool = False) -> Path | None:
    match = REEL_ID_RE.search(reel_url)
    if not match:
        print(f"skip (not a reel URL): {reel_url}", file=sys.stderr)
        return None

    reel_id = match.group(1)
    dest = THUMBS_DIR / thumb_filename(reel_id)
    if dest.exists() and not force:
        print(f"exists: {dest.name}")
        return dest

    print(f"fetch: {reel_id}")
    tmp_base = THUMBS_DIR / f".tmp-{reel_id}"
    for stale in THUMBS_DIR.glob(f".tmp-{reel_id}*"):
        stale.unlink(missing_ok=True)

    result = subprocess.run(
        [
            yt_dlp,
            "--write-thumbnail",
            "--convert-thumbnails",
            "jpg",
            "--skip-download",
            "-o",
            str(tmp_base),
            reel_url,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip().splitlines()
        print(f"  error: {err[-1] if err else 'unknown'}", file=sys.stderr)
        for stale in THUMBS_DIR.glob(f".tmp-{reel_id}*"):
            stale.unlink(missing_ok=True)
        return None

    downloaded = next(THUMBS_DIR.glob(f".tmp-{reel_id}*.jpg"), None)
    if not downloaded:
        print(f"  no thumbnail file for {reel_id}", file=sys.stderr)
        return None

    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    downloaded.replace(dest)
    print(f"  saved {dest.name} ({dest.stat().st_size // 1024} KB)")
    return dest


def dental_reel_urls_from_index() -> list[str]:
    text = INDEX_HTML.read_text(encoding="utf-8")
    return re.findall(r'category:\s*"dental"[\s\S]*?url:\s*"([^"]+)"', text)


def add_thumbnails_to_index() -> int:
    text = INDEX_HTML.read_text(encoding="utf-8")
    updated = 0

    def replacer(match: re.Match[str]) -> str:
        nonlocal updated
        block = match.group(0)
        if "thumbnail:" in block:
            return block
        url_match = re.search(r'url:\s*"(https://www\.facebook\.com/reel/(\d+))"', block)
        if not url_match:
            return block
        reel_id = url_match.group(2)
        thumb_line = f'\n          thumbnail: "/media/video-thumbs/facebook-{reel_id}.jpg",'
        updated += 1
        return block.replace(
            f'url: "{url_match.group(1)}",',
            f'url: "{url_match.group(1)}",{thumb_line}',
        )

    new_text = re.sub(
        r'\{\s*category:\s*"dental"[\s\S]*?externalOnly:\s*true,\s*\}',
        replacer,
        text,
    )
    if updated:
        INDEX_HTML.write_text(new_text, encoding="utf-8")
    return updated


def main() -> int:
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    urls = args or dental_reel_urls_from_index()

    if not urls:
        print("no URLs to fetch", file=sys.stderr)
        return 1

    yt_dlp = find_yt_dlp()
    ok = 0
    for i, url in enumerate(urls):
        if i:
            time.sleep(1.2)
        if fetch_reel_thumbnail(url, yt_dlp, force=force):
            ok += 1

    updated = add_thumbnails_to_index()
    print(f"\n{ok}/{len(urls)} thumbnails saved; {updated} entries updated in index.html")
    return 0 if ok == len(urls) else 1


if __name__ == "__main__":
    raise SystemExit(main())
