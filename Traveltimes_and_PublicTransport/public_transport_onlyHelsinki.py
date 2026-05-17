import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import osmnx as ox
from matplotlib.lines import Line2D

# -----------------------------
# 1. Load transport lines
# -----------------------------
gdf = gpd.read_file("Traveltimes_and_PublicTransport/hsl_lines.geojson")

gdf["vehicle_ty_clean"] = (
    gdf["vehicle_ty"]
    .astype(str)
    .str.strip()
    .str.replace(".0", "", regex=False)
)

# Force correct CRS if needed
gdf = gdf.set_crs(epsg=4326, allow_override=True)

# -----------------------------
# 2. Clip to Helsinki
# -----------------------------
helsinki = ox.geocode_to_gdf("Helsinki, Finland")
helsinki = helsinki.to_crs(gdf.crs)

gdf_helsinki = gpd.clip(gdf, helsinki)

# -----------------------------
# 3. Reproject for basemap
# -----------------------------
# Reproject for plotting
gdf_final = gdf_helsinki.to_crs(epsg=3857)

# Do NOT buffer(0) lines
gdf_final = gdf_final[
    gdf_final.geometry.notnull() &
    ~gdf_final.geometry.is_empty
]

# -----------------------------
# 4. Colors
# -----------------------------
mode_map = {
    "0":   {"name": "Tram",  "color": "#2E8B57"},
    "1":   {"name": "Metro", "color": "#C75100"},
    "3":   {"name": "Bus",   "color": "#6FAED6"},
    "4":   {"name": "Ferry", "color": "#E6E315"},
    "109": {"name": "Train", "color": "#C85A9E"},
}

draw_order = ["3", "4", "109", "0", "1"]

# -----------------------------
# 5. Plot
# -----------------------------
fig, ax = plt.subplots(figsize=(12, 14))

# Add padding so everything can be seen

bounds = gdf_final.total_bounds
pad = 500
ax.set_xlim(bounds[0] - pad, bounds[2] + pad)
ax.set_ylim(bounds[1], bounds[3] + pad*2.5)

# Basemap underneath
ctx.add_basemap(
    ax,
    crs=gdf_final.crs,
    source=ctx.providers.CartoDB.PositronNoLabels,
    zoom=12
)

# Boundary overlay
helsinki_boundary = helsinki.to_crs(epsg=3857)

helsinki_boundary.boundary.plot(
    ax=ax,
    color="black",
    linewidth=2,
    zorder=5
)

# Transport lines
for code in draw_order:
    info = mode_map[code]
    subset = gdf_final[gdf_final["vehicle_ty_clean"] == code]

    if not subset.empty:
        subset.plot(
            ax=ax,
            color=info["color"],
            linewidth=0.8 if code == "3" else 1.5,
            alpha=0.95,
            zorder=3
        )

# Legend
legend_items = [
    Line2D([0], [0], color=info["color"], lw=4, label=info["name"])
    for info in mode_map.values()
]

ax.legend(handles=legend_items, title="Transport mode", loc="lower right", fontsize="x-large")

#ax.set_title("Public Transport Lines in Helsinki", fontsize=16)
ax.set_axis_off()

plt.tight_layout()
#plt.savefig("Pictures/helsinki_transport_clipped_clean2.png", dpi=600, bbox_inches="tight")
plt.show()