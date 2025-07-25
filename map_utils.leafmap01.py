import geopandas as gpd
import pandas as pd
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import leafmap.foliumap as leafmap
import branca.colormap as bcm
import os
import folium
import streamlit as st  # needed for color_mode toggle

def load_data(filepath=os.path.join("data", "matched_districts.geojson")):
    return gpd.read_file(filepath)

def get_palette(palette_name="viridis", n_bins=6, reverse=False):
    cmap = cm.get_cmap(palette_name, n_bins)
    colors = [mcolors.rgb2hex(cmap(i)) for i in range(cmap.N)]
    return colors[::-1] if reverse else colors

def create_bins(values, n_bins=6, strategy="quantile"):
    values = values.dropna()
    if len(values.unique()) < 2:
        return [values.min(), values.max() + 0.001]

    if strategy == "quantile":
        q = min(n_bins, len(values.unique()))
        qcut = pd.qcut(values, q=q, duplicates="drop")
        bins = list(qcut.unique().categories.left)
        bins.append(values.max())
        return bins
    elif strategy == "uniform":
        q = min(n_bins, len(values.unique()))
        cut = pd.cut(values, bins=q, duplicates="drop")
        return list(cut.unique().categories.left) + [values.max()]
    else:
        raise ValueError("Unsupported binning strategy")

def create_map(gdf, column="ActualNSS_portion_ReqNSS", palette="viridis", reverse=False, bins=None):
    m = leafmap.Map(center=[42.1, -71.5], zoom=8, tiles="CartoDB.PositronNoLabels", draw_control=False, measure_control=False)

    # Inject CSS override to force legend top right
    legend_css = '''
    <style>
      .legend {
        position: absolute !important;
        top: 10px !important;
        right: 10px !important;
        z-index: 9999;
        background: white;
        border-radius: 6px;
        padding: 10px;
        box-shadow: 0 0 5px rgba(0,0,0,0.3);
      }
    </style>
    '''
    m.add_html(legend_css, position="topright")

    values = gdf[column].dropna()

    if bins is None:
        if st.session_state.get("color_mode") == "absolute":
            bins = [1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
        else:
            bins = create_bins(values, n_bins=6)

    num_colors = max(len(bins) - 1, 1)
    colors = get_palette(palette, n_bins=num_colors, reverse=reverse)

    labels = [f"{round(bins[i]*100)}% - {round(bins[i+1]*100)}%" for i in range(len(bins) - 1)]
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

    m.add_legend(
        title="Actual NSS / Required NSS",
        colors=colors,
        labels=labels,
        position="topright"
    )
    return m
