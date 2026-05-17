import geopandas as gpd
import pandas as pd
import requests
import matplotlib.pyplot as plt
import contextily as ctx

# ---------------------------
# 1. Load shapefile
# ---------------------------
shapefile_path = "Postal_code_data/PKS_Postinumeroalueet_2024.shp/Postinumeroalueet_2024.shp"
gdf = gpd.read_file(shapefile_path)

print("Shapefile columns:", gdf.columns)

# ---------------------------
# 2. QUERY
# ---------------------------
url = "https://pxdata.stat.fi/PxWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/arkisto/2025/paavo_pxt_12f3.px"

query = {
  "query": [
    {
      "code": "Postinumeroalue",
      "selection": {
        "filter": "item",
        "values": [
          "00100",
          "00120",
          "00130",
          "00140",
          "00150",
          "00160",
          "00170",
          "00180",
          "00190",
          "00200",
          "00210",
          "00220",
          "00230",
          "00240",
          "00250",
          "00260",
          "00270",
          "00280",
          "00290",
          "00300",
          "00310",
          "00320",
          "00330",
          "00340",
          "00350",
          "00360",
          "00370",
          "00380",
          "00390",
          "00400",
          "00410",
          "00420",
          "00430",
          "00440",
          "00500",
          "00510",
          "00520",
          "00530",
          "00540",
          "00550",
          "00560",
          "00570",
          "00580",
          "00590",
          "00600",
          "00610",
          "00620",
          "00630",
          "00640",
          "00650",
          "00660",
          "00670",
          "00680",
          "00690",
          "00700",
          "00710",
          "00720",
          "00730",
          "00740",
          "00750",
          "00760",
          "00770",
          "00780",
          "00790",
          "00800",
          "00810",
          "00820",
          "00830",
          "00840",
          "00850",
          "00860",
          "00870",
          "00880",
          "00890",
          "00900",
          "00910",
          "00920",
          "00930",
          "00940",
          "00950",
          "00960",
          "00970",
          "00980",
          "00990"
        ]
      }
    },
    {
      "code": "Tiedot",
      "selection": {
        "filter": "item",
        "values": [
          "tr_mtu"
        ]
      }
    },
    {
      "code": "Vuosi",
      "selection": {
        "filter": "item",
        "values": [
          "2023"
        ]
      }
    }
  ],
  "response": {
    "format": "json-stat2"
  }
}

response = requests.post(url, json=query)
data = response.json()

# ---------------------------
# 3. PARSE JSON-STAT2
# ---------------------------
values = data["value"]
areas = data["dimension"]["Postinumeroalue"]["category"]["label"]

df = pd.DataFrame({
    "postal_code": list(areas.keys()),
    "name": list(areas.values()),
    "median_income": values
})

# Clean postal code (ensure 5 digits)
df["postal_code"] = df["postal_code"].str[:5]

# ---------------------------
# 4. JOIN WITH SHAPEFILE
# ---------------------------
gdf["postal_code"] = gdf["Posnro"].astype(str)

gdf = gdf.merge(df, on="postal_code", how="right")
gdf["income_for_class"] = gdf["median_income"].replace(0, pd.NA)

# ---------------------------
# 5. REPROJECT
# ---------------------------
gdf = gdf.to_crs(epsg=3857)

# ---------------------------
# 6. PLOT HEATMAP
# ---------------------------
fig, ax = plt.subplots(figsize=(10, 10))

gdf.plot(
    column="income_for_class",
    label="name",
    ax=ax,
    alpha=0.4,
    cmap="Greens",
    legend=False,
    scheme="quantiles",
    k=20,
    edgecolor="black",
    linewidth=0.3,
    missing_kwds={
        "color": "red",   # how zero areas appear
        "label": "0"
    }
)

'''ctx.add_basemap(
    ax,
    source=ctx.providers.CartoDB.PositronNoLabels,
    zoom=11
)'''

ax.set_axis_off()
#ax.set_title("Median Income of Households by Postal Code Area (Helsinki, 2023)", fontsize=14)

plt.show()

# Save
#fig.savefig("Pictures/Postal_code/income-q.png", dpi=600, bbox_inches="tight")