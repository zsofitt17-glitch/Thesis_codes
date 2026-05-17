import geopandas as gpd
import pandas as pd
import requests
import folium

# ---------------------------
# 1. Load shapefile
# ---------------------------
shapefile_path = "Postal_code_data/PKS_Postinumeroalueet_2024.shp/Postinumeroalueet_2024.shp"
gdf = gpd.read_file(shapefile_path)

postal_codes = [
    "00100","00120","00130","00140","00150","00160","00170","00180","00190",
    "00200","00210","00220","00230","00240","00250","00260","00270","00280","00290",
    "00300","00310","00320","00330","00340","00350","00360","00370","00380","00390",
    "00400","00410","00420","00430","00440",
    "00500","00510","00520","00530","00540","00550","00560","00570","00580","00590",
    "00600","00610","00620","00630","00640","00650","00660","00670","00680","00690",
    "00700","00710","00720","00730","00740","00750","00760","00770","00780","00790",
    "00800","00810","00820","00830","00840","00850","00860","00870","00880","00890",
    "00900","00910","00920","00930","00940","00950","00960","00970","00980","00990"
]

# ---------------------------
# 2. Query PAAVO data
# ---------------------------
url = "https://pxdata.stat.fi/PxWeb/api/v1/en/Postinumeroalueittainen_avoin_tieto/arkisto/2025/paavo_pxt_12f7.px"

variables = ["tr_mtu", "ra_asunn", "tp_tyopy", "tp_p_koul"]

query = {
    "query": [
        {
            "code": "Postinumeroalue",
            "selection": {"filter": "item", "values": postal_codes}
        },
        {
            "code": "Tiedot",
            "selection": {"filter": "item", "values": variables}
        },
        {
            "code": "Vuosi",
            "selection": {"filter": "item", "values": ["2023"]}
        }
    ],
    "response": {"format": "json-stat2"}
}

data = requests.post(url, json=query).json()

# ---------------------------
# 3. Parse data
# ---------------------------
values = data["value"]
areas = data["dimension"]["Postinumeroalue"]["category"]["label"]

rows = []
i = 0

for pc in postal_codes:
    row = {
        "postal_code": pc,
        "name": areas.get(pc, pc),
        "median_income": values[i],
        "dwellings": values[i + 1],
        "workplaces": values[i + 2],
        "education": values[i + 3],
    }
    rows.append(row)
    i += 4

df = pd.DataFrame(rows)

for col in ["median_income", "dwellings", "workplaces", "education"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# ---------------------------
# 4. Normalize each value against all postal-code areas
# ---------------------------
for col in ["median_income", "dwellings", "workplaces", "education"]:

    if col == "median_income":
        valid_mask = df[col] > 0
    else:
        valid_mask = df[col].notna()

    df[col + "_score"] = 0

    df.loc[valid_mask, col + "_score"] = (
        df.loc[valid_mask, col]
        .rank(pct=True)
        * 100
    ).round(0)

# ---------------------------
# 5. Join with shapefile
# ---------------------------
gdf["postal_code"] = gdf["Posnro"].astype(str)
gdf = gdf.merge(df, on="postal_code", how="right")
gdf = gdf.to_crs(epsg=4326)

# ---------------------------
# 6. Create map
# ---------------------------
m = folium.Map(
    location=[60.21, 25.01],
    zoom_start=11,
    tiles="CartoDB positronnolabels",
    scrollWheelZoom=False
)

def style_function(feature):
    return {
        "fillColor": "#eeeeee",
        "color": "#555",
        "weight": 0.7,
        "fillOpacity": 0.55,
    }

def highlight_function(feature):
    return {
        "fillColor": "#cce5ff",
        "color": "#005bbb",
        "weight": 2,
        "fillOpacity": 0.85,
    }

geojson = folium.GeoJson(
    gdf,
    style_function=style_function,
    highlight_function=highlight_function,
    tooltip=folium.GeoJsonTooltip(
        fields=["name", "postal_code"],
        aliases=["Area:", "Postal code:"],
        sticky=False
    )
).add_to(m)

# ---------------------------
# 7. Floating pictogram panel
# ---------------------------
panel_html = """
<div id="info-panel">
  <h2>Select a postal code area</h2>
  <p>Click an area to see how it compares with the other Helsinki postal-code areas.</p>
</div>

<style>
#info-panel {
        position: absolute;
        top: 24px;
        right: 24px;
        width: 320px;
        max-height: 75vh;
        overflow-y: auto;
        background: white;
        z-index: 9999;
        padding: 10px;
        border-radius: 12px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.18);
        font-family: Arial, sans-serif;
    }

    #info-panel h2 {
        margin-top: 0;
        font-size: 16px;
        margin-bottom: 8px;
    }

    .metric {
        margin-top: 8px;
    }

    .metric-title {
        display: flex;
        font-size: 12px;
        justify-content: space-between;
        font-weight: bold;
        margin-bottom: 4px;
    }

    .icons {
        display: grid;
        grid-template-columns: repeat(10, 1fr);
        gap: 1px;
        justify-items: center;
        margin-top: 0;
    }

    .icon {
        font-size: 24px;
    }

    .icon.inactive {
        opacity: 0.12;
        filter: grayscale(100%);
    }

    .income {
        color: #2f9e44;
    }

    .dwellings {
        color: #f08c00;
    }

    .workplaces {
        color: #1971c2;
    }

    .education {
        color: #9c36b5;
    }

    .small-note {
        color: #666;
        font-size: 11px;
        margin-top: 6px;
    }
</style>
"""

m.get_root().html.add_child(folium.Element(panel_html))

# ---------------------------
# 8. JavaScript click behavior
# ---------------------------
geojson_name = geojson.get_name()

js = f"""
<script>
setTimeout(function() {{

function makeIcons(score, cssClass, symbol) {{
    const rounded = Math.round(score / 10);
    let html = '<div class="icons">';

    for (let i = 1; i <= 10; i++) {{
        const active = i <= rounded ? cssClass : 'inactive';
        html += `<span class="icon ${{active}}">${{symbol}}</span>`;
    }}

    html += '</div>';
    return html;
}}

function metricBlock(title, value, score, cssClass, symbol, suffix='') {{
    return `
      <div class="metric">
        <div class="metric-title">
          <span>${{title}}</span>
        </div>
        ${{makeIcons(score, cssClass, symbol)}}
        <div class="small-note">
          Actual value: ${{Number(value).toLocaleString()}}${{suffix}}
        </div>
      </div>
    `;
}}

{geojson_name}.eachLayer(function(layer) {{
    layer.on('click', function(e) {{
        const p = e.target.feature.properties;

        document.getElementById('info-panel').innerHTML = `
            <h2>${{p.name}}</h2>
            <p><strong>Postal code:</strong> ${{p.postal_code}}</p>

            ${{metricBlock('Median household income', p.median_income, p.median_income_score, 'income', '€')}}
            ${{metricBlock('Dwellings', p.dwellings, p.dwellings_score, 'dwellings', '⬤')}}
            ${{metricBlock('Workplaces', p.workplaces, p.workplaces_score, 'workplaces', '⬤')}}
            ${{metricBlock('Jobs in education sector', p.education, p.education_score, 'education', '⬤')}}

            <div class="small-note">
              Each row has 10 symbols. Colored symbols show the selected postal-code area'srank compared with other Helsinki postal-code areas.
            </div>
        `;
    }});
}});

}}, 500);
</script>
"""

m.get_root().html.add_child(folium.Element(js))

# ---------------------------
# 9. Save
# ---------------------------
m.save("helsinki_postal_code_pictogram_map.html")