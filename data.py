import pandas as pd
import pymongo
import requests
import streamlit as st

# NVE Magasinstatistikk API, returns the full weekly history for all areas
RESERVOIR_URL = "https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/HentOffentligData"

# Norwegian to English column names, same mapping as in the notebook
COLUMN_RENAME = {
    "dato_Id": "date",
    "omrType": "area_type",
    "omrnr": "area_number",
    "iso_aar": "iso_year",
    "iso_uke": "iso_week",
    "fyllingsgrad": "fill_level",
    "kapasitet_TWh": "capacity_twh",
    "fylling_TWh": "stored_energy_twh",
    "neste_Publiseringsdato": "next_publication_date",
    "fyllingsgrad_forrige_uke": "fill_level_prev_week",
    "endring_fyllingsgrad": "fill_level_change",
}

# The five columns we plot and show in the app
VALUE_COLUMNS = [
    "fill_level",
    "capacity_twh",
    "stored_energy_twh",
    "fill_level_prev_week",
    "fill_level_change",
]


def month_options():
    """All months from the first week in the API (Jan 1995) up to this month, as "YYYY-MM" strings.

    Used by the period slider, which has to exist before anything is downloaded.
    """
    months = pd.period_range("1995-01", pd.Timestamp.today(), freq="M")
    return [str(month) for month in months]


@st.cache_data(ttl=3600)
def load_reservoirs(start_month, end_month):
    """Download weekly reservoir data from the NVE API and keep the months in the chosen period.

    The API has no date parameters and always sends the whole history, so the
    period is cut right after the download. The cache is per period, so moving
    the slider to a new period gives a new download.
    """
    response = requests.get(RESERVOIR_URL, timeout=60)
    response.raise_for_status()

    df = pd.DataFrame(response.json())
    df = df.rename(columns=COLUMN_RENAME)
    df["date"] = pd.to_datetime(df["date"])

    # Keep only the weeks inside the chosen period
    months = df["date"].dt.strftime("%Y-%m")
    df = df[(months >= start_month) & (months <= end_month)]

    # The raw rows are not sorted by date
    return df.sort_values("date")


@st.cache_resource
def init_connection():
    """MongoDB client, created once and shared between reruns.

    The URI is in .streamlit/secrets.toml locally and in the app settings on streamlit.io.
    """
    return pymongo.MongoClient(st.secrets["mongo"]["uri"])


@st.cache_data(ttl=600)
def load_flows():
    """Daily cross-border flows (GWh) per connection and direction, prepared in the notebook with Spark."""
    client = init_connection()
    collection = client["ind320"]["flows_daily"]

    # Leave out MongoDB's _id field, it is not needed in the app
    items = list(collection.find({}, {"_id": 0}))

    df = pd.DataFrame(items)
    df["date"] = pd.to_datetime(df["date"])
    return df
