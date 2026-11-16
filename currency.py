import io

import pandas as pd
import requests

# Norges Bank's exchange rate API. B is business days, NOK is the quote currency and SP is the spot rate
NB_URL = "https://data.norges-bank.no/api/data/EXR/B.{}.NOK.SP"


def download_exchange_rates(start, end, currencies=("EUR", "USD")):
    """Daily exchange rates from Norges Bank, as NOK per unit of each currency.

    start and end are dates like "2024-01-01". There is only a rate on business days.
    """
    # Several currencies are joined with + in the URL, e.g. B.EUR+USD.NOK.SP
    url = NB_URL.format("+".join(currencies))
    params = {"format": "csv", "startPeriod": start, "endPeriod": end, "locale": "en"}
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    # The CSV has one row per currency and day, with the rate in OBS_VALUE
    df = pd.read_csv(io.StringIO(response.text), sep=";")
    rates = df.pivot(index="TIME_PERIOD", columns="BASE_CUR", values="OBS_VALUE")
    rates.index = pd.to_datetime(rates.index).rename("date")
    rates.columns.name = None
    return rates
