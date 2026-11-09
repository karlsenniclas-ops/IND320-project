import streamlit as st
from data import AREA_NUMBERS, month_options

# st.navigation shows these pages as a sidebar menu, grouped by data source. The page files are in the app_pages folder
pg = st.navigation({
    "Overview": [
        st.Page("app_pages/home.py", title="Home", default=True),
    ],
    "Reservoirs": [
        st.Page("app_pages/table.py", title="Table"),
        st.Page("app_pages/plot.py", title="Plot"),
        st.Page("app_pages/stl_spectrogram.py", title="STL and Spectrogram"),
    ],
    "Weather": [
        st.Page("app_pages/outliers.py", title="Outliers and Anomalies"),
    ],
    "Electricity flows": [
        st.Page("app_pages/transfers.py", title="Transfers"),
    ],
})

# Pages that use the area type, the download period and one area number. The weather page uses the same area
# as the reservoir pages, since the downloaded weather data follows the area chosen for the reservoirs
AREA_TYPE_PAGES = ["Table", "Plot", "STL and Spectrogram", "Outliers and Anomalies"]
PERIOD_PAGES = ["Table", "Plot", "STL and Spectrogram"]
AREA_NUMBER_PAGES = ["STL and Spectrogram", "Outliers and Anomalies"]

# The widgets are made here (not inside a page file) so they keep their value when switching between pages
if pg.title in AREA_TYPE_PAGES:
    st.sidebar.radio("Area type", ["EL", "NO", "VASS"], index=1, horizontal=True, key="area_type")

# STL, spectrogram and weather need a single area. NO has only area number 0, so there is nothing to choose
if pg.title in AREA_NUMBER_PAGES and len(AREA_NUMBERS[st.session_state["area_type"]]) > 1:
    st.sidebar.selectbox("Area number", AREA_NUMBERS[st.session_state["area_type"]], key="area_number")

if pg.title in PERIOD_PAGES:
    # The period decides which weeks are used, default is the last two years
    months = month_options()
    st.sidebar.select_slider(
        "Download period",
        options=months,
        value=(months[-24], months[-1]),
        key="period",
    )

pg.run()
