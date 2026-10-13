from datetime import date
import pandas as pd
import requests

BASE_URL = "https://api.jolpi.ca/ergast/f1"
PAGE_LIMIT = 100


def check_season(season: int) -> None:
    """Raise an error if the season is not a valid year."""
    current_year = date.today().year
    if not isinstance(season, int) or season < 1950 or season > current_year:
        raise ValueError(f"Invalid season: {season}")


def fetch_races(url: str) -> list:
    """Download every page of an endpoint and return the list of races."""
    races = []
    offset = 0
    total = 1

    while offset < total:
        params = {"limit": PAGE_LIMIT, "offset": offset}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()["MRData"]
        races.extend(data["RaceTable"]["Races"])

        total = int(data["total"])
        offset += PAGE_LIMIT

    return races


def flatten_results(races: list, results_key: str, session: str) -> list:
    """Turn the nested API data into one row per driver and per race."""
    rows = []

    for race in races:
        for result in race.get(results_key, []):
            driver = result["Driver"]
            position = result.get("position")

            row = {
                "round": int(race["round"]),
                "race": race["raceName"],
                "session": session,
                "driver_id": driver["driverId"],
                "driver": f"{driver['givenName']} {driver['familyName']}",
                "team": result["Constructor"]["name"],
                "finish_position": int(position) if position else None,
                "points": float(result.get("points", 0)),
                "status": result.get("status", ""),
            }
            rows.append(row)

    return rows


def get_season_results(season: int) -> pd.DataFrame:
    """One row per driver and per race, main races and sprints."""
    check_season(season)

    try:
        races = fetch_races(f"{BASE_URL}/{season}/results/")
        sprints = fetch_races(f"{BASE_URL}/{season}/sprint/")
    except requests.RequestException as error:
        print(f"Network error: {error}")
        return pd.DataFrame()

    rows = flatten_results(races, "Results", "Race")
    rows += flatten_results(sprints, "SprintResults", "Sprint")
    return pd.DataFrame(rows)

def get_season_calendar(season: int) -> pd.DataFrame:
    """One row per race of the season, with its date and whether it has a sprint."""
    check_season(season)

    try:
        races = fetch_races(f"{BASE_URL}/{season}/races/")
    except requests.RequestException as error:
        print(f"Network error: {error}")
        return pd.DataFrame()

    rows = []
    for race in races:
        row = {
            "round": int(race["round"]),
            "race": race["raceName"],
            "date": race["date"],
            "has_sprint": "Sprint" in race,
        }
        rows.append(row)

    calendar = pd.DataFrame(rows)
    if not calendar.empty:
        calendar["date"] = pd.to_datetime(calendar["date"])
    return calendar


def get_official_driver_standings(season: int) -> pd.DataFrame:
    """Official driver standings (with dropped scores before 1991)."""
    check_season(season)
    url = f"{BASE_URL}/{season}/driverstandings/"

    rows = []
    offset = 0
    total = 1

    try:
        while offset < total:
            params = {"limit": PAGE_LIMIT, "offset": offset}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()["MRData"]
            total = int(data["total"])
            offset += PAGE_LIMIT

            lists = data["StandingsTable"]["StandingsLists"]
            if not lists:
                break

            for item in lists[0]["DriverStandings"]:
                position = item.get("position")
                row = {
                    "driver_id": item["Driver"]["driverId"],
                    "position": int(position) if position else None,
                    "points": float(item.get("points", 0)),
                    "wins": int(item.get("wins", 0)),
                }
                rows.append(row)
    except requests.RequestException as error:
        print(f"Network error: {error}")
        return pd.DataFrame()

    return pd.DataFrame(rows)


if __name__ == "__main__":
    print(get_season_results(2025).head())
    print(get_season_calendar(2026).head())
    print(get_official_driver_standings(1988).head(3))