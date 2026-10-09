import plotly.express as px
import streamlit as st

from src.analysis.classements import classement_constructeurs, classement_pilotes
from src.ingestion.f1_api import get_resultats_saison

COULEURS_ECURIES = {
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

st.set_page_config(page_title="AutoDash", layout="wide")
st.title("AutoDash : F1")


@st.cache_data(ttl=3600)
def charger_resultats(saison: int):
    return get_resultats_saison(saison)


saison = st.sidebar.selectbox("Saison", range(2025, 1949, -1))
resultats = charger_resultats(saison)

if resultats.empty:
    st.warning(f"Aucune donnée disponible pour la saison {saison}.")
    st.stop()

pilotes = classement_pilotes(resultats)
constructeurs = classement_constructeurs(resultats, saison)

onglet_pilotes, onglet_constructeurs = st.tabs(["Pilotes", "Constructeurs"])

with onglet_pilotes:
    fig = px.bar(pilotes, x="pilote", y="points", color="ecurie",
                 color_discrete_map=COULEURS_ECURIES,
                 title=f"Points par pilote, saison {saison}")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(pilotes, hide_index=True)

with onglet_constructeurs:
    if constructeurs.empty:
        st.info("Pas de championnat constructeurs avant 1958.")
    else:
        fig = px.bar(constructeurs, x="ecurie", y="points", color="ecurie",
                     color_discrete_map=COULEURS_ECURIES,
                     title=f"Points par écurie, saison {saison}")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(constructeurs, hide_index=True)