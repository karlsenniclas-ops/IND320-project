import pandas as pd
import plotly.express as px
import streamlit as st
from analysis import forecast_filling
from data import WEATHER_PROPERTIES, chosen_area, load_exchange_rates, load_weekly_weather, weekly_filling, weeks
from weather import region_id

st.title("Forecasting")

# The area comes from the sidebar (or the map)
area_type, area_number = chosen_area()
region = region_id(area_type, area_number)
area_label = area_type if area_type == "NO" else f"{area_type} {area_number}"

# Timeframe of the training data. It ends in the week chosen on the map (the same value in the session state,
# so the two pages are synced), and the number of years before it is chosen here
end = st.select_slider("End of training data", options=weeks(), value=st.session_state["week"])
st.session_state["week"] = end
years = st.slider("Years of training data", min_value=2, max_value=15, value=5)
start = pd.Timestamp(end) - pd.DateOffset(years=years)  # first week of the training data, for the downloads
horizon = st.slider("Forecast horizon (weeks)", min_value=4, max_value=52, value=26)

# SNARIMAX parameters. The defaults were the best in the tests in the part 4 notebook
cols = st.columns(7)
p = cols[0].number_input("p", min_value=0, max_value=5, value=1)
d = cols[1].number_input("d", min_value=0, max_value=2, value=1)
q = cols[2].number_input("q", min_value=0, max_value=5, value=1)
m = cols[3].number_input("m", min_value=1, max_value=104, value=52)
sp = cols[4].number_input("sp", min_value=0, max_value=3, value=1)
sd = cols[5].number_input("sd", min_value=0, max_value=1, value=1)
sq = cols[6].number_input("sq", min_value=0, max_value=3, value=1)

# Exogenous variables from open-meteo and Norges Bank
weather_vars = st.multiselect("Weather (open-meteo)", list(WEATHER_PROPERTIES), format_func=WEATHER_PROPERTIES.get)
currencies = st.multiselect("Exchange rates (Norges Bank)", ["EUR", "USD"])

# Weekly data for the area: degree of filling and the chosen exogenous variables on the same Sundays
last = pd.Timestamp(end) + pd.Timedelta(weeks=horizon)
data = weekly_filling(area_type, area_number).to_frame()
try:
    if weather_vars:
        weather = load_weekly_weather(region, start, last)
        data = data.join(weather[weather_vars])
    if currencies:
        rates = load_exchange_rates(start.year, last.year)
        data = data.join(rates.resample("W-SUN").mean()[currencies])
except Exception as error:
    st.error(f"Could not download the exogenous variables: {error}")
    st.stop()
data = data.asfreq("W-SUN")

result = forecast_filling(data, end, years=years, horizon=horizon, exog=weather_vars + currencies,
                          p=p, d=d, q=q, m=m, sp=sp, sd=sd, sq=sq)

# The values of the exogenous variables are needed for the forecast weeks too
if result.empty:
    st.warning("The exogenous variables are not known after the end of the training data. "
               "Choose an earlier end of the training data, or remove the exogenous variables.")
    st.stop()

# Animation: the last two years of training data, then the forecast and the observed filling one week at a time
history = data["fill_level"].loc[:end].iloc[-104:]
observed = result["observed"].dropna()
frames = []
for step in range(1, len(result) + 1):
    frame = pd.concat([
        pd.DataFrame({"date": history.index, "filling": history.values, "series": "Training data"}),
        pd.DataFrame({"date": observed.index[:step], "filling": observed.values[:step], "series": "Observed"}),
        pd.DataFrame({"date": result.index[:step], "filling": result["forecast"].values[:step], "series": "Forecast"}),
    ])
    frame["step"] = step  # week number after the training data
    frames.append(frame)
plot_df = pd.concat(frames)

fig = px.line(plot_df, x="date", y="filling", color="series", animation_frame="step", markers=True,
              range_x=[history.index[0], result.index[-1]], range_y=[0, 100],
              labels={"date": "Week", "filling": "Degree of filling (%)", "step": "Weeks ahead", "series": ""},
              title=f"Degree of filling, {area_label}")
st.plotly_chart(fig)
