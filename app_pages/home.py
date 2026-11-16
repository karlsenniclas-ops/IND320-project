import streamlit as st

st.title("Home")
st.write("Use the sidebar menu to navigate between the pages:")
st.write("- **Map**: price areas and water areas coloured by degree of filling or a weather property. Click an area to choose it for the other pages.")
st.write("- **Data overview**: weekly reservoir data from the NVE API as a plot and a table. Choose area type and download period in the sidebar.")
st.write("- **STL and Spectrogram**: seasonal decomposition and spectrogram of the degree of filling for one area.")
st.write("- **Sliding Window Correlation**: correlation between a weather property and the weekly change in filling, with lag and window length.")
st.write("- **Transfers**: cross-border electricity flows between Norway and its neighbours, from ENTSO-E via MongoDB.")
st.write("- **Outliers and Anomalies**: ERA5 weather data from open-meteo for the chosen area, with SPC outliers and LOF anomalies for the chosen weather property.")
st.write("- **Forecasting**: forecast of the degree of filling with River's SNARIMAX, with weather and exchange rates from Norges Bank as exogenous variables.")
