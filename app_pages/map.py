import folium
import pandas as pd
import streamlit as st
from shapely.geometry import Point, shape
from streamlit_folium import st_folium
from data import WEATHER_PROPERTIES, download_reservoirs, load_geojson, load_weekly_weather, weeks
from weather import region_id

st.title("Map")

# Price areas are EL 1-5 and water areas VASS 1-3 in the magasinstatistikk, both coloured by degree of filling.
# The weather property is shown for the price areas
colour_by = st.radio("Colour by", ["Price area", "Water area", "Weather property"], horizontal=True)
if colour_by == "Weather property":
    props = list(WEATHER_PROPERTIES)
    prop = st.selectbox("Weather property", props, index=props.index(st.session_state["weather_property"]),
                        format_func=WEATHER_PROPERTIES.get)
    st.session_state["weather_property"] = prop  # shared with the other pages

area_type = "VASS" if colour_by == "Water area" else "EL"
geojson = load_geojson("water_areas" if area_type == "VASS" else "price_areas")

# The week is shared with the forecasting page, where it is the end of the training data
week = st.select_slider("Week", options=weeks(), value=st.session_state["week"])
st.session_state["week"] = week

# Value for each area in the chosen week
if colour_by == "Weather property":
    # Weather aggregated over the same week as the reservoir data
    rows = []
    for feature in geojson["features"]:
        number = feature["properties"]["area_number"]
        try:
            weekly = load_weekly_weather(region_id(area_type, number), week, week)
        except Exception as error:
            st.error(f"Could not download weather data from open-meteo: {error}")
            st.stop()
        if weekly.empty:
            st.warning("No weather data for this week yet (ERA5 is about 5 days behind). Choose an earlier week.")
            st.stop()
        rows.append({"area_number": number, "value": weekly[prop].iloc[0]})
    values = pd.DataFrame(rows)
    legend = WEATHER_PROPERTIES[prop]
else:
    df = download_reservoirs()
    df = df[(df["area_type"] == area_type) & (df["date"].dt.date == week)]
    values = pd.DataFrame({"area_number": df["area_number"], "value": df["fill_level"] * 100})
    legend = "Degree of filling (%)"

# Outlines of the areas as shapely polygons, used to find the area of a click (as in the lecture's example)
polygons = [(f["properties"]["area_number"], shape(f["geometry"])) for f in geojson["features"]]

m = folium.Map(location=[65, 14], zoom_start=4, tiles="OpenStreetMap")

# Transparent colours and outlines for all areas
folium.Choropleth(
    geo_data=geojson,
    data=values,
    columns=["area_number", "value"],
    key_on="feature.properties.area_number",
    fill_color="YlGnBu",
    fill_opacity=0.5,
    line_color="black",
    line_opacity=0.8,
    legend_name=legend,
).add_to(m)

# Thick red outline around the chosen area
if st.session_state["area_type"] == area_type:
    chosen = [f for f in geojson["features"] if f["properties"]["area_number"] == st.session_state["area_number"]]
    folium.GeoJson(
        {"type": "FeatureCollection", "features": chosen},
        style_function=lambda f: {"fillOpacity": 0, "color": "red", "weight": 4},
    ).add_to(m)

out = st_folium(m, key="map", height=600, width=None)

# A new click inside an area chooses it for the other pages. The map keeps returning the last click,
# so it is saved to only react once to each click
if out and out.get("last_clicked") and out["last_clicked"] != st.session_state.get("last_click"):
    st.session_state["last_click"] = out["last_clicked"]
    point = Point(out["last_clicked"]["lng"], out["last_clicked"]["lat"])
    for number, polygon in polygons:
        if polygon.covers(point):
            st.session_state["area_type"] = area_type
            st.session_state["area_number"] = number
            st.rerun()
