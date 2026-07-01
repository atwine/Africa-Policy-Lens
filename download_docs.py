"""
download_docs.py
----------------
Download PDFs listed in docs/policy_download_list.md and store them in the
correct subdirectories (docs/, docs/future/, docs/reference/).

Usage:
    python download_docs.py
    python download_docs.py --no-verify-ssl

The script:
- Parses the markdown table in policy_download_list.md
- Creates target directories if they don't exist
- Downloads each PDF with a browser-like User-Agent
- Verifies that the file is a real PDF (starts with %PDF) and > 10KB
- Logs failures and prints a summary at the end

Use --no-verify-ssl for sites with self-signed or expired certificates
(e.g. some government and academic domains).
"""

import argparse
import os
import re
import sys
from pathlib import Path

# Force UTF-8 output on Windows to handle URLs and filenames with special characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress the warning when SSL verification is disabled
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DOWNLOAD_LIST = PROJECT_ROOT / "docs" / "policy_download_list.md"
BASE_DIR = PROJECT_ROOT / "docs"

# Browser-like User-Agent to avoid blocks from government/academic sites
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )
}

MIN_SIZE_BYTES = 10 * 1024  # 10KB
TIMEOUT_SECONDS = 60


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def parse_markdown_tables(md_text: str) -> list[dict]:
    """
    Parse the markdown file and return a list of download tasks.
    Each task is {"filename": str, "url": str, "target_dir": Path}.
    """
    tasks = []

    # Split the document into sections by Priority headers
    sections = re.split(r"(?=##\s+PRIORITY\s+\d+:)", md_text)

    for section in sections:
        if not section.strip().startswith("## PRIORITY"):
            continue

        # Find the explicit download location for this section
        location_match = re.search(
            r"\*\*Download location:\*\*\s*`(.+?)`",
            section,
        )
        if not location_match:
            continue

        # Convert backslash path to Path object relative to project root
        raw_location = location_match.group(1).strip()
        # Strip the absolute project prefix if present (e.g. C:\...\PolicyBot\docs)
        project_prefix = str(PROJECT_ROOT).replace("\\", "/")
        if raw_location.replace("\\", "/").startswith(project_prefix):
            raw_location = raw_location.replace("\\", "/")[len(project_prefix):]
        raw_location = raw_location.replace("\\", "/").lstrip("./")
        target_dir = PROJECT_ROOT / Path(raw_location)

        # Extract table rows (lines starting with |)
        for line in section.splitlines():
            line = line.strip()
            if not line.startswith("|") or line.startswith("|---"):
                continue

            parts = [p.strip() for p in line.split("|")]
            # Remove empty leading/trailing cells caused by outer pipes
            parts = [p for p in parts if p]

            # We expect at least 4 columns: # | Document | Filename | URL
            if len(parts) < 4:
                continue

            # Try to extract filename and URL from the row
            filename = None
            url = None

            for cell in parts:
                # Filename is wrapped in backticks
                if not filename and cell.startswith("`") and cell.endswith("`") and cell.lower().endswith(".pdf`"):
                    filename = cell.strip("`").strip()

                # URL is the first http/https link in the row
                if not url:
                    url_match = re.search(r"https?://\S+", cell)
                    if url_match:
                        url = url_match.group(0).strip()
                        # Remove trailing punctuation that might be part of markdown
                        url = url.rstrip(").,;>`'")

            if filename and url:
                tasks.append({
                    "filename": filename,
                    "url": url,
                    "target_dir": target_dir,
                })

    return tasks


def is_valid_pdf(path: Path) -> bool:
    """Check if a file exists, is non-empty, and starts with the PDF magic bytes."""
    if not path.exists():
        return False
    if path.stat().st_size < MIN_SIZE_BYTES:
        return False
    with open(path, "rb") as f:
        return f.read(4) == b"%PDF"


def download_pdf(url: str, target_path: Path, verify_ssl: bool = True) -> bool:
    """Download a PDF from URL to target_path if not already present, returning True on success."""
    if is_valid_pdf(target_path):
        print(f"  SKIPPED (already exists and valid): {target_path.name}")
        return True

    try:
        response = requests.get(
            url, headers=HEADERS, timeout=TIMEOUT_SECONDS, stream=True, verify=verify_ssl
        )
        response.raise_for_status()

        # Stream to disk
        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Verify file size
        if target_path.stat().st_size < MIN_SIZE_BYTES:
            raise ValueError(f"Downloaded file is too small ({target_path.stat().st_size} bytes)")

        # Verify PDF header
        with open(target_path, "rb") as f:
            header = f.read(4)
        if header != b"%PDF":
            raise ValueError(f"File does not start with %PDF header (got {header!r})")

        return True

    except Exception as e:
        # Clean up partial/bad file
        if target_path.exists():
            target_path.unlink()
        print(f"  ERROR: {target_path.name} -> {e}", flush=True)
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Download PDFs listed in docs/policy_download_list.md"
    )
    parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="Disable SSL certificate verification for sites with self-signed certificates",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("PolicyLens — PDF Downloader")
    print("=" * 70)

    if args.no_verify_ssl:
        print("SSL verification: DISABLED\n")

    if not DOWNLOAD_LIST.exists():
        print(f"ERROR: Download list not found: {DOWNLOAD_LIST}")
        sys.exit(1)

    md_text = DOWNLOAD_LIST.read_text(encoding="utf-8")
    tasks = parse_markdown_tables(md_text)

    if not tasks:
        print("WARNING: No download tasks found in the markdown file.")
        sys.exit(0)

    print(f"Found {len(tasks)} PDF(s) to download.\n")

    success = []
    failed = []

    for task in tasks:
        target_dir = task["target_dir"]
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / task["filename"]
        print(f"Downloading {task['filename']}...")
        print(f"  URL: {task['url']}")
        print(f"  Target: {target_path}")

        if download_pdf(task["url"], target_path, verify_ssl=not args.no_verify_ssl):
            if target_path.exists() and target_path.stat().st_size >= MIN_SIZE_BYTES:
                size_kb = target_path.stat().st_size / 1024
                print(f"  OK ({size_kb:.1f} KB)")
            success.append(task["filename"])
        else:
            failed.append(task["filename"])
        print()

    # Summary
    print("=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)
    print(f"  Successful: {len(success)}/{len(tasks)}")
    print(f"  Failed:     {len(failed)}/{len(tasks)}")

    if success:
        print("\n  Successful downloads:")
        for name in success:
            print(f"    ✓ {name}")

    if failed:
        print("\n  Failed downloads:")
        for name in failed:
            print(f"    ✗ {name}")

    # Critical: Priority 1 failures are especially bad
    priority1_failures = [f for f in failed if any(
        f.startswith(prefix) for prefix in ("south_africa", "kenya", "uganda", "au_malabo")
    )]
    if priority1_failures:
        print("\n  ⚠️  PRIORITY 1 FAILURE — MVP demo cannot proceed without these:")
        for name in priority1_failures:
            print(f"      {name}")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
