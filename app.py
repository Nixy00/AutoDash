from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st

from src.analysis.simulation import (
    POSITION_CHOICES,
    apply_scenario,
    check_scenario,
    max_points_left,
    remaining_event_list,
    remaining_events,
    title_contenders,
)
from src.analysis.standings import (
    apply_official_points,
    constructor_standings,
    cumulative_points,
    driver_standings,
    driver_stats,
)
from src.ingestion.f1_api import (
    get_official_driver_standings,
    get_season_calendar,
    get_season_results,
)

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
    "gap": "Écart au leader",
    "max_possible": "Maximum atteignable",
    "can_win": "Encore en course",
    "extra_points": "Points du scénario",
    "final_points": "Total final",
}

CURRENT_YEAR = date.today().year
st.set_page_config(page_title="AutoDash", layout="wide")
st.title("AutoDash : F1")


@st.cache_data(ttl=3600)
def load_results(year: int):
    return get_season_results(year)


@st.cache_data(ttl=3600)
def load_calendar(year: int):
    return get_season_calendar(year)


@st.cache_data(ttl=3600)
def load_official_standings(year: int):
    return get_official_driver_standings(year)


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

official = load_official_standings(season)
drivers = apply_official_points(driver_standings(results), official)
teams = constructor_standings(results, season)

drivers_tab, teams_tab, profile_tab, simulation_tab = st.tabs(
    ["Pilotes", "Constructeurs", "Fiche pilote", "Simulation"]
)

with drivers_tab:
    fig = px.bar(
        drivers, x="driver", y="points", color="team",
        color_discrete_map=TEAM_COLORS, labels=LABELS,
        title=f"Points par pilote, saison {season}",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(drivers.drop(columns="driver_id").rename(columns=LABELS), hide_index=True)

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

with simulation_tab:
    if season != CURRENT_YEAR or calendar.empty:
        st.info("La simulation est disponible uniquement pour la saison en cours.")
    else:
        races_left, sprints_left = remaining_events(results, calendar)
        max_left = max_points_left(races_left, sprints_left)

        if races_left == 0:
            st.info("La saison est terminée, il n'y a plus rien à simuler.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Courses restantes", races_left)
            col2.metric("Sprints restants", sprints_left)
            col3.metric("Points max en jeu", max_left)

            contenders = title_contenders(drivers, max_left)
            still_in = contenders[contenders["can_win"]]

            if len(still_in) == 1:
                st.success(f"{still_in.iloc[0]['driver']} est déjà champion du monde !")
            else:
                st.info(f"{len(still_in)} pilotes peuvent encore être champions.")

            leader_points = drivers["points"].max()
            fig = px.bar(
                still_in, x="driver", y="max_possible", color="team",
                color_discrete_map=TEAM_COLORS, labels=LABELS,
                title="Points maximum atteignables par les prétendants",
            )
            fig.add_hline(
                y=leader_points, line_dash="dash",
                annotation_text=f"Leader actuel : {leader_points:g} pts",
            )
            st.plotly_chart(fig, use_container_width=True)

            display = contenders.copy()
            display["can_win"] = display["can_win"].map({True: "Oui", False: "Non"})
            st.dataframe(display.rename(columns=LABELS), hide_index=True)

            if len(still_in) > 1:
                st.subheader("Et si... ?")
                st.caption(
                    "Choisis le résultat des pilotes pour chaque course restante : "
                    "une position, DNF (abandon), DNS (non partant) ou DSQ (disqualifié). "
                    "Hypothèse : les autres pilotes ne marquent plus de points."
                )

                contender_names = still_in["driver"].tolist()
                chosen = st.multiselect(
                    "Pilotes du scénario",
                    options=contender_names,
                    default=contender_names[:2],
                    key="scenario_drivers",
                )

                if len(chosen) < 2:
                    st.info("Choisis au moins deux pilotes.")
                else:
                    grid = remaining_event_list(results, calendar)
                    for i, name in enumerate(chosen):
                        grid[name] = str(i + 1)

                    column_config = {"event": st.column_config.TextColumn("Course")}
                    for name in chosen:
                        column_config[name] = st.column_config.SelectboxColumn(
                            name, options=POSITION_CHOICES, required=True,
                        )

                    edited = pd.DataFrame(st.data_editor(
                        grid,
                        column_order=["event"] + chosen,
                        column_config=column_config,
                        disabled=["event"],
                        hide_index=True,
                    ))

                    wrong_events = check_scenario(edited, chosen)
                    if wrong_events:
                        for event in wrong_events:
                            st.error(f"{event} : deux pilotes ont la même position.")
                    else:
                        final = apply_scenario(drivers, edited, chosen)
                        champion = final.iloc[0]
                        st.success(
                            f"Avec ce scénario, {champion['driver']} serait champion "
                            f"avec {champion['final_points']:g} points."
                        )

                        top = final.head(10).rename(columns={
                            "points": "Points actuels",
                            "extra_points": "Points du scénario",
                        })
                        fig = px.bar(
                            top, x="driver", y=["Points actuels", "Points du scénario"],
                            labels={"driver": "Pilote", "value": "Points", "variable": ""},
                            title="Classement final avec ce scénario (top 10)",
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        st.dataframe(final.rename(columns=LABELS), hide_index=True)