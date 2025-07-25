import geopandas as gpd
import pandas as pd
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import leafmap.foliumap as leafmap
import branca.colormap as bcm
import os
import folium
import streamlit as st

def load_data(filepath=os.path.join("data", "matched_districts.geojson")):
    return gpd.read_file(filepath)

def get_palette(palette_name="viridis", n_bins=6, reverse=False):
    cmap = cm.get_cmap(palette_name, n_bins)
    colors = [mcolors.rgb2hex(cmap(i)) for i in range(cmap.N)]
    return colors[::-1] if reverse else colors

def create_map(gdf, column="ActualNSS_portion_ReqNSS", palette="viridis", reverse=False, bins=None):
    m = leafmap.Map(center=[42.1, -71.5], zoom=8, tiles="CartoDB.PositronNoLabels", draw_control=False, measure_control=False)

    values = gdf[column].dropna()

    if bins is None:
        if st.session_state.get("color_mode") == "absolute":
            bins = [0.0, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.01]
        else:
            # Relative mode: cap at 12 bins of width 0.25
            min_bin_width = 0.25
            max_bins = 12
            rounded_min = round(values.min() / min_bin_width) * min_bin_width
            rounded_max = round(values.max() / min_bin_width + 1) * min_bin_width
            num_bins = min(max_bins, int((rounded_max - rounded_min) / min_bin_width))
            bins = [rounded_min + i * min_bin_width for i in range(num_bins)]
            bins.append(values.max() + 0.001)

    num_colors = max(len(bins) - 1, 1)
    colors = get_palette(palette, n_bins=num_colors, reverse=reverse)

    labels = []
    for i in range(len(bins) - 1):
        low = round(bins[i] * 100)
        high = round(bins[i + 1] * 100)
        if i == 0:
            label = f"<= {high}%"
        elif i == len(bins) - 2:
            label = f">= {low}%"
        else:
            label = f"{low}% - {high}%"
        labels.append(label)

    colormap = bcm.StepColormap(colors=colors, index=bins, vmin=min(bins), vmax=max(bins))
    colormap.caption = "Actual NSS / Required NSS"

    def format_row(row, column):
        nss = f"{row[column] * 100:.1f}%" if pd.notnull(row[column]) else "N/A"
        fe = row.get("FE")
        fe_display = f"{int(fe):,}" if pd.notnull(fe) else "N/A"
        return (
            f"<b>District:</b> {row.get('DistOrg', 'N/A')}<br>"
            f"<b>Group Type:</b> {row.get('GroupType', 'N/A')}<br>"
            f"<b>NSS as % of Required:</b> {nss}<br>"
            f"<b>Foundation Enrollment:</b> {fe_display}"
        )

    gdf["TooltipHTML"] = gdf.apply(lambda row: format_row(row, column), axis=1)

    def style_function(feature):
        val = feature["properties"].get(column)
        return {
            "fillColor": colormap(val) if val is not None else "transparent",
            "color": "white",
            "weight": 0.5,
            "fillOpacity": 0.8,
        }

    tooltip = folium.GeoJsonTooltip(
        fields=["TooltipHTML"],
        aliases=[""],
        sticky=True,
        labels=False,
        style=(
            "background-color: white; color: black; font-size: 12px; "
            "padding: 6px; border-radius: 4px;"
        )
    )

    geojson = folium.GeoJson(
        data=gdf.__geo_interface__,
        style_function=style_function,
        tooltip=tooltip,
        name="School Finance"
    )
    geojson.add_to(m)

    legend_html = f'''<div class="legend" style="
        position: absolute; top: 10px; right: 10px; z-index:9999; background: white; 
        padding: 10px; border-radius: 5px; box-shadow: 0 0 6px rgba(0,0,0,0.3); font-size: 13px; min-width: 180px;">
        <b>Actual NSS / Required NSS</b><br>
        {''.join(f'<div><span style="background:{color};display:inline-block;width:12px;height:12px;margin-right:6px;"></span>{label}</div>' for color, label in zip(colors, labels))}
    </div>'''

    m.add_html(legend_html, position="topright")
    return m
