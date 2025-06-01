import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import pytz

st.set_page_config(layout="wide", page_title="Earthquake Monitoring")

# Caching to improve performance
@st.cache_data(ttl=3600)
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

# URLs for USGS feeds
realtime_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
historical_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"

# Fetch data
realtime_earthquake_data = fetch_earthquake_data(realtime_url)
historical_earthquake_data = fetch_earthquake_data(historical_url)

# Title and Description
st.title("🌍 Real-Time Earthquake Monitoring Webapp")
st.markdown("Visualizing real-time and historical earthquake data from the US Geological Survey (USGS).")

# Sidebar Info
st.sidebar.subheader("About This App")
st.sidebar.info(
    """
    This app fetches real-time and historical seismic data from USGS.
    You can filter by magnitude, explore earthquake trends, and download data.
    """
)

# Filter by Magnitude
min_magnitude = st.slider("Minimum Magnitude", 0.0, 10.0, 1.0, 0.1)
filtered_realtime_data = realtime_earthquake_data[realtime_earthquake_data["magnitude"] >= min_magnitude]
filtered_historical_data = historical_earthquake_data[historical_earthquake_data["magnitude"] >= min_magnitude]

# High-Magnitude Alert
high_mag = filtered_realtime_data[filtered_realtime_data["magnitude"] >= 5.0]
if not high_mag.empty:
    st.sidebar.warning("⚠️ High-magnitude earthquakes detected!")
    st.sidebar.dataframe(high_mag[["place", "magnitude", "time_local"]])

# Plot Real-time Earthquakes
fig_realtime = px.scatter_mapbox(
    filtered_realtime_data,
    lat="latitude",
    lon="longitude",
    size="magnitude",
    color="magnitude",
    hover_name="place",
    hover_data={"time_utc": True, "time_local": True, "magnitude": True},
    zoom=1,
    height=600,
    title="🟠 Recent Earthquakes (Last Hour)"
)
fig_realtime.update_layout(mapbox_style="open-street-map")

# Plot Historical Earthquakes
fig_historical = px.scatter_mapbox(
    filtered_historical_data,
    lat="latitude",
    lon="longitude",
    size="magnitude",
    color="magnitude",
    hover_name="place",
    hover_data={"time_utc": True, "time_local": True, "magnitude": True},
    zoom=1,
    height=600,
    title="🔵 Historical Earthquakes (Last Month)"
)
fig_historical.update_layout(mapbox_style="open-street-map")

# Display maps side-by-side
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_realtime, use_container_width=True)
with col2:
    st.plotly_chart(fig_historical, use_container_width=True)

# Histogram of magnitudes
st.subheader("📊 Magnitude Distribution (Last Month)")
fig_hist = px.histogram(
    filtered_historical_data,
    x="magnitude",
    nbins=30,
    title="Histogram of Earthquake Magnitudes"
)
st.plotly_chart(fig_hist, use_container_width=True)

# Earthquakes per Day
st.subheader("📈 Earthquakes Per Day")
historical_data_daily = filtered_historical_data.copy()
historical_data_daily['date'] = historical_data_daily['time_local'].dt.date
counts_per_day = historical_data_daily.groupby('date').size().reset_index(name='count')
fig_daily = px.line(counts_per_day, x='date', y='count', markers=True, title="Earthquakes Per Day")
st.plotly_chart(fig_daily, use_container_width=True)

# Download buttons
st.subheader("⬇️ Download Filtered Data")
col3, col4 = st.columns(2)
with col3:
    st.download_button(
        "Download Real-Time Data as CSV",
        filtered_realtime_data.to_csv(index=False),
        "filtered_realtime_earthquakes.csv",
        "text/csv"
    )
with col4:
    st.download_button(
        "Download Historical Data as CSV",
        filtered_historical_data.to_csv(index=False),
        "filtered_historical_earthquakes.csv",
        "text/csv"
    )

# Raw Data Tables
st.subheader("📄 Filtered Real-Time Earthquake Data")
st.dataframe(filtered_realtime_data)

st.subheader("📄 Filtered Historical Earthquake Data")
st.dataframe(filtered_historical_data)
