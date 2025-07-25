
import os
import pandas as pd
import geopandas as gpd
from fuzzywuzzy import fuzz, process
from pandasgui import show
import pickle

# ----------------------------
# Configuration
# ----------------------------
DATA_FILE = "data/Ch 70 District Profiles Actual NSS Over Required.xlsx"
SHAPE_DIR = "data"
OUTPUT_PKL = "data/matched_districts.pkl"
OUTPUT_GEOJSON = "data/matched_districts.geojson"
DEBUG_MODE = False  # Toggle for inspection and debugging

# ----------------------------
# Utility Functions
# ----------------------------
def clean_name(name):
    return (
        str(name).lower()
        .replace("school district", "")
        .replace("public schools", "")
        .replace("sd", "")
        .replace("-", " ")
        .replace(",", "")
        .replace(".", "")
        .strip()
    )

# ----------------------------
# Load and Filter Excel
# ----------------------------
xls = pd.ExcelFile(DATA_FILE)
df = pd.read_excel(xls, sheet_name="MACh70_All_Districts")
df = df[df["DistCode"] != "0000"]
df = df[df["ActualNSS_portion_ReqNSS"] != 0]
df["clean_name"] = df["DistOrg"].apply(clean_name)

# ----------------------------
# Load Shapefiles
# ----------------------------
def load_shapefiles():
    unified = gpd.read_file(os.path.join(SHAPE_DIR, "tl_2023_25_unsd.shp"))
    elementary = gpd.read_file(os.path.join(SHAPE_DIR, "tl_2023_25_elsd.shp"))
    secondary = gpd.read_file(os.path.join(SHAPE_DIR, "tl_2023_25_scsd.shp"))

    unified["type"] = "unified"
    elementary["type"] = "elementary"
    secondary["type"] = "secondary"

    unified = unified.rename(columns={"UNSDLEA": "LEA", "NAME": "NAME"})
    elementary = elementary.rename(columns={"ELSDLEA": "LEA", "NAME": "NAME"})
    secondary = secondary.rename(columns={"SCSDLEA": "LEA", "NAME": "NAME"})

    return pd.concat([unified, elementary, secondary], ignore_index=True)

shapes = load_shapefiles()
shapes["clean_name"] = shapes["NAME"].apply(clean_name)

# ----------------------------
# Fuzzy Match
# ----------------------------
matches = []
unmatched_log = []

for idx, row in df.iterrows():
    match_result = process.extractOne(row["clean_name"], shapes["clean_name"], scorer=fuzz.ratio)
    if not match_result:
        unmatched_log.append((row["DistOrg"], []))
        continue

    best_match = match_result[0]
    score = match_result[1]
    if score >= 90:
        match_row = shapes[shapes["clean_name"] == best_match].iloc[0]
        combined = row.to_dict()
        for col in match_row.index:
            if col not in combined:
                combined[col] = match_row[col]
        combined["geometry"] = match_row["geometry"]
        matches.append(combined)
    else:
        top_matches = process.extract(row["clean_name"], shapes["clean_name"], scorer=fuzz.ratio, limit=3)
        unmatched_log.append((row["DistOrg"], top_matches))

matched_df = pd.DataFrame(matches)
matched_gdf = gpd.GeoDataFrame(matched_df, geometry="geometry", crs=shapes.crs).to_crs(epsg=4326)

# ----------------------------
# Create % col for Streamlit map
# ----------------------------

matched_gdf["NSS_percent"] = (matched_gdf["ActualNSS_portion_ReqNSS"] * 100).round(0).astype("Int64")

# ----------------------------
# Assign Group Type
# ----------------------------
def assign_group(row):
    dist_type = str(row.get("DistType", "") or "")
    if dist_type == "District" or dist_type.startswith("Regional Union"):
        return "Districts"
    elif dist_type.startswith("Regional Composite") or dist_type.startswith("Superintendency Union"):
        return "Regions"
    elif dist_type == "Regional":
        return "Unified Regions"
    return "Other"

matched_gdf["GroupType"] = matched_gdf.apply(assign_group, axis=1)

# ----------------------------
# Save Output
# ----------------------------
matched_gdf.to_file(OUTPUT_GEOJSON, driver="GeoJSON")
with open(OUTPUT_PKL, "wb") as f:
    pickle.dump(matched_gdf, f)

# ----------------------------
# Debug Preview
# ----------------------------
if DEBUG_MODE:
    print("\n=== Previewing matched data ===")
    print(matched_gdf[["DistOrg", "FY", "ActualNSS_portion_ReqNSS", "GroupType"]].head(10))

    if unmatched_log:
        print("\n=== Unmatched or Low-Confidence Matches ===")
        for name, matches in unmatched_log:
            print(f"{name} → {matches}")

    show(matched_gdf)  # Launches an interactive GUI
