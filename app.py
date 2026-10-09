import streamlit as st
import plotly.express as px
from src.ingestion.f1_api import get_classement_pilotes

st.set_page_config(page_title="AutoDash", layout="wide")
st.title("AutoDash : classement pilotes F1")


@st.cache_data(ttl=3600)
def charger_classement(saison):
    return get_classement_pilotes(saison)


saison = st.sidebar.selectbox("Saison", range(2025, 1949, -1))

df = charger_classement(saison)

if df.empty:
    st.warning(f"Aucune donnée disponible pour la saison {saison}.")
    st.stop()

ecuries = st.sidebar.multiselect(
    "Écuries", options=df["ecurie"].unique(), default=list(df["ecurie"].unique())
)
df_filtre = df[df["ecurie"].isin(ecuries)]

fig = px.bar(df_filtre, x="pilote", y="points", color="ecurie",
             title=f"Points par pilote, saison {saison}")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(df_filtre, hide_index=True)