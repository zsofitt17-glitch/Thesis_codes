import pandas as pd
import numpy as np
from pathlib import Path

# File paths
DATA_DIR = Path("Bike_routes")

trip_files = sorted(DATA_DIR.glob("2023-*.csv"))
station_file = DATA_DIR / "HSL_bike_stations.csv"

# Load and merge trip files
trips = pd.concat(
    [pd.read_csv(file) for file in trip_files],
    ignore_index=True
)

# Clean column names
trips.columns = trips.columns.str.strip()

# Parse datetime columns
trips["Departure"] = pd.to_datetime(trips["Departure"], errors="coerce")
trips["Return"] = pd.to_datetime(trips["Return"], errors="coerce")

# Remove rows with missing essential values
trips = trips.dropna(
    subset=[
        "Departure",
        "Departure station id",
        "Return station id"
    ]
)

# Make station IDs consistent
trips["Departure station id"] = trips["Departure station id"].astype(int)
trips["Return station id"] = trips["Return station id"].astype(int)

# Extract date and hour
trips["date"] = trips["Departure"].dt.date
trips["hour"] = trips["Departure"].dt.hour

# Number of active days in the dataset
active_days = trips["date"].nunique()

print(f"Total trips: {len(trips):,}")
print(f"Active days: {active_days}")
print(f"Date range: {trips['Departure'].min()} to {trips['Departure'].max()}")


# Count departures by day and hour
daily_hourly_counts = (
    trips
    .groupby(["date", "hour"])
    .size()
    .reset_index(name="departures")
)

# Ensure every day has every hour represented
all_dates = pd.DataFrame({"date": trips["date"].unique()})
all_hours = pd.DataFrame({"hour": range(24)})

full_grid = all_dates.merge(all_hours, how="cross")

daily_hourly_counts = full_grid.merge(
    daily_hourly_counts,
    on=["date", "hour"],
    how="left"
).fillna({"departures": 0})

# Average departures per hour per day
hourly_average = (
    daily_hourly_counts
    .groupby("hour")["departures"]
    .mean()
    .reset_index(name="avg_departures_per_day")
)

hourly_average.to_csv("hourly_average_departures.csv", index=False)

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

hours = hourly_average["hour"].values
values = hourly_average["avg_departures_per_day"].values

order = np.argsort(hours)
hours = hours[order]
values = values[order]

# Middle of hourly bins
theta = 2 * np.pi * (hours + 0.5) / 24
theta_closed = np.append(theta, theta[0] + 2 * np.pi)

clock_radius = 2
ring_inner = clock_radius + 0.15
ring_outer = ring_inner + 0.55
data_inner = ring_outer + 0.15
data_outer_max = 5

value_scaled = values / values.max()
data_radius = data_inner + value_scaled * (data_outer_max - data_inner)
data_radius_closed = np.append(data_radius, data_radius[0])

sky_colors = [
    (0.00, "#081a33"),
    (0.20, "#102a4c"),
    (0.35, "#3f6fa3"),
    (0.50, "#9fc9e8"),
    (0.65, "#3f6fa3"),
    (0.80, "#102a4c"),
    (1.00, "#081a33")
]

sky_cmap = LinearSegmentedColormap.from_list("sky_cmap", sky_colors)

fig = plt.figure(figsize=(12, 12))
ax = plt.subplot(111, polar=True)

ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)
ax.set_ylim(0, data_outer_max + 0.7)
ax.set_xticks([])
ax.set_yticks([])
ax.grid(False)
ax.spines["polar"].set_visible(False)

# Data shape
# Bars

bar_width = 2 * np.pi / 24 * 0.55

bar_color = "#d9826b"
bar_edge = "#7a3f32"     # darker outline

for angle, radius in zip(theta, data_radius):
    ax.bar(
        angle,
        radius - data_inner,
        width=bar_width,
        bottom=data_inner,
        color=bar_color,
        edgecolor=bar_edge,
        linewidth=1.1,
        alpha=0.85,
        zorder=6
    )

# Small rounded-looking points at the ends
ax.scatter(
    theta,
    data_radius,
    s=38,
    color="#fff7ef",
    edgecolor=bar_edge,
    linewidth=1.2,
    zorder=8
)

# Outer daylight ring, separated from data
ring_steps = 360
ring_theta = np.linspace(0, 2 * np.pi, ring_steps, endpoint=False)
ring_width = 2 * np.pi / ring_steps

for i, angle in enumerate(ring_theta):
    color = sky_cmap(i / ring_steps)

    ax.bar(
        angle,
        ring_outer - ring_inner,
        width=ring_width,
        bottom=ring_inner,
        color=color,
        edgecolor=color,
        linewidth=0,
        zorder=3
    )

# Clock
# Main clock part
clock_face = plt.Circle(
    (0, 0),
    clock_radius,
    transform=ax.transData._b,
    facecolor="#fff8e7",
    edgecolor="#8a5a22",
    linewidth=3,
    zorder=20
)
ax.add_artist(clock_face)

# Smaller inner circle
inner_circle = plt.Circle(
    (0, 0),
    clock_radius * 0.88,
    transform=ax.transData._b,
    facecolor="none",
    edgecolor="#d6b77a",
    linewidth=1.3,
    zorder=21
)
ax.add_artist(inner_circle)

# 24 small dots around the clock
for h in range(24):
    a = 2 * np.pi * h / 24

    ax.scatter(
        [a],
        [clock_radius * 0.94],
        s=18 if h % 6 == 0 else 8,
        color="#5c3b1e",
        zorder=25
    )

# Four main clock numbers
clock_labels = {
    0: "XII",
    6: "III",
    12: "VI",
    18: "IX"
}

for h, label in clock_labels.items():
    a = 2 * np.pi * h / 24

    ax.text(
        a,
        clock_radius * 0.72,
        label,
        ha="center",
        va="center",
        fontsize=25,
        fontfamily="serif",
        color="#4b2e13",
        zorder=30
    )

minute_angle = 2 * np.pi * 9.6 / 24

hour_angle = 2 * np.pi * 1.4 / 24

ax.plot(
    [0, minute_angle],
    [0, clock_radius * 0.78],
    color="#2b2b2b",
    linewidth=3,
    solid_capstyle="round",
    zorder=35
)

ax.plot(
    [0, hour_angle],
    [0, clock_radius * 0.58],
    color="#2b2b2b",
    linewidth=4,
    solid_capstyle="round",
    zorder=36
)

# Center dot
ax.scatter(
    [0],
    [0],
    s=85,
    color="#2b2b2b",
    zorder=40
)




# HOUR LABELS INSIDE THE BLUE RING

label_radius = (ring_inner + ring_outer) / 2

for h in range(24):
    angle = 2 * np.pi * h / 24

    ax.text(
        angle,
        label_radius,
        f"{h:02d}",
        ha="center",
        va="center",
        fontsize=8.5,
        fontfamily="DejaVu Sans Mono",
        fontweight="bold",
        color="white",
        zorder=20
    )


plt.title(
    "Average Bike Departures by Hour\nApril–October 2023",
    fontsize=22,
    fontfamily="serif",
    pad=35
)


plt.tight_layout()
#plt.savefig("Clock_pics_final.png", dpi=600, bbox_inches="tight")
plt.show()