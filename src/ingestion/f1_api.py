from datetime import date
import pandas as pd
import requests

URL_BASE = "https://api.jolpi.ca/ergast/f1"
LIMITE = 100

def _valider_saison(saison: int) -> None:
    if not isinstance(saison, int) or not 1950 <= saison <= date.today().year:
        raise ValueError(f"Saison invalide : {saison}")


def _recuperer_courses(url: str) -> list:
    """Parcourt toutes les pages de l'API et renvoie la liste des courses."""
    courses = []
    offset = 0
    while True:
        reponse = requests.get(
            url, params={"limit": LIMITE, "offset": offset}, timeout=10
        )
        reponse.raise_for_status()
        mrdata = reponse.json()["MRData"]
        courses.extend(mrdata["RaceTable"]["Races"])
        offset += LIMITE
        if offset >= int(mrdata["total"]):
            break
    return courses


def _aplatir(courses: list, cle: str, type_course: str) -> list:
    """Transforme les courses imbriquées en une ligne par pilote et par course."""
    lignes = []
    for course in courses:
        for r in course.get(cle, []):
            position = r.get("position")
            lignes.append({
                "manche": int(course["round"]),
                "course": course["raceName"],
                "type": type_course,
                "driver_id": r["Driver"]["driverId"],
                "pilote": f"{r['Driver']['givenName']} {r['Driver']['familyName']}",
                "ecurie": r["Constructor"]["name"],
                "position_arrivee": int(position) if position else None,
                "points": float(r.get("points", 0)),
            })
    return lignes


def get_resultats_saison(saison: int) -> pd.DataFrame:
    """Une ligne par pilote et par course (course principale + sprints)."""
    _valider_saison(saison)
    try:
        courses = _recuperer_courses(f"{URL_BASE}/{saison}/results/")
        sprints = _recuperer_courses(f"{URL_BASE}/{saison}/sprint/")
    except requests.RequestException as erreur:
        print(f"Erreur réseau : {erreur}")
        return pd.DataFrame()

    lignes = _aplatir(courses, "Results", "Course")
    lignes += _aplatir(sprints, "SprintResults", "Sprint")
    return pd.DataFrame(lignes)


if __name__ == "__main__":
    print(get_resultats_saison(2025).head())