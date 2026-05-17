import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import contextily as ctx
import osmnx as ox
import matplotlib.colors as mcolors
import numpy as np


# File paths
GRID_FILE = "Population_dist_interactive/target_zones_grid250m_EPSG3067.geojson"
POP_FILE = "Population_dist_interactive/HMA_Dynamic_population_24H_workdays.csv" # 24H_sat.csv for Saturday, 24H_sun.csv for Sunday
HOUR_COL = "H19"  # hour


# Load and prepare data
grid = gpd.read_file(GRID_FILE)

# Force correct CRS
grid = grid.set_crs(epsg=3067, allow_override=True)

pop = pd.read_csv(POP_FILE)

# Merge
merged = grid.merge(pop, on="YKR_ID")

# Handle missing values
merged[HOUR_COL] = merged[HOUR_COL].fillna(0)


# Clip to Helsinki
helsinki = ox.geocode_to_gdf("Helsinki, Finland")
helsinki = helsinki.to_crs(epsg=3067)

merged_helsinki = gpd.clip(merged, helsinki)

# Reproject for mapping
merged_final = merged_helsinki.to_crs(epsg=3857)

# Fix geometry issues
merged_final["geometry"] = merged_final.buffer(0)
merged_web = merged_final[merged_final.geometry.notnull() & merged_final.is_valid]

# Plot map
fig, ax = plt.subplots(figsize=(12, 14))

# Set map extent (zoom to Helsinki)
bounds = merged_final.total_bounds
ax.set_xlim(bounds[0], bounds[2])
ax.set_ylim(bounds[1], bounds[3])

# Basemap
'''ctx.add_basemap(
    ax,
    crs=merged_web.crs,
    source=ctx.providers.CartoDB.DarkMatterNoLabels,  # neutral gray map
    zoom=14
)'''

# -----------------------------
# Color scaling like interactive map
# -----------------------------
values = merged_final[HOUR_COL].fillna(0)
positive_values = values[values > 0]

vmin = 0
vmax = positive_values.quantile(0.98)

# Truncated Inferno colormap
base_cmap = plt.cm.inferno

truncated_inferno = mcolors.LinearSegmentedColormap.from_list(
    "truncated_inferno",
    base_cmap(np.linspace(0.12, 0.94, 256))
)

# Population layer
merged_final.plot(
    column=HOUR_COL,
    cmap=truncated_inferno,
    vmin=vmin,
    vmax=vmax,
    edgecolor="none",
    alpha=1,
    legend=False,
    ax=ax
)

# Title & layout
#ax.set_title("Helsinki Dynamic Population — 09:00 (Workday)", fontsize=16)
ax.set_axis_off()
plt.tight_layout()

# Save
#plt.savefig("Pictures/Pop_workday_19", dpi=600)
plt.show()
