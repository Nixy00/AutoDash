from datetime import date

import pytest

from src.ingestion.f1_api import check_season, flatten_results

def test_valid_seasons():
    check_season(1950)
    check_season(2025)
    check_season(date.today().year)


@pytest.mark.parametrize("season", [1949, date.today().year + 1, "2025", 2025.0])
def test_invalid_seasons(season):
    with pytest.raises(ValueError):
        # Wrong types are passed on purpose, to check they are refused
        # noinspection PyTypeChecker
        check_season(season)

def make_race(results_key: str) -> dict:
    """Fake race in the same shape as the API JSON."""
    return {
        "round": "3",
        "raceName": "GP Test",
        results_key: [
            {
                "position": "1",
                "points": "25",
                "status": "Finished",
                "Driver": {"driverId": "alice", "givenName": "Alice", "familyName": "Martin"},
                "Constructor": {"name": "Red"},
            },
            {
                "points": "0",
                "status": "Retired",
                "Driver": {"driverId": "bob", "givenName": "Bob", "familyName": "Durand"},
                "Constructor": {"name": "Blue"},
            },
        ],
    }


def test_flatten_race_results():
    rows = flatten_results([make_race("Results")], "Results", "Race")

    assert len(rows) == 2
    alice = rows[0]
    assert alice["round"] == 3
    assert alice["driver"] == "Alice Martin"
    assert alice["team"] == "Red"
    assert alice["finish_position"] == 1
    assert alice["points"] == 25.0
    assert alice["session"] == "Race"


def test_flatten_handles_missing_position():
    rows = flatten_results([make_race("Results")], "Results", "Race")
    assert rows[1]["finish_position"] is None


def test_flatten_sprint_results():
    rows = flatten_results([make_race("SprintResults")], "SprintResults", "Sprint")
    assert rows[0]["session"] == "Sprint"


def test_flatten_race_without_results():
    race = {"round": "1", "raceName": "GP Empty"}
    assert flatten_results([race], "Results", "Race") == []