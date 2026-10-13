import pandas as pd

RACE_POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
SPRINT_POINTS = [8, 7, 6, 5, 4, 3, 2, 1]

NO_POINTS_RESULTS = ["DNF", "DNS", "DSQ"]
POSITION_CHOICES = [str(position) for position in range(1, 21)] + NO_POINTS_RESULTS


def remaining_event_list(results: pd.DataFrame, calendar: pd.DataFrame) -> pd.DataFrame:
    """One row per event still to be run: round, event name and session (Sprint or Race)."""
    race_rounds = results.loc[results["session"] == "Race", "round"]
    last_race_round = 0
    if not race_rounds.empty:
        last_race_round = int(race_rounds.max())

    sprint_rounds_done = set(results.loc[results["session"] == "Sprint", "round"])
    remaining = calendar[calendar["round"] > last_race_round]

    rows = []
    for _, race in remaining.iterrows():
        if race["has_sprint"] and race["round"] not in sprint_rounds_done:
            rows.append({
                "round": int(race["round"]),
                "event": f"{race['race']} (Sprint)",
                "session": "Sprint",
            })
        rows.append({
            "round": int(race["round"]),
            "event": race["race"],
            "session": "Race",
        })

    if not rows:
        return pd.DataFrame({"round": [], "event": [], "session": []})
    return pd.DataFrame(rows)


def remaining_events(results: pd.DataFrame, calendar: pd.DataFrame) -> tuple:
    """Number of races and sprints still to be run this season."""
    events = remaining_event_list(results, calendar)
    races_left = int((events["session"] == "Race").sum())
    sprints_left = int((events["session"] == "Sprint").sum())
    return races_left, sprints_left


def max_points_left(races_left: int, sprints_left: int) -> int:
    """Maximum points one driver can still score (wins everything)."""
    return races_left * RACE_POINTS[0] + sprints_left * SPRINT_POINTS[0]


def title_contenders(standings: pd.DataFrame, max_left: int) -> pd.DataFrame:
    """For each driver: gap to the leader, max reachable points, and if he can still win."""
    if standings.empty:
        return pd.DataFrame()

    leader_points = standings["points"].max()

    table = standings[["position", "driver", "team", "points"]].copy()
    table["gap"] = leader_points - table["points"]
    table["max_possible"] = table["points"] + max_left
    table["can_win"] = table["max_possible"] >= leader_points
    return table


def points_for_result(result: str, session: str) -> int:
    """Points given for a result ("1" to "20", DNF, DNS or DSQ) in a race or a sprint."""
    if result in NO_POINTS_RESULTS:
        return 0

    if session == "Race":
        points_table = RACE_POINTS
    else:
        points_table = SPRINT_POINTS

    position = int(result)
    if 1 <= position <= len(points_table):
        return points_table[position - 1]
    return 0


def check_scenario(grid: pd.DataFrame, drivers: list) -> list:
    """Return the events where two drivers have the same finishing position."""
    wrong_events = []
    for _, row in grid.iterrows():
        positions = []
        for driver in drivers:
            if row[driver] not in NO_POINTS_RESULTS:
                positions.append(row[driver])

        if len(positions) != len(set(positions)):
            wrong_events.append(row["event"])
    return wrong_events


def apply_scenario(standings: pd.DataFrame, grid: pd.DataFrame, drivers: list) -> pd.DataFrame:
    """Final standings if the scenario happens (other drivers score no more points)."""
    table = standings[["driver", "team", "points"]].copy()
    table["extra_points"] = 0

    for driver in drivers:
        extra = 0
        for _, row in grid.iterrows():
            extra += points_for_result(str(row[driver]), row["session"])
        table.loc[table["driver"] == driver, "extra_points"] = extra

    table["final_points"] = table["points"] + table["extra_points"]
    table = table.sort_values("final_points", ascending=False).reset_index(drop=True)
    table.insert(0, "position", table.index + 1)
    return table