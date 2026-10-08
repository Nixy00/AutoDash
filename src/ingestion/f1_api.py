import requests
import pandas as pd

URL_BASE = "https://api.jolpi.ca/ergast/f1"

def get_classement_pilotes(saison: int) -> pd.DataFrame:
    """Retourne le classement pilotes d'une saison sous forme de dataframe."""
    url = f"{URL_BASE}/{saison}/driverstandings/"

    try:
        reponse = requests.get(url, timeout=10)
    except requests.RequestException as erreur:
        print(f"Erreur réseau : {erreur}")
        return pd.DataFrame()

    if reponse.status_code != 200:
        print(f"Erreur lors de la requête : {reponse.status_code}")
        return pd.DataFrame()

    data = reponse.json()
    listes = data["MRData"]["StandingsTable"]["StandingsLists"]

    if not listes:
        return pd.DataFrame()

    lignes = []
    for pilote in listes[0]["DriverStandings"]:
        ecuries = " / ".join(c["name"] for c in pilote["Constructors"])
        lignes.append({
            "position": int(pilote["position"]),
            "pilote": f"{pilote['Driver']['givenName']} {pilote['Driver']['familyName']}",
            "points": float(pilote["points"]),
            "victoires": int(pilote["wins"]),
            "ecurie": ecuries,
        })

    return pd.DataFrame(lignes)


if __name__ == "__main__":
    df = get_classement_pilotes(2025)
    print(df.head())