import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from matplotlib.lines import Line2D

# Load data
gdf = gpd.read_file("Traveltimes_and_PublicTransport/hsl_lines.geojson")

# Clean types
gdf["vehicle_ty_clean"] = (
    gdf["vehicle_ty"]
    .astype(str)
    .str.strip()
    .str.replace(".0", "", regex=False)
)

# Convert to Web Mercator for basemap
gdf = gdf.to_crs(epsg=3857)


mode_map = {
    "0":   {"name": "Tram",  "color": "#2E8B57"},  # softer green
    "1":   {"name": "Metro", "color": "#C75100"},  # burnt orange
    "3":   {"name": "Bus",   "color": "#6FAED6"},  # muted blue
    "4":   {"name": "Ferry", "color": "#E6E315"},  # desaturated cyan
    "109": {"name": "Train", "color": "#C85A9E"},  # softer magenta
}


# Draw order: lowest first, highest last
draw_order = ["3", "4", "109", "0", "1"]
#            Bus Ferry Train Tram Metro

plt.close("all")

fig, ax = plt.subplots(figsize=(15, 15))

bounds = gdf.total_bounds
minx, miny, maxx, maxy = bounds

xlim = (minx + 3000, maxx - 3000)
ylim = (miny + 3000, maxy - 45000)

ax.set_xlim(xlim)
ax.set_ylim(ylim)

# Basemap
ctx.add_basemap(
    ax,
    source=ctx.providers.CartoDB.PositronNoLabels,
    zoom=12,
    zorder=1,
    reset_extent=True
)

# Force crop again
ax.set_xlim(xlim)
ax.set_ylim(ylim)

# Lines
for code in draw_order:
    info = mode_map[code]
    subset = gdf[gdf["vehicle_ty_clean"] == code]

    if not subset.empty:
        subset.plot(
            ax=ax,
            color=info["color"],
            linewidth=0.7 if code == "3" else 1.0,
            alpha=0.3 if code == "3" else 0.95,
            zorder=draw_order.index(code) + 5
        )

# Legend
legend_items = [
    Line2D([0], [0], color=info["color"], lw=4, label=info["name"])
    for info in mode_map.values()
]

ax.legend(
    handles=legend_items,
    title="Transport mode",
    loc="upper left",
    fontsize="xx-large"
)

ax.set_xlim(xlim)
ax.set_ylim(ylim)
ax.set_axis_off()

# Save
#fig.savefig("Public_transport.png", dpi=600, facecolor="white", pad_inches=0)

plt.show()