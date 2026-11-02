from pathlib import Path
import geopandas as gpd

data_path = (
    Path(__file__).resolve().parents[1]
    / "data/raw/california-public-schools-2025-2026.geojson"
)

STUDY_CITIES = ["Redlands", "Yucaipa"]

if not data_path.exists():
    raise FileNotFoundError(data_path)

schools = gpd.read_file(data_path)

print("Records:", len(schools))
print("CRS:", schools.crs)
print("Geometry types:")
print(schools.geom_type.value_counts())
print("Columns:")
print(schools.columns.tolist())
print("Null geometries:", schools.geometry.isna().sum())
print("Empty geometries:", schools.geometry.is_empty.sum())

print("Duplicate CDSCode:", schools["CDSCode"].duplicated().sum())

print("\nSample attributes:")
print(schools.drop(columns="geometry").head().to_string())

# City is the mailing-address city, not a municipal boundary
study = schools[schools["City"].isin(STUDY_CITIES)]
print("\nStudy area records (City):", len(study))
print(study.groupby(["City", "Status"]).size().to_string())
print("\nVirtual by city (N=no, C=mostly classroom, F=mostly virtual, V=exclusively virtual):")
print(study.groupby(["City", "Virtual"]).size().to_string())