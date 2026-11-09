import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from scipy.fft import dct, idct
from scipy.signal import stft
from sklearn.neighbors import LocalOutlierFactor
from statsmodels.tsa.seasonal import STL


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

    fig = plt.figure(figsize=(10, 4))
    plt.plot(series.index, values, linewidth=0.6, label=series.name)
    plt.plot(series.index, upper, color="black", linestyle="--", label="SPC boundaries")
    plt.plot(series.index, lower, color="black", linestyle="--")
    plt.plot(series.index[is_outlier], values[is_outlier], "o", color="red", markersize=3, label="Outliers")
    plt.xlabel("Time")
    plt.ylabel(series.name)
    plt.title("SPC outliers")
    plt.legend()

    outliers = series[is_outlier]
    summary = pd.DataFrame({
        "outliers": [is_outlier.sum()],
        "share (%)": [100 * is_outlier.mean()],
        "SATV median": [median],
        "SATV robust SD": [sd],
    })
    return fig, outliers, summary


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

    fig = plt.figure(figsize=(10, 4))
    plt.plot(series.index, values, linewidth=0.6, label=series.name)
    plt.plot(series.index[is_anomaly], values[is_anomaly], "o", color="red", markersize=3, label="Anomalies")
    plt.xlabel("Time")
    plt.ylabel(series.name)
    plt.title("LOF anomalies")
    plt.legend()

    anomalies = series[is_anomaly]
    summary = pd.DataFrame({
        "anomalies": [is_anomaly.sum()],
        "share (%)": [100 * is_anomaly.mean()],
        "lowest": [anomalies.min()],
        "highest": [anomalies.max()],
    })
    return fig, anomalies, summary


def stl_decomposition(series, seasonal=7, trend=101, robust=False):
    """STL decomposition of a weekly series with a period of 52 weeks.

    seasonal and trend are the lengths of the smoothers (odd numbers, high number = less change),
    robust=True allows more individual deviation from trend and season. Returns the plot.
    """
    # Fit the model and plot the series, trend, season and residual
    stl = STL(series, period=52, seasonal=seasonal, trend=trend, robust=robust)
    res = stl.fit()
    fig = res.plot()
    fig.set_size_inches(10, 7)
    return fig


def spectrogram_plot(series, window_length=52, window_overlap=26):
    """Spectrogram of a weekly series using the short-time Fourier transform.

    window_length and window_overlap are in weeks. The sampling frequency is 52 per year,
    so the frequency axis is in cycles per year. Returns the plot.
    """
    # Remove the mean so the zero frequency does not hide the rest
    values = series.values - series.values.mean()
    f, t, Zxx = stft(values, fs=52, nperseg=window_length, noverlap=window_overlap)

    fig = plt.figure(figsize=(10, 4))
    plt.pcolormesh(t, f, np.abs(Zxx), shading="gouraud")
    plt.colorbar(label="Magnitude")
    plt.xlabel(f"Years from {series.index[0].date()}")
    plt.ylabel("Frequency (cycles per year)")
    plt.title("Spectrogram")
    return fig
