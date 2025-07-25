# app.py
import streamlit as st
from map_utils import load_data, create_map
import leafmap.foliumap as leafmap
import time

st.set_page_config(layout="wide")
st.markdown(
    "<p style='font-size:1.25rem; margin-top:0.5rem; margin-bottom:0.5rem;'>"
    "Massachusetts School Finance Explorer"
    "</p>",
    unsafe_allow_html=True
)


@st.cache_data
def get_data():
    gdf = load_data()
    gdf["geometry"] = gdf["geometry"].simplify(0.001)
    return gdf

gdf = get_data()

# --- Set up sidebar controls ---
years = sorted(gdf["FY"].dropna().unique())
years_desc = sorted(gdf["FY"].dropna().unique(), reverse=True)      # for dropdown
years_asc = sorted(years_desc)  # for animation order
group_options = sorted([g for g in gdf["GroupType"].dropna().unique() if g != "Other"])
palettes = ["viridis", "cividis", "plasma", "inferno", "magma"]

# Session state setup
if "year_index" not in st.session_state:
    st.session_state.year_index = years.index(2025) if 2025 in years else 0
if "play" not in st.session_state:
    st.session_state.play = False
if "color_mode" not in st.session_state:
    st.session_state.color_mode = "absolute"

# Sidebar: animation toggle
st.sidebar.markdown("Animate map")
## if st.sidebar.button("\u25B6 Start" if not st.session_state.play else "\u23F8 Stop"):
##    st.session_state.play = not st.session_state.play
clicked = st.sidebar.button("\u25B6 Start" if not st.session_state.play else "\u23F8 Stop")
if clicked:
    st.session_state.play = not st.session_state.play
    st.session_state.animate_next = st.session_state.play

# Sidebar: year selector
# Determine current year for display and filtering
current_year = years_asc[st.session_state.year_index]

# Always show dropdown; update its selection based on current year
selected_year = st.sidebar.selectbox(
    "Select fiscal year", years_desc,
    index=years_desc.index(current_year)
)

# If not playing, sync year_index to manual selection
if not st.session_state.play:
    st.session_state.year_index = years_asc.index(selected_year)


# Sidebar: group types
default_groups = [g for g in group_options if g in ["Districts", "Unified Regions"]]
selected_groups = st.sidebar.multiselect("Group types", group_options, default=default_groups)

# Sidebar: color mode
st.session_state.color_mode = st.sidebar.radio(
    "Choose color scale:", ["relative", "absolute"],
    index=1 if st.session_state.color_mode == "absolute" else 0,
    horizontal=True
)

# Sidebar: palette and color scale
selected_palette = st.sidebar.selectbox("Color palette", palettes)
reverse_palette = st.sidebar.checkbox("Reverse palette")

# --- Filter data ---
filtered = gdf[
    (gdf["FY"] == selected_year) &
    (gdf["GroupType"].isin(selected_groups))
]

st.subheader(f"Fiscal year: {selected_year}")

if filtered.empty:
    st.warning("No data matches your selection.")
else:
    try:
        m = create_map(
            gdf=filtered,
            column="ActualNSS_portion_ReqNSS",
            palette=selected_palette,
            reverse=reverse_palette,
        )
        m.to_streamlit(height=700)
    except Exception as e:
        st.error(f"Error rendering map: {e}")

# Auto-play animation loop
if st.session_state.play:
    st.session_state.year_index = (st.session_state.year_index + 1) % len(years_asc)
    time.sleep(1.0)
    st.rerun()
