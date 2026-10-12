import pandas as pd
import streamlit as st
from data import VALUE_COLUMNS, load_reservoirs

st.title("Table")

# Area type and period come from the sidebar widgets in app.py
area_type = st.session_state["area_type"]
start_month, end_month = st.session_state["period"]

df = load_reservoirs(start_month, end_month)
df = df[df["area_type"] == area_type]

if df.empty:
    st.warning("No data in the chosen period, try a wider period.")
    st.stop()

st.write(f"Weekly values for {area_type}, {start_month} to {end_month}. One row per area number.")

# One row per area number, each cell holds the weekly values as a list so LineChartColumn can draw it
rows = []
for number, area_df in df.groupby("area_number"):
    # NO has only area number 0, so just show "NO" there
    row = {"area": area_type if area_type == "NO" else f"{area_type} {number}"}
    for col in VALUE_COLUMNS:
        row[col] = area_df[col].tolist()
    rows.append(row)

table_data = pd.DataFrame(rows)

st.dataframe(
    table_data,
    hide_index=True,
    column_config={col: st.column_config.LineChartColumn(col) for col in VALUE_COLUMNS},
)
