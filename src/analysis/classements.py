import pandas as pd


def classement_pilotes(resultats: pd.DataFrame) -> pd.DataFrame:
    """Tous les points du pilote, avec son écurie actuelle (celle de sa dernière manche)."""
    if resultats.empty:
        return pd.DataFrame()

    ecurie_actuelle = (
        resultats.sort_values("manche")
        .groupby("driver_id")["ecurie"]
        .last()
        .rename("ecurie")
    )
    points = resultats.groupby("driver_id")["points"].sum()
    victoires = (
        resultats[(resultats["type"] == "Course") & (resultats["position_arrivee"] == 1)]
        .groupby("driver_id")
        .size()
        .rename("victoires")
    )
    noms = resultats.drop_duplicates("driver_id").set_index("driver_id")["pilote"]

    df = pd.concat([noms, points, victoires, ecurie_actuelle], axis=1)
    df["victoires"] = df["victoires"].fillna(0).astype(int)
    df = df.sort_values(["points", "victoires"], ascending=False).reset_index(drop=True)
    df.insert(0, "position", df.index + 1)
    return df


def classement_constructeurs(resultats: pd.DataFrame, saison: int) -> pd.DataFrame:
    """Chaque course rapporte ses points à l'écurie du jour."""
    if resultats.empty or saison < 1958:  # pas de championnat constructeurs avant 1958
        return pd.DataFrame()

    df = (
        resultats.groupby("ecurie", as_index=False)["points"]
        .sum()
        .sort_values("points", ascending=False)
        .reset_index(drop=True)
    )
    df.insert(0, "position", df.index + 1)
    return df