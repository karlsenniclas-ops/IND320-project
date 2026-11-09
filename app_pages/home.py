import streamlit as st

st.title("Home")
st.write("Use the sidebar menu to navigate between the pages:")
st.write("- **Table** and **Plot**: weekly reservoir data from the NVE API. Choose area type and download period in the sidebar.")
st.write("- **STL and Spectrogram**: seasonal decomposition and spectrogram of the degree of filling for one area.")
st.write("- **Outliers and Anomalies**: ERA5 weather data from open-meteo for the chosen area, with outliers in precipitation and anomalies in temperature.")
st.write("- **Transfers**: cross-border electricity flows between Norway and its neighbours, from ENTSO-E via MongoDB.")
