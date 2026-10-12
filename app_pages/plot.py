import matplotlib.pyplot as plt
import streamlit as st
from data import VALUE_COLUMNS, load_reservoirs

st.title("Plot")

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

column_choice = st.selectbox("Column", VALUE_COLUMNS)

fig, ax = plt.subplots()

# One line per area number, e.g. EL 1 to EL 5
for number, area_df in df.groupby("area_number"):
    label = area_type if area_type == "NO" else f"{area_type} {number}"
    ax.plot(area_df["date"], area_df[column_choice], label=label)

ax.set_xlabel("Date")
ax.set_ylabel(UNITS[column_choice])
ax.set_title(f"{column_choice}, {area_type}, {start_month} to {end_month}")
ax.legend()
fig.autofmt_xdate()

st.pyplot(fig)
