import pandas as pd

# Statuses meaning the driver did not take the start
NOT_STARTED = {
    "Did not start",
    "Did not qualify",
    "Did not prequalify",
    "Withdrew",
    "Excluded",
}


def driver_standings(results: pd.DataFrame) -> pd.DataFrame:
    """All the driver's points, with his current team (team of his last round)."""
    if results.empty:
        return pd.DataFrame()

    points = results.groupby("driver_id")["points"].sum()

    races_only = results[results["session"] == "Race"]
    winners = races_only[races_only["finish_position"] == 1]
    wins = winners.groupby("driver_id").size()

    sorted_results = results.sort_values("round")
    current_team = sorted_results.groupby("driver_id")["team"].last()

    names = results.groupby("driver_id")["driver"].first()

    standings = pd.DataFrame({
        "driver": names,
        "points": points,
        "wins": wins,
        "team": current_team,
    })
    standings["wins"] = standings["wins"].fillna(0).astype(int)

    standings = standings.sort_values(["points", "wins"], ascending=False)
    standings = standings.reset_index(drop=True)
    standings.insert(0, "position", standings.index + 1)
    return standings


def constructor_standings(results: pd.DataFrame, season: int) -> pd.DataFrame:
    """Each result gives its points to the team of the day."""
    # No constructors championship before 1958
    if results.empty or season < 1958:
        return pd.DataFrame()

    points = results.groupby("team")["points"].sum()
    standings = points.reset_index()

    standings = standings.sort_values("points", ascending=False)
    standings = standings.reset_index(drop=True)
    standings.insert(0, "position", standings.index + 1)
    return standings


def cumulative_points(results: pd.DataFrame) -> pd.DataFrame:
    """Running total of points for each driver, round after round."""
    if results.empty:
        return pd.DataFrame({"round": [], "driver": [], "cumulative_points": []})

    table = results.pivot_table(
        index="round",
        columns="driver",
        values="points",
        aggfunc="sum",
        fill_value=0,
    )

    last_round = int(table.index.max())
    table = table.reindex(range(1, last_round + 1), fill_value=0)
    table.index.name = "round"

    table = table.cumsum()

    table = table.reset_index()
    long_table = table.melt(id_vars="round", var_name="driver", value_name="cumulative_points")
    return long_table


def has_finished(status: str) -> bool:
    """True if the driver saw the chequered flag (even laps behind)."""
    return status in ("Finished", "Lapped") or status.startswith("+")


def driver_stats(results: pd.DataFrame, driver: str) -> dict:
    """Season stats of one driver (main races, points include sprints)."""
    driver_results = results[results["driver"] == driver]
    races = driver_results[driver_results["session"] == "Race"]
    if races.empty:
        return {}

    statuses = races["status"].fillna("")
    not_started = statuses.isin(NOT_STARTED)
    disqualified = statuses == "Disqualified"
    finished = statuses.apply(has_finished)
    retired = ~(finished | not_started | disqualified)

    finish_positions = races.loc[finished, "finish_position"].dropna()
    best_position = None
    if not finish_positions.empty:
        best_position = int(finish_positions.min())

    return {
        "races": int((~not_started).sum()),
        "points": float(driver_results["points"].sum()),
        "wins": int((races["finish_position"] == 1).sum()),
        "podiums": int((races["finish_position"] <= 3).sum()),
        "best_position": best_position,
        "retirements": int(retired.sum()),
        "disqualifications": int(disqualified.sum()),
    }