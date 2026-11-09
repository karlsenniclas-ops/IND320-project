import pandas as pd
import pymongo
import requests
import streamlit as st
from weather import download_era5

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

# Area numbers that have data for each area type (VASS 4 is in the API, but has no data)
AREA_NUMBERS = {"EL": [1, 2, 3, 4, 5], "NO": [0], "VASS": [1, 2, 3]}


def month_options():
    """All months from the first week in the API (Jan 1995) up to this month, as "YYYY-MM" strings.

    Used by the period slider, which has to exist before anything is downloaded.
    """
    months = pd.period_range("1995-01", pd.Timestamp.today(), freq="M")
    return [str(month) for month in months]


def chosen_area():
    """Area type and area number chosen in the sidebar. The number is 0 for NO and the first one if none is chosen."""
    area_type = st.session_state["area_type"]
    numbers = AREA_NUMBERS[area_type]
    number = st.session_state.get("area_number", numbers[0])
    if number not in numbers:
        number = numbers[0]
    return area_type, number


@st.cache_data(ttl=3600)
def download_reservoirs():
    """Download the full weekly reservoir history from the NVE API.

    The API has no date parameters and always sends the whole history. This function has no
    arguments, so the download is cached once and not repeated when the period is changed.
    """
    response = requests.get(RESERVOIR_URL, timeout=60)
    response.raise_for_status()

    df = pd.DataFrame(response.json())
    df = df.rename(columns=COLUMN_RENAME)
    df["date"] = pd.to_datetime(df["date"])

    # The raw rows are not sorted by date
    return df.sort_values("date")


def load_reservoirs(start_month, end_month):
    """Reservoir data for the months in the chosen period, cut from the cached download."""
    df = download_reservoirs()
    months = df["date"].dt.strftime("%Y-%m")
    return df[(months >= start_month) & (months <= end_month)]


@st.cache_data(ttl=86400, show_spinner="Downloading ERA5 data from open-meteo. This takes a minute or two the first time.")
def load_weather(region, year):
    """Hourly ERA5 weather for a region and year, averaged over the sampled locations.

    The app uses 200 of the 1000 locations to keep the download at a minute or two
    with open-meteo's free limits. The result is cached for each region and year.
    """
    return download_era5(region, f"{year}-01-01", f"{year}-12-31", n_points=200)


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
