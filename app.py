import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard F1", layout="wide")
st.title("Dashboard F1 : exemple")

# Données factices pour tester (on remplacera par la base PostgreSQL)
df = pd.DataFrame({
    "pilote": ["Verstappen", "Norris", "Leclerc", "Hamilton", "Piastri"],
    "points": [300, 280, 250, 200, 190],
    "ecurie": ["Red Bull", "McLaren", "Ferrari", "Ferrari", "McLaren"],
})

# Filtre interactif dans la barre latérale
ecuries = st.sidebar.multiselect(
    "Écuries", options=df["ecurie"].unique(), default=list(df["ecurie"].unique())
)
df_filtre = df[df["ecurie"].isin(ecuries)]

# Graphique interactif (zoom, survol, etc.)
fig = px.bar(df_filtre, x="pilote", y="points", color="ecurie", title="Points par pilote")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(df_filtre)