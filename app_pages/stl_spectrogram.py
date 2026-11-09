import streamlit as st
from analysis import spectrogram_plot, stl_decomposition
from data import chosen_area, load_reservoirs

st.title("STL and Spectrogram")

# Area type and period come from the sidebar widgets in app.py, together with the area number
area_type, area_number = chosen_area()
start_month, end_month = st.session_state["period"]
area_label = area_type if area_type == "NO" else f"{area_type} {area_number}"

df = load_reservoirs(start_month, end_month)
df = df[(df["area_type"] == area_type) & (df["area_number"] == area_number)]

if df.empty:
    st.warning("No data in the chosen period, try a wider period.")
    st.stop()

# One value per week, with the date as index
series = df.set_index("date")["fill_level"]
st.write(f"Degree of filling for {area_label}, {start_month} to {end_month} ({len(series)} weeks).")

tab_stl, tab_spectrogram = st.tabs(["STL", "Spectrogram"])

with tab_stl:
    # LOESS smoothers must be odd numbers, and the trend smoother must be larger than the period of 52 weeks
    seasonal = st.slider("Seasonal smoother", min_value=3, max_value=51, value=7, step=2)
    trend = st.slider("Trend smoother", min_value=53, max_value=301, value=101, step=2)
    robust = st.checkbox("Robust fitting", value=False)

    if len(series) < 2 * 52:
        st.warning("STL works best with at least two years of data. Choose a longer period in the sidebar.")

    st.pyplot(stl_decomposition(series, seasonal=seasonal, trend=trend, robust=robust))

with tab_spectrogram:
    window_length = st.slider("Window length (weeks)", min_value=13, max_value=260, value=52)
    # The overlap must be smaller than the window, default is half the window
    window_overlap = st.slider("Window overlap (weeks)", min_value=0, max_value=window_length - 1, value=window_length // 2)

    if window_length > len(series):
        st.warning("The window is longer than the data. Choose a shorter window or a longer period in the sidebar.")
    else:
        st.pyplot(spectrogram_plot(series, window_length=window_length, window_overlap=window_overlap))
