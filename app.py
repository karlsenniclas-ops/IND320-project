import streamlit as st
from data import month_options

# st.navigation shows these pages as a sidebar menu, the page files are in the app_pages folder
pg = st.navigation([
    st.Page("app_pages/home.py", title="Home", default=True),
    st.Page("app_pages/table.py", title="Table"),
    st.Page("app_pages/plot.py", title="Plot"),
    st.Page("app_pages/transfers.py", title="Transfers"),
])

# Table and Plot show the same reservoir data, so area type and period are chosen once in the sidebar.
# Widgets made here (not inside a page file) keep their value when switching between the two pages
if pg.title in ["Table", "Plot"]:
    st.sidebar.radio("Area type", ["EL", "NO", "VASS"], index=1, horizontal=True, key="area_type")

    # The period decides which weeks are downloaded from the NVE API, default is the last two years
    months = month_options()
    st.sidebar.select_slider(
        "Download period",
        options=months,
        value=(months[-24], months[-1]),
        key="period",
    )

pg.run()
