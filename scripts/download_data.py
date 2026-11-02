"""Download the raw source datasets into data/raw/ and verify their checksums.

Sources and checksums are documented in docs/data-sources.md. A checksum
mismatch usually means the publisher updated the dataset: review the changes
before re-running with --accept-changed.
"""
from pathlib import Path
import argparse
import hashlib
import shutil
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data/raw"

SOURCES = [
    {
        "name": "CDE California Public Schools 2025-26 (GeoJSON)",
        "url": "https://gis.data.ca.gov/api/download/v1/items/0cab44bcfd9a44eb88197147e4d37e8b/geojson?layers=0",
        "path": RAW_DIR / "california-public-schools-2025-2026.geojson",
        "sha256": "29d5af3991a2151c4e13d72726322f85bd9d098c556c4a4b09cbc965693e68af",
    },
    {
        "name": "Census TIGER/Line 2026 Places, California (shapefile)",
        "url": "https://www2.census.gov/geo/tiger/TIGER2026/PLACE/tl_2026_06_place.zip",
        "path": RAW_DIR / "tl_2026_06_place/tl_2026_06_place.zip",
        "sha256": "4f1475be8db892b1d4894011846c5c857fe445bf876e470003170cd333d68032",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "community-services-explorer"})
    # Write to a temporary file first so an interrupted download never looks complete
    with urllib.request.urlopen(request, timeout=120) as response, tempfile.NamedTemporaryFile(
        dir=destination.parent, delete=False
    ) as tmp:
        shutil.copyfileobj(response, tmp)
    Path(tmp.name).replace(destination)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--accept-changed",
        action="store_true",
        help="keep files whose checksum differs from the documented one",
    )
    args = parser.parse_args()

    mismatches = []
    for source in SOURCES:
        path = source["path"]
        if path.exists() and sha256(path) == source["sha256"]:
            print(f"OK (already present): {source['name']}")
        else:
            print(f"Downloading: {source['name']}")
            download(source["url"], path)
            if sha256(path) == source["sha256"]:
                print(f"OK: {path.relative_to(ROOT)}")
            else:
                mismatches.append(source)
                print(f"CHECKSUM MISMATCH: {path.relative_to(ROOT)} ({sha256(path)})")

        if path.suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                archive.extractall(path.parent)

    if mismatches and not args.accept_changed:
        raise SystemExit(
            "The source data changed since it was documented. Review it, update "
            "docs/data-sources.md, then re-run with --accept-changed."
        )


if __name__ == "__main__":
    main()
