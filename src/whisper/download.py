#!/usr/bin/env python3
"""Simple downloader for Whisper GGUF/bin models with a CLI progress bar.

Usage examples:
  python src\whisper\download.py
  python src\whisper\download.py --url https://huggingface.co/ggerganov/whisper.cpp/resolve/main/models/ggml-base.en.bin
  python src\whisper\download.py --out-dir models --filename ggml-base.bin

The script uses only the Python standard library.
"""

from __future__ import annotations
import argparse
import sys
import time
import urllib.request
from pathlib import Path

DEFAULT_URL = (
    "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin"
)

CHUNK_SIZE = 64 * 1024


def human_bytes(n: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024.0:
            return f"{n:.2f} {unit}"
        n /= 1024.0
    return f"{n:.2f} TiB"


def download_with_progress(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp = dest.with_suffix(dest.suffix + ".part")

    req = urllib.request.Request(url, headers={"User-Agent": "python-urllib/3"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        total_header = resp.getheader("Content-Length")
        total = int(total_header) if total_header and total_header.isdigit() else None

        downloaded = 0
        start = time.time()
        with open(temp, "wb") as fh:
            while True:
                chunk = resp.read(CHUNK_SIZE)
                if not chunk:
                    break
                fh.write(chunk)
                downloaded += len(chunk)

                elapsed = max(1e-6, time.time() - start)
                speed = downloaded / elapsed
                if total:
                    pct = downloaded / total * 100
                    eta = (total - downloaded) / speed if speed > 0 else 0
                    sys.stdout.write(
                        f"\r{downloaded}/{total} bytes ({pct:5.1f}%) "
                        f"{human_bytes(int(speed))}/s ETA {int(eta)}s"
                    )
                else:
                    sys.stdout.write(f"\r{human_bytes(downloaded)} downloaded ({human_bytes(int(speed))}/s)")
                sys.stdout.flush()

    temp.replace(dest)
    print(f"\nSaved to: {dest}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Download a Whisper GGUF/bin model with a progress bar")
    p.add_argument("--url", default=DEFAULT_URL, help="URL to download (default: known whisper.cpp base model)")
    p.add_argument("--out-dir", default="models", help="Directory to save the model (default: models)")
    p.add_argument("--filename", default="ggml-base.bin", help="Filename to save as (default: ggml-base.bin)")
    p.add_argument("--no-clobber", action="store_true", help="Do not overwrite if file already exists")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / args.filename

    if dest.exists() and args.no_clobber:
        print(f"File already exists: {dest} (use --filename or remove file to re-download)")
        return 0

    try:
        print(f"Downloading:\n  from: {args.url}\n  to:   {dest}\n")
        download_with_progress(args.url, dest)
    except Exception as e:
        print(f"Download failed: {e}")
        # Clean up partial file if present
        part = dest.with_suffix(dest.suffix + ".part")
        try:
            if part.exists():
                part.unlink()
        except Exception:
            pass
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
