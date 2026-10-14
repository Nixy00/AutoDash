import pandas as pd
import pytest

from src.analysis.simulation import (
    apply_scenario,
    check_scenario,
    max_points_left,
    points_for_result,
    remaining_event_list,
    remaining_events,
    title_contenders,
)

@pytest.mark.parametrize(
    "result, session, expected",
    [
        ("1", "Race", 25),
        ("10", "Race", 1),
        ("11", "Race", 0),
        ("1", "Sprint", 8),
        ("8", "Sprint", 1),
        ("9", "Sprint", 0),
        ("DNF", "Race", 0),
        ("DNS", "Race", 0),
        ("DSQ", "Sprint", 0),
    ],
)
def test_points_for_result(result, session, expected):
    assert points_for_result(result, session) == expected


def test_max_points_left_races_only():
    assert max_points_left(6, 0) == 150


def test_max_points_left_with_sprint():
    assert max_points_left(2, 1) == 58


def test_max_points_left_end_of_season():
    assert max_points_left(0, 0) == 0


def make_calendar():
    """Fake 3-round season, rounds 2 and 3 have a sprint."""
    return pd.DataFrame({
        "round": [1, 2, 3],
        "race": ["GP A", "GP B", "GP C"],
        "date": pd.to_datetime(["2026-03-01", "2026-03-08", "2026-03-15"]),
        "has_sprint": [False, True, True],
    })


def test_remaining_events_during_a_sprint_weekend():
    results = pd.DataFrame({
        "round": [1, 2],
        "session": ["Race", "Sprint"],
    })
    events = remaining_event_list(results, make_calendar())

    assert list(events["event"]) == ["GP B", "GP C (Sprint)", "GP C"]
    assert remaining_events(results, make_calendar()) == (2, 1)


def test_remaining_events_at_the_end_of_the_season():
    results = pd.DataFrame({
        "round": [1, 2, 2, 3, 3],
        "session": ["Race", "Sprint", "Race", "Sprint", "Race"],
    })
    events = remaining_event_list(results, make_calendar())

    assert events.empty
    assert remaining_events(results, make_calendar()) == (0, 0)


def test_title_contenders():
    standings = pd.DataFrame({
        "position": [1, 2, 3, 4],
        "driver": ["Alice", "Bob", "Carl", "Dan"],
        "team": ["Red", "Blue", "Green", "Blue"],
        "points": [100.0, 80.0, 40.0, 50.0],
    })
    table = title_contenders(standings, max_left=50)
    can_win = dict(zip(table["driver"], table["can_win"]))

    assert can_win["Alice"]
    assert can_win["Bob"]
    assert not can_win["Carl"]


def test_check_scenario_finds_same_position():
    grid = pd.DataFrame({
        "event": ["GP A", "GP B"],
        "session": ["Race", "Race"],
        "Alice": ["1", "2"],
        "Bob": ["1", "3"],
    })
    assert check_scenario(grid, ["Alice", "Bob"]) == ["GP A"]


def test_check_scenario_allows_several_retirements():
    grid = pd.DataFrame({
        "event": ["GP A"],
        "session": ["Race"],
        "Alice": ["DNF"],
        "Bob": ["DNF"],
    })
    assert check_scenario(grid, ["Alice", "Bob"]) == []


def test_apply_scenario_changes_the_champion():
    standings = pd.DataFrame({
        "driver": ["Alice", "Bob", "Carl"],
        "team": ["Red", "Blue", "Green"],
        "points": [100.0, 90.0, 10.0],
    })
    grid = pd.DataFrame({
        "event": ["GP A", "GP B"],
        "session": ["Race", "Race"],
        "Alice": ["DNF", "DNF"],
        "Bob": ["1", "1"],
    })
    final = apply_scenario(standings, grid, ["Alice", "Bob"])

    assert final.iloc[0]["driver"] == "Bob"
    assert final.iloc[0]["final_points"] == 140
    carl = final[final["driver"] == "Carl"].iloc[0]
    assert carl["final_points"] == 10