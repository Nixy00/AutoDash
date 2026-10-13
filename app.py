from datetime import date
import plotly.express as px
import streamlit as st

from src.analysis.standings import (
    constructor_standings,
    cumulative_points,
    driver_standings,
    driver_stats,
)
from src.ingestion.f1_api import get_season_calendar, get_season_results

TEAM_COLORS = {
    "Ferrari": "#E8002D",
    "McLaren": "#FF8000",
    "Red Bull": "#3671C6",
    "Mercedes": "#27F4D2",
    "Aston Martin": "#229971",
    "Alpine F1 Team": "#FF87BC",
    "Williams": "#64C4FF",
    "RB F1 Team": "#6692FF",
    "Sauber": "#52E252",
    "Haas F1 Team": "#B6BABD",
}

LABELS = {
    "position": "Position",
    "driver": "Pilote",
    "team": "Écurie",
    "points": "Points",
    "wins": "Victoires",
    "round": "Manche",
    "cumulative_points": "Points cumulés",
}

CURRENT_YEAR = date.today().year
st.set_page_config(page_title="AutoDash", layout="wide")
st.title("AutoDash : F1")


@st.cache_data(ttl=3600)
def load_results(season: int):
    return get_season_results(season)


@st.cache_data(ttl=3600)
def load_calendar(season: int):
    return get_season_calendar(season)

season = st.sidebar.selectbox("Saison", range(CURRENT_YEAR, 1949, -1))
results = load_results(season)
calendar = load_calendar(season)

if results.empty:
    if season == CURRENT_YEAR and not calendar.empty:
        first_race = calendar.iloc[0]
        st.info(
            f"La saison {season} n'a pas encore commencé. "
            f"Première course : {first_race['race']} le {first_race['date']:%d/%m/%Y}."
        )
    else:
        st.warning(f"Aucune donnée disponible pour la saison {season}.")
    st.stop()

last_round = int(results["round"].max())
last_race = results.loc[results["round"] == last_round, "race"].iloc[0]
total_rounds = len(calendar)

if calendar.empty:
    st.caption(f"Résultats jusqu'à la manche {last_round} ({last_race}).")
elif last_round < total_rounds:
    next_race = calendar[calendar["round"] == last_round + 1].iloc[0]
    st.info(
        f"Saison en cours : après la manche {last_round} sur {total_rounds} ({last_race}). "
        f"Prochaine course : {next_race['race']} le {next_race['date']:%d/%m/%Y}."
    )
else:
    st.caption(f"Saison terminée : {total_rounds} manches.")

drivers = driver_standings(results)
teams = constructor_standings(results, season)

drivers_tab, teams_tab, profile_tab = st.tabs(["Pilotes", "Constructeurs", "Fiche pilote"])

with drivers_tab:
    fig = px.bar(
        drivers, x="driver", y="points", color="team",
        color_discrete_map=TEAM_COLORS, labels=LABELS,
        title=f"Points par pilote, saison {season}",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(drivers.rename(columns=LABELS), hide_index=True)

with teams_tab:
    if teams.empty:
        st.info("Pas de championnat constructeurs avant 1958.")
    else:
        fig = px.bar(
            teams, x="team", y="points", color="team",
            color_discrete_map=TEAM_COLORS, labels=LABELS,
            title=f"Points par écurie, saison {season}",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(teams.rename(columns=LABELS), hide_index=True)

with profile_tab:
    driver_list = drivers["driver"].tolist()
    selected = st.multiselect(
        "Pilotes à comparer",
        options=driver_list,
        default=driver_list[:2],
    )

    if not selected:
        st.info("Choisis au moins un pilote.")
    else:
        progress = cumulative_points(results)
        progress = progress[progress["driver"].isin(selected)]

        fig = px.line(
            progress, x="round", y="cumulative_points", color="driver",
            markers=True, labels=LABELS,
            title=f"Évolution des points, saison {season}",
        )
        st.plotly_chart(fig, use_container_width=True)

        for name in selected:
            stats = driver_stats(results, name)
            if not stats:
                continue

            st.subheader(name)
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.metric("Courses", stats["races"])
            col2.metric("Points", f"{stats['points']:g}")
            col3.metric("Victoires", stats["wins"])
            col4.metric("Podiums", stats["podiums"])

            best = stats["best_position"]
            col5.metric("Meilleure place", best if best is not None else "-")
            col6.metric("Abandons", stats["retirements"])