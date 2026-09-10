#!/usr/bin/env python3
"""Download the Customer Support on Twitter dataset.

This script provides two methods for acquiring the dataset:

Method A: Kaggle API (automated)
    Requires KAGGLE_USERNAME and KAGGLE_KEY environment variables.
    Install: pip install kaggle
    Credentials: https://www.kaggle.com/settings/account (API section)

Method B: Manual download
    1. Go to: https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter
    2. Download the dataset ZIP file
    3. Extract CSV files into data/raw/
    4. Run this script to verify

The dataset contains approximately 3M tweets across multiple brands,
representing real customer-support conversations on Twitter.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Expected files from the dataset
EXPECTED_FILES = [
    "twcs.csv",  # Main dataset file (tweets with conversation threads)
]


def find_project_root() -> Path:
    """Find the project root directory (where this script's parent is scripts/)."""
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent


def check_kaggle_credentials() -> bool:
    """Check if Kaggle credentials are available as environment variables."""
    username = os.environ.get("KAGGLE_USERNAME")
    key = os.environ.get("KAGGLE_KEY")
    if username and key:
        return True
    return False


def download_via_kaggle_api(raw_dir: Path) -> bool:
    """Download dataset using the Kaggle CLI.

    Returns True if successful, False otherwise.
    """
    try:
        import subprocess

        dataset_slug = "thoughtvector/customer-support-on-twitter"
        print(f"Downloading dataset: {dataset_slug}")
        print(f"Target directory: {raw_dir}")

        # Use kaggle datasets download command
        result = subprocess.run(
            [
                "kaggle",
                "datasets",
                "download",
                "-d",
                dataset_slug,
                "-p",
                str(raw_dir),
                "--unzip",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            print(f"Kaggle CLI error: {result.stderr}")
            return False

        print("Download complete.")
        return True

    except FileNotFoundError:
        print("Error: 'kaggle' CLI not found.")
        print("Install it with: pip install kaggle")
        return False
    except subprocess.TimeoutExpired:
        print("Error: Download timed out after 5 minutes.")
        return False
    except Exception as e:
        print(f"Error during download: {e}")
        return False


def verify_manual_download(raw_dir: Path) -> bool:
    """Verify that expected files exist after manual download.

    Returns True if all expected files are found.
    """
    print("Checking for expected dataset files...")
    all_found = True

    for filename in EXPECTED_FILES:
        filepath = raw_dir / filename
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"  Found: {filename} ({size_mb:.1f} MB)")
        else:
            print(f"  Missing: {filename}")
            all_found = False

    # Also check for any CSV files that might be present
    csv_files = list(raw_dir.glob("*.csv"))
    if csv_files:
        print(f"\nAll CSV files in data/raw/:")
        for f in csv_files:
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"  {f.name} ({size_mb:.1f} MB)")
    else:
        print("\nNo CSV files found in data/raw/.")

    return all_found


def create_metadata(raw_dir: Path, download_method: str) -> None:
    """Create dataset_metadata.json with acquisition information."""
    metadata = {
        "dataset_name": "Customer Support on Twitter",
        "source": "thoughtvector/customer-support-on-twitter",
        "kaggle_url": "https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter",
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "download_method": download_method,
        "files": [],
        "total_rows": None,
        "columns": None,
        "notes": [],
    }

    # Catalog found files
    for filename in EXPECTED_FILES:
        filepath = raw_dir / filename
        if filepath.exists():
            metadata["files"].append({
                "filename": filename,
                "size_bytes": filepath.stat().st_size,
                "size_mb": round(filepath.stat().st_size / (1024 * 1024), 2),
            })

    # Also catalog any other CSV files
    for csv_path in sorted(raw_dir.glob("*.csv")):
        if csv_path.name not in EXPECTED_FILES:
            metadata["files"].append({
                "filename": csv_path.name,
                "size_bytes": csv_path.stat().st_size,
                "size_mb": round(csv_path.stat().st_size / (1024 * 1024), 2),
            })
            metadata["notes"].append(f"Additional file found: {csv_path.name}")

    metadata_path = raw_dir / "dataset_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"\nMetadata saved to: {metadata_path}")


def print_manual_instructions() -> None:
    """Print instructions for manual dataset download."""
    print("=" * 70)
    print("MANUAL DOWNLOAD INSTRUCTIONS")
    print("=" * 70)
    print()
    print("Step 1: Go to the dataset page")
    print("  https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter")
    print()
    print("Step 2: Click 'Download' (you may need a free Kaggle account)")
    print()
    print("Step 3: Extract the downloaded ZIP file")
    print()
    print("Step 4: Copy the CSV file(s) into this directory:")
    print(f"  {Path('data/raw').resolve()}")
    print()
    print("Step 5: Run this script again to verify:")
    print("  python scripts/download_dataset.py --verify-only")
    print()
    print("=" * 70)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download the Customer Support on Twitter dataset."
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify that files exist (do not attempt download).",
    )
    parser.add_argument(
        "--method",
        choices=["kaggle", "manual"],
        default="auto",
        help="Download method: 'kaggle' for API, 'manual' for instructions, 'auto' to try API first.",
    )
    args = parser.parse_args()

    project_root = find_project_root()
    raw_dir = project_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    if args.verify_only:
        success = verify_manual_download(raw_dir)
        create_metadata(raw_dir, "manual-verification")
        return 0 if success else 1

    # Try download method
    download_method = "manual"
    success = False

    if args.method in ("kaggle", "auto"):
        if check_kaggle_credentials():
            print("Kaggle credentials found. Attempting API download...")
            success = download_via_kaggle_api(raw_dir)
            if success:
                download_method = "kaggle-api"
        elif args.method == "kaggle":
            print("Error: Kaggle credentials not found.")
            print("Set KAGGLE_USERNAME and KAGGLE_KEY environment variables.")
            print("Get credentials from: https://www.kaggle.com/settings/account")
            return 1
        else:
            print("Kaggle credentials not found. Falling back to manual instructions.")

    if not success:
        print_manual_instructions()
        download_method = "manual-instructions"

    # Verify and create metadata
    verify_manual_download(raw_dir)
    create_metadata(raw_dir, download_method)

    return 0


if __name__ == "__main__":
    sys.exit(main())
