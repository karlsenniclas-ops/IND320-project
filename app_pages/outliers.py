import streamlit as st
from analysis import lof_anomalies, spc_outliers
from data import WEATHER_PROPERTIES, chosen_area, load_weather
from weather import region_id

st.title("Outliers and Anomalies")

# The area and the weather property come from the sidebar (or the map), shared with the other pages
area_type, area_number = chosen_area()
region = region_id(area_type, area_number)
area_label = area_type if area_type == "NO" else f"{area_type} {area_number}"
prop = st.session_state["weather_property"]
label = WEATHER_PROPERTIES[prop]

# The year is chosen here, since the weather data is downloaded for a whole year at a time
years = list(range(2025, 1999, -1))
year = st.selectbox("Year", years, index=years.index(2024))

st.write(f"ERA5 weather for {area_label} (region {region}), {year}, averaged over the sampled locations.")

try:
    weather = load_weather(region, year)
except Exception as error:
    # For example when open-meteo's hourly or daily limit is reached
    st.error(f"Could not download weather data from open-meteo: {error}")
    st.stop()

# The label with the unit is used as the name of the series in the plots
series = weather[prop].rename(label)

tab_spc, tab_lof = st.tabs(["Outliers (SPC)", "Anomalies (LOF)"])

with tab_spc:
    cutoff = st.slider("Cut-off frequency (cycles per year)", min_value=1, max_value=100, value=12)
    n_std = st.slider("Number of standard deviations", min_value=1.0, max_value=6.0, value=3.0, step=0.5)

    fig, outliers, summary = spc_outliers(series, cutoff, n_std)
    fig.update_layout(title=f"SPC outliers, {area_label}, {year}")
    st.plotly_chart(fig)

    # Summary of the outliers and the outlier hours
    st.dataframe(summary, hide_index=True)
    with st.expander("Outliers"):
        st.dataframe(outliers)

with tab_lof:
    # The proportion is chosen in percent
    contamination = st.slider("Proportion of outliers (%)", min_value=0.1, max_value=10.0, value=1.0, step=0.1) / 100

    fig, anomalies, summary = lof_anomalies(series, contamination)
    fig.update_layout(title=f"LOF anomalies, {area_label}, {year}")
    st.plotly_chart(fig)

    # Summary of the anomalies and the anomaly hours
    st.dataframe(summary, hide_index=True)
    with st.expander("Anomalies"):
        st.dataframe(anomalies)

with st.expander("Data source"):
    st.write(
        "Hourly ERA5 reanalysis from open-meteo (UTC). 1000 locations were sampled at random inside each area "
        "from NVE's price area and region polygons. ERA5 has one value per 0.25 degree grid cell, so each cell is "
        "downloaded once and weighted by the number of sampled locations in it. The app uses 200 of the 1000 "
        "locations to keep the download at a minute or two."
    )
