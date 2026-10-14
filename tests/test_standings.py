import pandas as pd
import pytest

from src.analysis.standings import (
    apply_official_points,
    constructor_standings,
    cumulative_points,
    driver_standings,
    driver_stats,
    has_finished,
)


def make_results():
    """Fake season: 2 rounds, a sprint in round 2, Bob moves from Blue to Green.

    Totals: Alice 25 + 8 + 15 = 48, Bob 18 + 7 + 25 = 50, Carl 0 + 18 = 18.
    """
    return pd.DataFrame({
        "round":           [1, 1, 1, 2, 2, 2, 2, 2],
        "race":            ["GP A", "GP A", "GP A", "GP B", "GP B", "GP B", "GP B", "GP B"],
        "session":         ["Race", "Race", "Race", "Sprint", "Sprint", "Race", "Race", "Race"],
        "driver_id":       ["alice", "bob", "carl", "alice", "bob", "alice", "bob", "carl"],
        "driver":          ["Alice", "Bob", "Carl", "Alice", "Bob", "Alice", "Bob", "Carl"],
        "team":            ["Red", "Blue", "Green", "Red", "Green", "Red", "Green", "Green"],
        "finish_position": [1, 2, 3, 1, 2, 3, 1, 2],
        "points":          [25.0, 18.0, 0.0, 8.0, 7.0, 15.0, 25.0, 18.0],
        "status":          ["Finished", "Finished", "Retired", "Finished", "Finished",
                            "Lapped", "Finished", "Finished"],
    })

def test_driver_standings_order_and_points():
    standings = driver_standings(make_results())

    assert list(standings["driver"]) == ["Bob", "Alice", "Carl"]
    assert list(standings["points"]) == [50, 48, 18]
    assert list(standings["position"]) == [1, 2, 3]

def test_sprint_win_is_not_a_win():
    standings = driver_standings(make_results())
    wins = dict(zip(standings["driver"], standings["wins"]))

    assert wins["Alice"] == 1
    assert wins["Bob"] == 1
    assert wins["Carl"] == 0

def test_current_team_is_the_last_one():
    standings = driver_standings(make_results())
    bob = standings[standings["driver"] == "Bob"].iloc[0]
    assert bob["team"] == "Green"

def test_driver_standings_empty():
    assert driver_standings(pd.DataFrame()).empty

def test_points_go_to_the_team_of_the_day():
    standings = constructor_standings(make_results(), season=2026)
    points = dict(zip(standings["team"], standings["points"]))

    assert points["Blue"] == 18
    assert points["Green"] == 50
    assert points["Red"] == 48
    assert standings.iloc[0]["team"] == "Green"


def test_no_constructors_before_1958():
    assert constructor_standings(make_results(), season=1957).empty

def test_cumulative_points():
    progress = cumulative_points(make_results())
    alice = progress[progress["driver"] == "Alice"]

    assert list(alice["cumulative_points"]) == [25, 48]


def test_cumulative_points_fills_missing_rounds():
    results = pd.DataFrame({
        "round": [1, 3],
        "driver": ["Alice", "Alice"],
        "points": [25.0, 18.0],
    })
    progress = cumulative_points(results)

    assert list(progress["round"]) == [1, 2, 3]
    assert list(progress["cumulative_points"]) == [25, 25, 43]

@pytest.mark.parametrize(
    "status, expected",
    [
        ("Finished", True),
        ("Lapped", True),
        ("+1 Lap", True),
        ("+3 Laps", True),
        ("Retired", False),
        ("Engine", False),
        ("Disqualified", False),
        ("Did not start", False),
    ],
)
def test_has_finished(status, expected):
    assert has_finished(status) == expected

def test_driver_stats_alice():
    stats = driver_stats(make_results(), "Alice")

    assert stats["races"] == 2
    assert stats["points"] == 48
    assert stats["wins"] == 1
    assert stats["podiums"] == 2
    assert stats["best_position"] == 1
    assert stats["retirements"] == 0


def test_driver_stats_counts_retirements():
    stats = driver_stats(make_results(), "Carl")

    assert stats["retirements"] == 1
    assert stats["best_position"] == 2


def test_driver_stats_unknown_driver():
    assert driver_stats(make_results(), "Nobody") == {}

def test_official_points_replace_computed_points():
    standings = driver_standings(make_results())
    official = pd.DataFrame({
        "driver_id": ["alice", "bob", "carl"],
        "position": [1, 2, None],
        "points": [60.0, 50.0, 18.0],
        "wins": [2, 1, 0],
    })
    table = apply_official_points(standings, official)

    assert list(table["driver"]) == ["Alice", "Bob", "Carl"]
    assert table.iloc[0]["points"] == 60
    assert pd.isna(table.iloc[2]["position"])
    assert table.iloc[1]["team"] == "Green"


def test_official_points_missing_keeps_our_standings():
    standings = driver_standings(make_results())
    table = apply_official_points(standings, pd.DataFrame())

    assert list(table["driver"]) == ["Bob", "Alice", "Carl"]