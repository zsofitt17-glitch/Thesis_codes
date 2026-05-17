import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from cmcrameri import cm

# ---------------------------
# FILE PATHS
# ---------------------------
TRAVEL_FILE = "Traveltimes_and_PublicTransport/Helsinki_Travel_Time_Matrix_2023_travel_times_to_5963653.csv"
START_GRID = 5963653
GRID_FILE = 'Traveltimes_and_PublicTransport/Helsinki_Travel_Time_Matrix_2023_grid.gpkg'

TRAVEL_MODE = "pt_n_avg"  # pt_n_avg = Public transport, rush hour, avarage walking time, bike_slo, bike_fst, car_r (car rush hour), car_n (car night)
TIME_BINS = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 33, 36, 39, 42, 45, 50, 55, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 170, 190, 210, 230, 250, 300, 400, 500, 650, 800, 1000]
#[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 33, 36, 39, 42, 45, 50, 55, 60, 70, 80, 90, 100, 1000]  - for cars I used this one

# ---------------------------
# LOAD TRAVEL DATA
# ---------------------------
df = pd.read_csv(TRAVEL_FILE)

# ---------------------------
# LOAD GRID
# ---------------------------
grid = gpd.read_file(GRID_FILE)


grid["id"] = grid["id"].astype(int)
df["from_id"] = df["from_id"].astype(int)

# ---------------------------
# MERGE
# ---------------------------
gdf = grid.merge(
    df,
    left_on="id",      # grid cell id
    right_on="from_id" # origins
)

# Remove missing values
gdf = gdf.dropna(subset=[TRAVEL_MODE])
print("Merged cells:", len(gdf))

# ---------------------------
# CLASSIFY (isochrone bins)
# ---------------------------
gdf["time_bin"] = pd.cut(
    gdf[TRAVEL_MODE],
    bins=TIME_BINS
)

# ---------------------------
# REPROJECT FOR BASEMAP
# ---------------------------
gdf = gdf.to_crs(epsg=3857)

dest = grid[grid["id"] == START_GRID].copy()
dest = dest.to_crs(epsg=3857)
dest_point = dest.geometry.centroid


# ---------------------------
# PLOT
# ---------------------------
fig, ax = plt.subplots(figsize=(10, 10))

gdf.plot(
    column="time_bin",
    cmap=cm.lajolla_r,
    linewidth=0,
    alpha=0.9,
    legend=False,
    ax=ax
)

ax.set_xlim(gdf.total_bounds[0], gdf.total_bounds[2])
ax.set_ylim(gdf.total_bounds[1], gdf.total_bounds[3])

# Basemap
'''ctx.add_basemap(
    ax,
    source=ctx.providers.CartoDB.PositronNoLabels,
    zoom=10
)'''

ax.scatter(
    dest_point.x,
    dest_point.y,
    marker="*",
    s=100,
    color="firebrick",
    edgecolor="black",
    linewidth=0.5,
    zorder=10
)

# Title
'''ax.set_title(
    "Travel Time to Destination \nPublic Transport (Average, night)",
    fontsize=14
)'''

ax.set_axis_off()

#plt.savefig("Pictures/Traveltimes/traveltimes_pt-n.png", dpi=600, bbox_inches="tight")

plt.show()