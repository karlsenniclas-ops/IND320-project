import pandas as pd
import streamlit as st
from analysis import sliding_window_correlation
from data import WEATHER_PROPERTIES, chosen_area, download_reservoirs, load_weekly_weather
from weather import region_id

st.title("Sliding Window Correlation")

# Area, period and weather property come from the sidebar (or the map)
area_type, area_number = chosen_area()
region = region_id(area_type, area_number)
prop = st.session_state["weather_property"]
start_month, end_month = st.session_state["period"]
start = pd.Period(start_month).start_time
end = pd.Period(end_month).end_time

# The weekly change in the degree of filling is used from the magasinstatistikk, since the weather
# should affect how much the filling goes up or down in a week
df = download_reservoirs()
df = df[(df["area_type"] == area_type) & (df["area_number"] == area_number)]
change = (df.set_index("date")["fill_level_change"] * 100).rename("Change in filling (percentage points)")

try:
    weather = load_weekly_weather(region, start, end)
except Exception as error:
    st.error(f"Could not download weather data from open-meteo: {error}")
    st.stop()

# Weekly weather and change in filling on the same Sundays
data = pd.concat([weather[prop].rename(WEATHER_PROPERTIES[prop]), change], axis=1, join="inner")

lag = st.slider("Lag (weeks)", min_value=0, max_value=52, value=0)
window = st.slider("Window length (weeks)", min_value=5, max_value=104, value=26)

if window > len(data):
    st.warning("The window is longer than the data. Choose a shorter window or a longer period in the sidebar.")
    st.stop()

st.plotly_chart(sliding_window_correlation(data.iloc[:, 0], data.iloc[:, 1], window=window, lag=lag))
