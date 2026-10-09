import streamlit as st
import pandas as pd
import plotly.express as px
from src.ingestion.f1_api import get_classement_pilotes

st.set_page_config(page_title="Dashboard F1", layout="wide")
st.title("Dashboard F1 : exemple")

df = get_classement_pilotes(2025)

ecuries = st.sidebar.multiselect(
    "Écuries", options=df["ecurie"].unique(), default=list(df["ecurie"].unique())
)
df_filtre = df[df["ecurie"].isin(ecuries)]

fig = px.bar(df_filtre, x="pilote", y="points", color="ecurie", title="Points par pilote")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(df_filtre)