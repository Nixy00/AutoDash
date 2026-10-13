import plotly.express as px
import streamlit as st

from src.analysis.standings import constructor_standings, driver_standings
from src.ingestion.f1_api import get_season_results

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
}

st.set_page_config(page_title="AutoDash", layout="wide")
st.title("AutoDash : F1")


@st.cache_data(ttl=3600)
def load_results(season: int):
    return get_season_results(season)


season = st.sidebar.selectbox("Saison", range(2025, 1949, -1))
results = load_results(season)

if results.empty:
    st.warning(f"Aucune donnée disponible pour la saison {season}.")
    st.stop()

drivers = driver_standings(results)
teams = constructor_standings(results, season)

drivers_tab, teams_tab = st.tabs(["Pilotes", "Constructeurs"])

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