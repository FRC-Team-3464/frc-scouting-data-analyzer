import streamlit as st
import pandas as pd

tab1, tab2 = st.tabs(["Data", "ranker"])
df = pd.DataFrame(pd.read_csv("avgs.csv"))

# Mapping from criteria to column names
criteria_mapping = {
    "auto points": "avgAutoFuel",
    "auto climb": "autoClimbPercent",
    "transition": "avgTransitionFuel",
    "first shift": "avgFirstActiveHubFuel",
    "second shift": "avgSecondActiveHubFuel",
    "Endgame Points": "avgEndgameFuel",
    "Climb": "endgameAvgClimbPoints",
}

import time

extra_df = pd.DataFrame(pd.read_csv("custom.csv"))


def update(s1, m1, s2, m2, s3, m3, s4, m4):
    row = {
        "multiplier1": m1,
        "selector1": s1,
        "multiplier2": m2,
        "selector2": s2,
        "multiplier3": m3,
        "selector3": s3,
        "multiplier4": m4,
        "selector4": s4,
    }
    extra_df = pd.read_csv("custom.csv")
    extra_df = pd.concat([extra_df, pd.DataFrame([row])], ignore_index=True)
    extra_df.to_csv("custom.csv", index=False)


max_rows = len(df[["teamNumber"]])

with tab1:
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    st.write("work in progress")
with tab2:

    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    label = "multiplier"
    with col1:
        if st.button("run"):
            update(
                st.session_state["selector_1"],
                st.session_state["multiplier_1"],
                st.session_state["selector_2"],
                st.session_state["multiplier_2"],
                st.session_state["selector_3"],
                st.session_state["multiplier_3"],
                st.session_state["selector_4"],
                st.session_state["multiplier_4"],
            )
            # Create a working copy and rename based on selected criteria
            df_copy = df.copy()
            df_copy = df_copy.rename(
                columns={
                    criteria_mapping[st.session_state["selector_1"]]: "Values1",
                    criteria_mapping[st.session_state["selector_2"]]: "Values2",
                    criteria_mapping[st.session_state["selector_3"]]: "Values3",
                    criteria_mapping[st.session_state["selector_4"]]: "Values4",
                }
            )
            extra_df = pd.DataFrame(pd.read_csv("custom.csv"))
            df_copy["Values1"] = (
                df_copy["Values1"].astype(object) * extra_df.iloc[-1][f"multiplier1"]
            )
            df_copy["Values2"] = (
                df_copy["Values2"].astype(object) * extra_df.iloc[-1][f"multiplier2"]
            )
            df_copy["Values3"] = (
                df_copy["Values3"].astype(object) * extra_df.iloc[-1][f"multiplier3"]
            )
            df_copy["Values4"] = (
                df_copy["Values4"].astype(object) * extra_df.iloc[-1][f"multiplier4"]
            )
            # Update the original df with the multiplied values
            for sel_idx, selector_key in enumerate(
                ["selector_1", "selector_2", "selector_3", "selector_4"], 1
            ):
                col_name = criteria_mapping[st.session_state[selector_key]]
                df[col_name] = df_copy[f"Values{sel_idx}"]

    with col5:
        selector_1 = st.selectbox(
            "Criteria",
            [
                "auto points",
                "auto climb",
                "transition",
                "first shift",
                "second shift",
                "Endgame Points",
                "Climb",
            ],
            key="selector_1",
        )
        selector_1_multiplier = st.text_input(label, key="multiplier_1")

    with col6:
        selector_2 = st.selectbox(
            "Criteria",
            ["auto points", "auto climb", "transition", "first shift", "second shift", "Endgame Points", "Climb"],
            key="selector_2",
        )
        selector_2_multiplier = st.text_input(label, key="multiplier_2")

    with col7:
        selector_3 = st.selectbox(
            "Criteria",
            [
                "auto points",
                "auto climb",
                "transition",
                "first shift",
                "second shift",
                "Endgame Points",
                "Climb",
            ],
            key="selector_3",
        )
        selector_3_multiplier = st.text_input(label, key="multiplier_3")

    with col8:
        selector_4 = st.selectbox(
            "Criteria",
            [
                "auto points",
                "auto climb",
                "transition",
                "first shift",
                "second shift",
                "Endgame Points",
                "Climb",
            ],
            key="selector_4",
        )
        selector_4_multiplier = st.text_input(label, key="multiplier_4")

    st.data_editor(
        df,
        column_order=(
            "teamNumber",
            "entries",
            criteria_mapping.get(
                st.session_state.get("selector_1", "AUTO points"), "avgAutoFuel"
            ),
            criteria_mapping.get(
                st.session_state.get("selector_2", "Teleop Points"), "avgTransitionFuel"
            ),
            criteria_mapping.get(
                st.session_state.get("selector_3", "Endgame Points"), "avgEndgameFuel"
            ),
            criteria_mapping.get(
                st.session_state.get("selector_4", "Climb"), "avgTotalFuel"
            ),
        ),
        hide_index=True,
        disabled=["widgets"],
        key="chud",
    )
