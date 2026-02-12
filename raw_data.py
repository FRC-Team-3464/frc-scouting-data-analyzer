import streamlit as st
import json
import os
import sys
import pandas as pd
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logger

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

if allRows:
    df = pd.DataFrame(allRows)
    allKeys = set(df.columns)
    orderedCols = [c for c in COLUMN_ORDER if c in allKeys]
    otherCols = sorted(list(allKeys - set(COLUMN_ORDER)))
    finalColumns = orderedCols + otherCols

    df = df[finalColumns]

    # Sidebar filters
    st.sidebar.header("Filters")

    # Team filter
    if "teamNumber" in df.columns:
        teams = sorted(df["teamNumber"].unique().astype(str))
        selected_teams = st.sidebar.multiselect(
            "Filter by Team", teams, default=teams[:5]
        )
        df = df[df["teamNumber"].astype(str).isin(selected_teams)]

    # Event filter
    if "eventName" in df.columns:
        events = sorted(df["eventName"].dropna().unique())
        selected_events = st.sidebar.multiselect(
            "Filter by Event", events, default=events if events else []
        )
        if selected_events:
            df = df[df["eventName"].isin(selected_events)]

    # Display statistics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records", len(df))
    col2.metric(
        "Unique Teams", df["teamNumber"].nunique() if "teamNumber" in df.columns else 0
    )
    col3.metric(
        "Unique Matches",
        df["matchNumber"].nunique() if "matchNumber" in df.columns else 0,
    )

    st.divider()

    # Display dataframe with styling
    st.subheader("Scouting Data Table")

    # Create styled dataframe
    styled_df = df.copy()

    # Apply numeric gradient coloring
    for col in NUMERIC_GRADIENT_COLUMNS:
        if col in styled_df.columns:
            max_val = pd.to_numeric(styled_df[col], errors="coerce").max()
            styled_df[col] = styled_df[col].apply(
                lambda x: f"{x}" if pd.notna(x) else ""
            )

    # Display with column customization
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

    # Export options
    st.divider()
    st.subheader("Export Options")

    col1, col2 = st.columns(2)
    
    with col2:
        json_data = df.to_json(orient="records", indent=2)
        st.download_button(
            label="📥 Download as JSON",
            data=json_data,
            file_name=f"scouting_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

else:
    st.warning("No data to display. Please ensure fetched_data.json exists.")
