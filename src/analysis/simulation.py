import pandas as pd

RACE_POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
SPRINT_POINTS = [8, 7, 6, 5, 4, 3, 2, 1]


def remaining_events(results: pd.DataFrame, calendar: pd.DataFrame) -> tuple:
    """Number of races and sprints still to be run this season."""
    race_rounds = results.loc[results["session"] == "Race", "round"]
    last_race_round = 0
    if not race_rounds.empty:
        last_race_round = int(race_rounds.max())

    remaining = calendar[calendar["round"] > last_race_round]
    races_left = len(remaining)

    sprint_rounds_done = set(results.loc[results["session"] == "Sprint", "round"])
    sprints_left = 0
    for _, race in remaining.iterrows():
        if race["has_sprint"] and race["round"] not in sprint_rounds_done:
            sprints_left += 1

    return races_left, sprints_left


def max_points_left(races_left: int, sprints_left: int) -> int:
    """Maximum points one driver can still score (wins everything)."""
    return races_left * RACE_POINTS[0] + sprints_left * SPRINT_POINTS[0]