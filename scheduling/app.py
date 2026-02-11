import streamlit as st
import pandas as pd
import json
import os
from PIL import Image
from io import BytesIO
import requests
from st_image_button import st_image_button
from ranking import read_matches

ranked = read_matches()


def load_image_from_url(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return img


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


st.set_page_config(page_title="Raw Scouting Data", layout="wide")
st.title("📊 Raw Scouting Data Viewer")
data_path = os.path.join(os.path.dirname(__file__), "..", "fetched_data.json")
allRows = loadAndFlattenData(data_path)

tab1, tab2 = st.tabs(["Data", "ranker"])
df = pd.DataFrame(pd.read_csv("avgs.csv"))

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
criteria_mapping = {
    "rank": "rank",
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
        "multiplier6": 1,
    }
    extra_df = pd.read_csv("custom.csv")
    extra_df = pd.concat([extra_df, pd.DataFrame([row])], ignore_index=True)
    extra_df.to_csv("custom.csv", index=False)


max_rows = len(df[["teamNumber"]])

with tab1:
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
with tab2:
    df = pd.read_csv("avgs.csv")
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    label = "multiplier"
    if "Pickability" in df.columns:
        df["Pickability"] = pd.to_numeric(df["Pickability"], errors="coerce").fillna(0)
    else:
        df["Pickability"] = 0.0
    with col1:
        if st.button("$\\Large\\text{🥭}$"):

            update(
                st.session_state.get("multiplier_1", 1),
                st.session_state.get("multiplier_2", 1),
                st.session_state.get("multiplier_3", 1),
                st.session_state.get("multiplier_4", 1),
                st.session_state.get("multiplier_5", 1),
                st.session_state.get("multiplier_6", 1),
            )

    # Place text inputs in the columns
    with col2:
        st.number_input("Auto", key="multiplier_1", value=1)
    with col3:
        st.number_input("Trans", key="multiplier_2", value=1)
    with col4:
        st.number_input("Shift 1", key="multiplier_3", value=1)
    with col5:
        st.number_input("Shift 2", key="multiplier_4", value=1)
    with col6:
        st.number_input("Endgame", key="multiplier_5", value=1)
    with col7:
        st.number_input("Total", key="multiplier_6", value=1)

    # 2. Prepare the Display DataFrame
    # We create a copy so we don't modify the source data incorrectly
    display_df = df.copy()

    # 3. Calculate Ranks without saving to the original 'df'
    def get_rank(team_num):
        try:
            # Clean team number and look up in the 'ranked' list from ranking.py
            clean_team = int(float(str(team_num).replace(".0", "")))
            return ranked.index(clean_team) + 1
        except (ValueError, IndexError):
            return None

    # Insert 'Live Rank' at the beginning of the chart
    display_df.insert(0, "Live Rank", display_df["teamNumber"].apply(get_rank))

    # 4. Render the Chart
    st.subheader("Ranked Performance Overview")
    st.data_editor(
        display_df,
        column_order=(
            "Live Rank",
            "teamNumber",
            "entries",
            "Pickability",
            "avgAutoFuel",
            "avgTransitionFuel",
            "avgFirstActiveHubFuel",
            "avgSecondActiveHubFuel",
            "avgEndgameFuel",
            "avgTotalFuel",
        ),
        hide_index=True,
        use_container_width=True,
        disabled=True,  # Keeps it read-only
        key="rank_editor_view",
    )
