import streamlit as st
import pandas as pd
import json
import os

COLUMN_ORDER = [
    "eventName",
    "team",
    "match",
    "name",
    "scoutingTeam",
    "teamNumber",
    "matchNumber",
    "autoFuel",
    "autoUnderTrench",
    "autoClimbed",
    "transitionFuel",
    "shift1HubActive",
    "shift1Fuel",
    "shift1Defense",
    "shift2HubActive",
    "shift2Fuel",
    "shift2Defense",
    "shift3HubActive",
    "shift3Fuel",
    "shift3Defense",
    "shift4HubActive",
    "shift4Fuel",
    "shift4Defense",
    "endgameFuel",
    "endgameClimbLevel",
    "crossedBump",
    "underTrench",
    "robotError",
    "notes",
]

NUMERIC_GRADIENT_COLUMNS = [
    "transitionFuel",
    "shift1Fuel",
    "shift2Fuel",
    "shift3Fuel",
    "shift4Fuel",
    "autoFuel",
    "endgameFuel",
]


def loadAndFlattenData(filePath):
    try:
        with open(filePath, "r") as f:
            fullData = json.load(f)

        rootData = fullData.get("root", {})
        st.write(f"✓ Loaded data for {len(rootData)} teams")

        rows = []
        for teamNum, matches in rootData.items():
            for matchId, matchFields in matches.items():
                row = {"team": teamNum, "match": matchId}

                # Iterate fields
                for key, value in matchFields.items():
                    if key == "robotError" and isinstance(value, dict):
                        trueErrors = [k for k, v in value.items() if v is True]
                        row[key] = ", ".join(trueErrors)
                    else:
                        row[key] = value
                rows.append(row)
        return rows
    except Exception as e:
        st.error(f"Error loading JSON: {e}")
        return []


def color_numeric_cell(val, max_val):
    """Generate a color gradient for numeric values."""
    if not isinstance(val, (int, float)) or max_val == 0:
        return "background-color: white"

    ratio = min(max(val / max_val, 0), 1)
    r = int(255 - (75 * ratio))
    g = int(180 + (75 * ratio))
    return f"background-color: rgb({r}, {g}, 180)"


def color_boolean_cell(val):
    """Generate a color for boolean values."""
    if val is True:
        return "background-color: #d4edda"  # Light Green
    elif val is False:
        return "background-color: #f8d7da"  # Light Red
    else:
        return "background-color: white"


# Streamlit App
st.set_page_config(page_title="Raw Scouting Data", layout="wide")
st.title("📊 Raw Scouting Data Viewer")
data_path = os.path.join(os.path.dirname(__file__), "..", "fetched_data.json")
allRows = loadAndFlattenData(data_path)

tab1, tab2 = st.tabs(["Data", "ranker"])
df = pd.DataFrame(pd.read_csv("avgs.csv"))

criteria_mapping = {
    "auto points": "avgAutoFuel",
    "auto climb": "autoClimbPercent",
    "transition": "avgTransitionFuel",
    "first shift": "avgFirstActiveHubFuel",
    "second shift": "avgSecondActiveHubFuel",
    "Endgame Points": "avgEndgameFuel",
    "Climb": "endgameAvgClimbPoints",
}


extra_df = pd.DataFrame(pd.read_csv("custom.csv"))


def update(m1, m2, m3, m4, m5, m6):
    row = {
        "multiplier1": m1,
        "multiplier2": m2,
        "multiplier3": m3,
        "multiplier4": m4,
        "multiplier5": m5,
        "multiplier6": m6,
    }
    extra_df = pd.read_csv("custom.csv")
    extra_df = pd.concat([extra_df, pd.DataFrame([row])], ignore_index=True)
    extra_df.to_csv("custom.csv", index=False)


max_rows = len(df[["teamNumber"]])

with tab1:
    if allRows:
        df = pd.DataFrame(allRows)
        allKeys = set(df.columns)
        orderedCols = [c for c in COLUMN_ORDER if c in allKeys]
        otherCols = sorted(list(allKeys - set(COLUMN_ORDER)))
        finalColumns = orderedCols + otherCols

        df = df[finalColumns]

        st.sidebar.header("Filters")

        if "teamNumber" in df.columns:
            teams = sorted(df["teamNumber"].unique().astype(str))
            selected_teams = st.sidebar.multiselect(
                "Filter by Team", teams, default=teams[:5]
            )
            df = df[df["teamNumber"].astype(str).isin(selected_teams)]

        if "eventName" in df.columns:
            events = sorted(df["eventName"].dropna().unique())
            selected_events = st.sidebar.multiselect(
                "Filter by Event", events, default=events if events else []
            )
            if selected_events:
                df = df[df["eventName"].isin(selected_events)]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Records", len(df))
        col2.metric(
            "Unique Teams",
            df["teamNumber"].nunique() if "teamNumber" in df.columns else 0,
        )
        col3.metric(
            "Unique Matches",
            df["matchNumber"].nunique() if "matchNumber" in df.columns else 0,
        )

        st.divider()

        st.subheader("Scouting Data Table")

        styled_df = df.copy()

        for col in NUMERIC_GRADIENT_COLUMNS:
            if col in styled_df.columns:
                max_val = pd.to_numeric(styled_df[col], errors="coerce").max()
                styled_df[col] = styled_df[col].apply(
                    lambda x: f"{x}" if pd.notna(x) else ""
                )

        st.dataframe(
            styled_df,
            use_container_width=True,
            height=600,
            column_config={
                "notes": st.column_config.TextColumn(width=250),
                "robotError": st.column_config.TextColumn(width=200),
                "eventName": st.column_config.TextColumn(width=150),
            },
        )

        st.divider()
        st.subheader("Export Options")
    else:
        st.warning("No data to display. Please ensure fetched_data.json exists.")

df = pd.DataFrame(pd.read_csv("avgs.csv"))

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


def update(m1, m2, m3, m4, m5, m6):
    row = {
        "multiplier1": m1,
        "multiplier2": m2,
        "multiplier3": m3,
        "multiplier4": m4,
        "multiplier5": m5,
        "multiplier6": m6,
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
                st.session_state["multiplier_1"],
                st.session_state["multiplier_2"],
                st.session_state["multiplier_3"],
                st.session_state["multiplier_4"],
                st.session_state["multiplier_5"],
                st.session_state["multiplier_6"],
            )
            extra_df = pd.DataFrame(pd.read_csv("custom.csv"))
            df["avgAutoFuel"] = (
                df["avgAutoFuel"].astype(object) * extra_df.iloc[-1][f"multiplier1"]
            )
            df["avgTransitionFuel"] = (
                df["avgTransitionFuel"].astype(object)
                * extra_df.iloc[-1][f"multiplier2"]
            )
            df["avgFirstActiveHubFuel"] = (
                df["avgFirstActiveHubFuel"].astype(object)
                * extra_df.iloc[-1][f"multiplier3"]
            )
            df["avgSecondActiveHubFuel"] = (
                df["avgSecondActiveHubFuel"].astype(object)
                * extra_df.iloc[-1][f"multiplier4"]
            )
            df["avgEndgameFuel"] = (
                df["avgEndgameFuel"].astype(object) * extra_df.iloc[-1][f"multiplier5"]
            )
            df["avgTotalFuel"] = (
                df["avgTotalFuel"].astype(object) * extra_df.iloc[-1][f"multiplier6"]
            )

    with col3:
        selector_1_multiplier = st.text_input(label, key="multiplier_1")
    with col4:
        selector_2_multiplier = st.text_input(label, key="multiplier_2")
    with col5:
        selector_3_multiplier = st.text_input(label, key="multiplier_3")
    with col6:
        selector_4_multiplier = st.text_input(label, key="multiplier_4")
    with col7:
        selector_4_multiplier = st.text_input(label, key="multiplier_5")
    with col8:
        selector_4_multiplier = st.text_input(label, key="multiplier_6")

    st.data_editor(
        df,
        column_order=(
            "teamNumber",
            "entries",
            "avgAutoFuel",
            "avgTransitionFuel",
            "avgFirstActiveHubFuel",
            "avgSecondActiveHubFuel",
            "avgEndgameFuel",
            "avgTotalFuel",
        ),
        hide_index=True,
        disabled=["widgets"],
        key="chud",
    )
