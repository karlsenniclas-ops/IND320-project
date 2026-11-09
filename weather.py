import time

import pandas as pd
import requests

# open-meteo's historical weather API, models=era5 gives the ERA5 reanalysis
ERA5_URL = "https://archive-api.open-meteo.com/v1/archive"

# Hourly properties to download
VARIABLES = "temperature_2m,precipitation,snowfall,wind_speed_10m"

# The 1000 random locations per region, made in the part 3 notebook
POINTS_FILE = "data/region_points.csv"


def region_id(area_type, area_number):
    """Region name in the points file for a magasinstatistikk area, e.g. EL 3 is NO3 and VASS 1 is VASS1."""
    if area_type == "EL":
        return f"NO{area_number}"
    if area_type == "VASS":
        return f"VASS{area_number}"
    return "NO0"  # all of Norway


def download_era5(region, start, end, n_points=1000, points_file=POINTS_FILE):
    """Hourly ERA5 weather for a region, averaged over the sampled locations.

    region is a name from the points file, e.g. "NO3". start and end are dates like "2024-01-01".
    ERA5 has one value per 0.25 degree grid cell, so locations in the same cell get the same data.
    To use fewer API calls, each cell is downloaded once and weighted by the number of locations in it.
    """
    points = pd.read_csv(points_file)
    points = points[points["region"] == region].head(n_points)

    # Round the locations to the nearest grid cell and count the locations in each cell
    cells = (points[["lat", "lon"]] / 0.25).round() * 0.25
    cells = cells.value_counts().reset_index()

    total = 0
    for i in range(0, len(cells), 50):
        # 50 cells per request, given as comma separated lists
        batch = cells.iloc[i:i + 50]
        params = {
            "latitude": ",".join(batch["lat"].astype(str)),
            "longitude": ",".join(batch["lon"].astype(str)),
            "start_date": start,
            "end_date": end,
            "hourly": VARIABLES,
            "models": "era5",
            "wind_speed_unit": "ms",
        }
        response = requests.get(ERA5_URL, params=params, timeout=120)
        response.raise_for_status()
        locations = response.json()
        if isinstance(locations, dict):  # a single location is not returned as a list
            locations = [locations]

        # Add the hourly values of each cell, weighted by the number of locations in the cell
        for location, count in zip(locations, batch["count"]):
            hourly = pd.DataFrame(location["hourly"]).set_index("time")
            total = total + hourly * count

        # The free API allows 600 calls per minute, and 50 cells for one year count as about 520 calls
        if i + 50 < len(cells):
            time.sleep(60)

    weather = total / cells["count"].sum()
    weather.index = pd.to_datetime(weather.index)
    return weather
