import streamlit as st
from data import AREA_NUMBERS, WEATHER_PROPERTIES, month_options, weeks

# st.navigation shows these pages as a sidebar menu, grouped by the type of task (see the sketch in the
# part 4 notebook). The page files are in the app_pages folder
PAGES = {
    "Overview": [
        st.Page("app_pages/home.py", title="Home", default=True),
        st.Page("app_pages/map.py", title="Map"),
        st.Page("app_pages/overview.py", title="Data overview"),
    ],
    "Exploratory": [
        st.Page("app_pages/stl_spectrogram.py", title="STL and Spectrogram"),
        st.Page("app_pages/correlation.py", title="Sliding Window Correlation"),
        st.Page("app_pages/transfers.py", title="Transfers"),
    ],
    "Anomalies": [
        st.Page("app_pages/outliers.py", title="Outliers and Anomalies"),
    ],
    "Predictive": [
        st.Page("app_pages/forecast.py", title="Forecasting"),
    ],
}

# One colour per group, shown above the page to emphasise which group is active
GROUP_COLOURS = {"Overview": "gray", "Exploratory": "blue", "Anomalies": "orange", "Predictive": "green"}

pg = st.navigation(PAGES)

# Selections shared by the pages through the session state, with their default values
months = month_options()
DEFAULTS = {
    "area_type": "NO",
    "area_number": 0,
    "period": (months[-60], months[-1]),
    "weather_property": "temperature_2m",
    "week": weeks()[-1],
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Pages that use the shared selections in the sidebar
AREA_TYPE_PAGES = ["Data overview", "STL and Spectrogram", "Sliding Window Correlation", "Outliers and Anomalies", "Forecasting"]
AREA_NUMBER_PAGES = ["STL and Spectrogram", "Sliding Window Correlation", "Outliers and Anomalies", "Forecasting"]
PERIOD_PAGES = ["Data overview", "STL and Spectrogram", "Sliding Window Correlation"]
WEATHER_PAGES = ["Sliding Window Correlation", "Outliers and Anomalies"]

# The widgets start at the value in the session state and save the choice there, so all pages use the same choice.
# The widgets are made here (not inside a page file) so they are the same on all pages
if pg.title in AREA_TYPE_PAGES:
    types = ["EL", "NO", "VASS"]
    st.session_state["area_type"] = st.sidebar.radio(
        "Area type", types, index=types.index(st.session_state["area_type"]), horizontal=True)

# The area number must exist for the area type. NO has only area number 0, so there is nothing to choose
numbers = AREA_NUMBERS[st.session_state["area_type"]]
if st.session_state["area_number"] not in numbers:
    st.session_state["area_number"] = numbers[0]
if pg.title in AREA_NUMBER_PAGES and len(numbers) > 1:
    st.session_state["area_number"] = st.sidebar.selectbox(
        "Area number", numbers, index=numbers.index(st.session_state["area_number"]))

if pg.title in PERIOD_PAGES:
    st.session_state["period"] = st.sidebar.select_slider("Download period", options=months, value=st.session_state["period"])

if pg.title in WEATHER_PAGES:
    props = list(WEATHER_PROPERTIES)
    st.session_state["weather_property"] = st.sidebar.selectbox(
        "Weather property", props, index=props.index(st.session_state["weather_property"]), format_func=WEATHER_PROPERTIES.get)

# Coloured label with the active group
group = [name for name, pages in PAGES.items() if pg in pages][0]
st.badge(group, color=GROUP_COLOURS[group])

pg.run()
