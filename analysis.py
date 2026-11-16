import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from river import time_series
from scipy import stats
from scipy.fft import dct, idct
from scipy.signal import stft
from sklearn.neighbors import LocalOutlierFactor
from statsmodels.tsa.seasonal import STL

# Primary colour of the app theme (.streamlit/config.toml). Plotly express uses the theme by itself,
# but lines made with graph_objects get Plotly's own colours, so they are given this colour
THEME_COLOUR = "#1f6f8b"

# All functions are cached with st.cache_data, so they only run again when the inputs change


@st.cache_data(show_spinner=False)
def spc_outliers(series, cutoff=12, n_std=3):
    """Outliers in an hourly series with Statistical Process Control (SPC).

    A DCT high-pass filter removes all frequencies below cutoff (cycles per year). What is left is the
    seasonally adjusted variation (SATV). The boundaries are the median of the SATV +/- n_std robust
    standard deviations (1.4826 * MAD) for the whole period. Returns the plot, the outliers and a summary.
    """
    values = series.values
    N = len(values)

    # Frequency axis in cycles per year. One hour is 1/(365*24) year (2* because of the DCT definition)
    dt = 1 / (365 * 24)
    W = np.linspace(0, 1 / (2 * dt), N)

    # High-pass filter: remove the low frequencies and transform back to get the SATV
    fourier_signal = dct(values, type=1, norm="forward")
    fourier_signal[W < cutoff] = 0
    satv = idct(fourier_signal, type=1, norm="forward")
    trend = values - satv  # the slow variation that was removed

    # Robust statistics of the SATV
    median = np.median(satv)
    sd = 1.4826 * stats.median_abs_deviation(satv)

    # The boundaries follow the slow variation, so they can be drawn on top of the original series
    upper = trend + median + n_std * sd
    lower = trend + median - n_std * sd
    is_outlier = (values > upper) | (values < lower)

    fig = go.Figure()
    fig.add_scatter(x=series.index, y=values, mode="lines", line=dict(width=1, color=THEME_COLOUR), name=series.name)
    fig.add_scatter(x=series.index, y=upper, mode="lines", line=dict(color="gray", dash="dash"), name="SPC boundaries")
    fig.add_scatter(x=series.index, y=lower, mode="lines", line=dict(color="gray", dash="dash"), showlegend=False)
    fig.add_scatter(x=series.index[is_outlier], y=values[is_outlier], mode="markers",
                    marker=dict(color="red", size=5), name="Outliers")
    fig.update_layout(title="SPC outliers", xaxis_title="Time", yaxis_title=series.name)

    outliers = series[is_outlier]
    summary = pd.DataFrame({
        "outliers": [is_outlier.sum()],
        "share (%)": [100 * is_outlier.mean()],
        "SATV median": [median],
        "SATV robust SD": [sd],
    })
    return fig, outliers, summary


@st.cache_data(show_spinner=False)
def lof_anomalies(series, contamination=0.01, step_size=0.005):
    """Anomalies in an hourly series with the Local Outlier Factor (LOF).

    As in the lecture notes, the observation number (times step_size) is used as a second column,
    so the anomalies are local in time. contamination is the proportion of outliers.
    Returns the plot, the anomalies and a summary.
    """
    values = series.values
    N = len(values)
    data2D = np.array([values, np.linspace(0, N * step_size, N)]).T

    lof = LocalOutlierFactor(n_neighbors=20, contamination=contamination)
    is_anomaly = lof.fit_predict(data2D) == -1  # -1 is an outlier

    fig = go.Figure()
    fig.add_scatter(x=series.index, y=values, mode="lines", line=dict(width=1, color=THEME_COLOUR), name=series.name)
    fig.add_scatter(x=series.index[is_anomaly], y=values[is_anomaly], mode="markers",
                    marker=dict(color="red", size=5), name="Anomalies")
    fig.update_layout(title="LOF anomalies", xaxis_title="Time", yaxis_title=series.name)

    anomalies = series[is_anomaly]
    summary = pd.DataFrame({
        "anomalies": [is_anomaly.sum()],
        "share (%)": [100 * is_anomaly.mean()],
        "lowest": [anomalies.min()],
        "highest": [anomalies.max()],
    })
    return fig, anomalies, summary


@st.cache_data(show_spinner=False)
def stl_decomposition(series, seasonal=7, trend=101, robust=False):
    """STL decomposition of a weekly series with a period of 52 weeks.

    seasonal and trend are the lengths of the smoothers (odd numbers, high number = less change),
    robust=True allows more individual deviation from trend and season. Returns the plot.
    """
    stl = STL(series, period=52, seasonal=seasonal, trend=trend, robust=robust)
    res = stl.fit()

    # The series, trend, season and residual above each other, as in res.plot() from statsmodels
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, subplot_titles=["Series", "Trend", "Season", "Residual"])
    fig.add_scatter(x=series.index, y=res.observed, mode="lines", line_color=THEME_COLOUR, row=1, col=1)
    fig.add_scatter(x=series.index, y=res.trend, mode="lines", line_color=THEME_COLOUR, row=2, col=1)
    fig.add_scatter(x=series.index, y=res.seasonal, mode="lines", line_color=THEME_COLOUR, row=3, col=1)
    fig.add_scatter(x=series.index, y=res.resid, mode="markers", marker=dict(size=3, color=THEME_COLOUR), row=4, col=1)
    fig.update_layout(height=700, showlegend=False)
    return fig


@st.cache_data(show_spinner=False)
def spectrogram_plot(series, window_length=52, window_overlap=26):
    """Spectrogram of a weekly series using the short-time Fourier transform.

    window_length and window_overlap are in weeks. The sampling frequency is 52 per year,
    so the frequency axis is in cycles per year. Returns the plot.
    """
    # Remove the mean so the zero frequency does not hide the rest
    values = series.values - series.values.mean()
    f, t, Zxx = stft(values, fs=52, nperseg=window_length, noverlap=window_overlap)

    fig = go.Figure(go.Heatmap(x=t, y=f, z=np.abs(Zxx), colorbar_title="Magnitude"))
    fig.update_layout(
        title="Spectrogram",
        xaxis_title=f"Years from {series.index[0].date()}",
        yaxis_title="Frequency (cycles per year)",
    )
    return fig


@st.cache_data(show_spinner=False)
def sliding_window_correlation(x, y, window=52, lag=0):
    """Sliding window correlation (SWC) between two weekly series, as in the lecture notes.

    x is shifted lag weeks forward, so x from lag weeks earlier is compared with y.
    The window is centred on each week. Returns the plot.
    """
    x_lagged = x.shift(lag)
    swc = y.rolling(window, center=True).corr(x_lagged)

    # The two series and the SWC above each other, as in the lecture
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        subplot_titles=[f"{x.name} (lagged {lag} weeks)", y.name, f"SWC, window {window} weeks"])
    fig.add_scatter(x=x_lagged.index, y=x_lagged, mode="lines", line_color=THEME_COLOUR, row=1, col=1)
    fig.add_scatter(x=y.index, y=y, mode="lines", line_color=THEME_COLOUR, row=2, col=1)
    fig.add_scatter(x=swc.index, y=swc, mode="lines", line_color=THEME_COLOUR, row=3, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=3, col=1)
    fig.update_yaxes(range=[-1, 1], row=3, col=1)
    fig.update_layout(height=700, showlegend=False)
    return fig


@st.cache_data(show_spinner="Training the model")
def forecast_filling(data, end, years=5, horizon=26, exog=None, p=1, d=1, q=1, m=52, sp=1, sd=1, sq=1):
    """Dynamic forecast of the degree of filling with River's SNARIMAX model.

    data has one row per week (or month) with the column fill_level and any exogenous variables.
    The model learns from the years (length of the history) up to end and forecasts horizon steps after end.
    exog is a list of the columns to use as exogenous variables (the chosen data sources). Their values
    are needed for the forecast steps too, so with exog the forecast stops where these columns stop.
    p, d, q is the order, sp, sd, sq the seasonal order and m the season length (52 for weeks).
    Returns a DataFrame with the forecast and the observed values (NaN where there is no observation).
    """
    if exog is None:
        exog = []

    # Training data, rows with missing values are skipped
    start = pd.Timestamp(end) - pd.DateOffset(years=years)
    train = data.loc[start:end].dropna(subset=["fill_level"] + exog)

    # Learn one step at a time, as in the streaming examples from the lecture
    model = time_series.SNARIMAX(p=p, d=d, q=q, m=m, sp=sp, sd=sd, sq=sq)
    for _, row in train.iterrows():
        x = row[exog].to_dict() if exog else None
        model.learn_one(row["fill_level"], x)

    # The steps after the training data. With exogenous variables, only steps where they are known are used
    dates = pd.date_range(end, periods=horizon + 1, freq=data.index.freq)[1:]
    future = data.reindex(dates)
    xs = None
    if exog:
        future = future.dropna(subset=exog)
        xs = [row[exog].to_dict() for _, row in future.iterrows()]

    # Dynamic forecast: each step uses the forecasts of the previous steps
    forecast = model.forecast(horizon=len(future), xs=xs)
    return pd.DataFrame({"forecast": forecast, "observed": future["fill_level"]}, index=future.index)
