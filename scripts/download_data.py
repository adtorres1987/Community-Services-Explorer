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
    {
        "name": "Census TIGER/Line 2020 blocks, San Bernardino County (shapefile)",
        "url": "https://www2.census.gov/geo/tiger/TIGER2020PL/LAYER/TABBLOCK/2020/tl_2020_06071_tabblock20.zip",
        "path": RAW_DIR / "tl_2020_06071_tabblock20/tl_2020_06071_tabblock20.zip",
        "sha256": "46bdeb50e3d035b3268d908b0107b48123531375c9f422d6eca74b804af809f7",
    },
    {
        "name": "Census 2020 P.L. 94-171 redistricting data, California",
        "url": "https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/California/ca2020.pl.zip",
        "path": RAW_DIR / "ca2020.pl/ca2020.pl.zip",
        "sha256": "e02c83c85a9a5d69ded4bf0d4c8ebe3f4bcd2d8e5911db765e9e42915ad1f753",
        # Only the geographic header is needed: it carries POP100 for every block
        "extract": ["cageo2020.pl"],
    },
    {
        "name": "Census 2020 Demographic and Housing Characteristics File (DHC), California",
        "url": "https://www2.census.gov/programs-surveys/decennial/2020/data/demographic-and-housing-characteristics-file/California/ca2020.dhc.zip",
        "path": RAW_DIR / "ca2020.dhc/ca2020.dhc.zip",
        "sha256": "380711a2de1313fea48f2184810baccc83e36643f145daab4a2f37130d815c61",
        # ~1 GB; only the geographic header and segment 6 (table P12, sex by age) are needed
        "extract": ["cageo2020.dhc", "ca000062020.dhc"],
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
                archive.extractall(path.parent, members=source.get("extract"))

    if mismatches and not args.accept_changed:
        raise SystemExit(
            "The source data changed since it was documented. Review it, update "
            "docs/data-sources.md, then re-run with --accept-changed."
        )


if __name__ == "__main__":
    main()
