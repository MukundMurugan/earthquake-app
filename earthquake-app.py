import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import pytz
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# -----------------------------------------------
# Region keywords for filtering
REGION_KEYWORDS = {
    "Asia": ["China", "Japan", "India", "Indonesia", "Philippines", "Nepal", "Turkey", "Iran", "Pakistan"],
    "North America": ["California", "Alaska", "Mexico", "USA", "Hawaii", "Canada"],
    "South America": ["Chile", "Peru", "Argentina", "Ecuador", "Colombia", "Bolivia"],
    "Europe": ["Italy", "Greece", "Romania", "Spain", "Iceland", "Portugal", "France"],
    "Africa": ["Morocco", "Tanzania", "Ethiopia", "South Africa", "Algeria", "Egypt"],
    "Oceania": ["New Zealand", "Australia", "Papua", "Fiji", "Samoa"],
    "Middle East": ["Iran", "Iraq", "Syria", "Israel", "Saudi Arabia", "Jordan", "Lebanon"],
    "Pacific Ocean": ["Pacific", "Tonga", "Vanuatu", "Kermadec", "Solomon", "Guam"]
}

# -----------------------------------------------
# Fetch Earthquake Data
def fetch_earthquake_data(url):
    response = requests.get(url)
    data = response.json()
    features = data['features']
    earthquakes = []

    for feature in features:
        properties = feature['properties']
        geometry = feature['geometry']
        utc_time = pd.to_datetime(properties['time'], unit='ms')
        local_time = utc_time.tz_localize('UTC').tz_convert(pytz.timezone('America/Los_Angeles'))

        earthquakes.append({
            "place": properties['place'],
            "magnitude": properties['mag'],
            "time_utc": utc_time,
            "time_local": local_time,
            "latitude": geometry['coordinates'][1],
            "longitude": geometry['coordinates'][0]
        })

    return pd.DataFrame(earthquakes)

# -----------------------------------------------
# Sidebar controls
st.sidebar.title("Earthquake Filter Options")
min_magnitude = st.sidebar.slider("Minimum Magnitude", 0.0, 10.0, 1.0, 0.1)
selected_regions = st.sidebar.multiselect("Select Region(s):", list(REGION_KEYWORDS.keys()))
location_keyword = st.sidebar.text_input("Keyword Search (e.g. Japan, Alaska)")

# -----------------------------------------------
# Fetch data
st.title("🌍 Real-Time Earthquake Monitoring Web App")
st.markdown("Live data from [USGS Earthquake API](https://earthquake.usgs.gov/) visualized with real-time updates and filters.")

realtime_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
historical_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"

realtime_data = fetch_earthquake_data(realtime_url)
historical_data = fetch_earthquake_data(historical_url)

# -----------------------------------------------
# Apply magnitude filter
realtime_data = realtime_data[realtime_data["magnitude"] >= min_magnitude]
historical_data = historical_data[historical_data["magnitude"] >= min_magnitude]

# -----------------------------------------------
# Apply region filter
def apply_region_filter(df):
    if not selected_regions:
        return df
    keywords = [term for region in selected_regions for term in REGION_KEYWORDS[region]]
    return df[df["place"].str.contains("|".join(keywords), case=False, na=False)]

realtime_data = apply_region_filter(realtime_data)
historical_data = apply_region_filter(historical_data)

# -----------------------------------------------
# Apply keyword search
if location_keyword:
    realtime_data = realtime_data[realtime_data["place"].str.contains(location_keyword, case=False, na=False)]
    historical_data = historical_data[historical_data["place"].str.contains(location_keyword, case=False, na=False)]

# -----------------------------------------------
# Real-time Earthquake Map
st.subheader("📍 Real-Time Earthquakes (Past Hour)")
fig_realtime = px.scatter_mapbox(
    realtime_data,
    lat="latitude",
    lon="longitude",
    size="magnitude",
    color="magnitude",
    hover_name="place",
    hover_data={"time_utc": True, "time_local": True},
    zoom=1,
    height=600
)
fig_realtime.update_layout(mapbox_style="open-street-map")
st.plotly_chart(fig_realtime)

# -----------------------------------------------
# Historical Earthquake Map
st.subheader("📌 Historical Earthquakes (Past Month)")
fig_historical = px.scatter_mapbox(
    historical_data,
    lat="latitude",
    lon="longitude",
    size="magnitude",
    color="magnitude",
    hover_name="place",
    hover_data={"time_utc": True, "time_local": True},
    zoom=1,
    height=600
)
fig_historical.update_layout(mapbox_style="open-street-map")
st.plotly_chart(fig_historical)

# -----------------------------------------------
# Heatmap
st.subheader("🔥 Earthquake Density Heatmap")
if not historical_data.empty:
    fig_heatmap = px.density_mapbox(
        historical_data,
        lat="latitude",
        lon="longitude",
        z="magnitude",
        radius=10,
        center={"lat": 0, "lon": 0},
        zoom=1,
        mapbox_style="open-street-map",
        height=600
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
else:
    st.info("No data available for heatmap.")

# -----------------------------------------------
# Clustering Map (Folium)
st.subheader("🧭 Earthquake Clustering Map")
if not historical_data.empty:
    m = folium.Map(location=[0, 0], zoom_start=2)
    cluster = MarkerCluster().add_to(m)
    for _, row in historical_data.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=f"<b>{row['place']}</b><br>Mag: {row['magnitude']}<br>{row['time_local']}"
        ).add_to(cluster)
    st_folium(m, width=1200, height=600)
else:
    st.info("No data available for clustering map.")

# -----------------------------------------------
# Time-lapse Animation
st.subheader("📽️ Earthquake Time-Lapse Animation")
if not historical_data.empty:
    historical_data["date"] = historical_data["time_local"].dt.date.astype(str)
    fig_animation = px.scatter_mapbox(
        historical_data,
        lat="latitude",
        lon="longitude",
        size="magnitude",
        color="magnitude",
        hover_name="place",
        hover_data={"time_local": True, "magnitude": True},
        animation_frame="date",
        zoom=1,
        height=700
    )
    fig_animation.update_layout(mapbox_style="open-street-map")
    fig_animation.update_layout(margin={"r":0, "t":40, "l":0, "b":0})
    st.plotly_chart(fig_animation)
else:
    st.info("No data available for animation.")

# -----------------------------------------------
# Data Tables
st.subheader("📋 Filtered Real-Time Earthquake Data")
st.write(realtime_data)

st.subheader("📋 Filtered Historical Earthquake Data")
st.write(historical_data)

# -----------------------------------------------
# Sidebar Info
st.sidebar.subheader("About This App")
st.sidebar.info("""
This dashboard monitors real-time and historical earthquakes using USGS data.
Features include:
- Real-time map
- Filters by magnitude, region, keyword
- Heatmap, cluster map, time-lapse animation
""")
