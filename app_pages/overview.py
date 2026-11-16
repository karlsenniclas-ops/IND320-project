import pandas as pd
import plotly.express as px
import streamlit as st
from data import VALUE_COLUMNS, load_reservoirs

st.title("Data overview")

# Units per column, used as y axis labels
UNITS = {
    "fill_level": "Share of capacity",
    "capacity_twh": "TWh",
    "stored_energy_twh": "TWh",
    "fill_level_prev_week": "Share of capacity",
    "fill_level_change": "Change in share of capacity",
}

# Area type and period come from the sidebar widgets in app.py
area_type = st.session_state["area_type"]
start_month, end_month = st.session_state["period"]

df = load_reservoirs(start_month, end_month)
df = df[df["area_type"] == area_type]

if df.empty:
    st.warning("No data in the chosen period, try a wider period.")
    st.stop()

# Label for each line, e.g. EL 1 to EL 5 (NO only has area number 0)
df = df.assign(area=area_type if area_type == "NO" else area_type + " " + df["area_number"].astype(str))

tab_plot, tab_table = st.tabs(["Plot", "Table"])

with tab_plot:
    column_choice = st.selectbox("Column", VALUE_COLUMNS)
    fig = px.line(df, x="date", y=column_choice, color="area",
                  title=f"{column_choice}, {area_type}, {start_month} to {end_month}")
    fig.update_xaxes(title="Date")
    fig.update_yaxes(title=UNITS[column_choice])
    st.plotly_chart(fig)

with tab_table:
    # One row per area, each cell holds the weekly values as a list so LineChartColumn can draw it
    rows = []
    for area, area_df in df.groupby("area"):
        row = {"area": area}
        for col in VALUE_COLUMNS:
            row[col] = area_df[col].tolist()
        rows.append(row)

    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        column_config={col: st.column_config.LineChartColumn(col) for col in VALUE_COLUMNS},
    )
