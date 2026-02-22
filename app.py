import streamlit as st
import pandas as pd
import json
import os
from PIL import Image
from io import BytesIO
import requests
from st_image_button import st_image_button
from ranking import read_matches
from bluealliance import fetch as bfetch
from fetchfromdb import fetch as ffetch
from pieceviewer import processTeamAverages
from json_to_csv import convert_avgs_to_csv

#ffetch()
bfetch("matches")
bfetch("rankings")
with open("avgs.json", "w") as goy:
    json.dump(processTeamAverages("fetched_data.json"), goy, indent=4)

convert_avgs_to_csv()

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
        print(len(rows))
        return rows
    except Exception as e:
        st.error(f"Error loading JSON: {e}")
        return []

st.set_page_config(page_title="Raw Scouting Data", layout="wide")
st.title("📊 Raw Scouting Data Viewer")
data_path = "fetched_data.json"
allRows = loadAndFlattenData(data_path)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["data", "ranker", "matches", "STD predictor", "Game Predictor"])
df = pd.DataFrame(pd.read_csv("avgs.csv"))

with tab1:
    if allRows:
        df = pd.DataFrame(allRows)
        allKeys = set(df.columns)
        orderedCols = [c for c in COLUMN_ORDER if c in allKeys]
        otherCols = sorted(list(allKeys - set(COLUMN_ORDER)))
        finalColumns = orderedCols + otherCols

        df = df[finalColumns]

        with open("fetched_data.json", "r") as goy:
            # Ensure teamList contains strings to match the multiselect options
            teamsList = [str(t) for t in json.load(goy).get("team", [])]

        st.sidebar.header("Filters")

        if "teamNumber" in df.columns:
            # Get all possible teams from the dataframe
            all_teams = sorted(df["teamNumber"].unique().astype(str))
            
            # 2. Initialize the session state for the multiselect if it doesn't exist
            if "selected_teams" not in st.session_state:
                st.session_state.selected_teams = all_teams

            # 3. Create the Reset/Select All button
            # When clicked, it updates the session state directly
            if st.sidebar.button("Select All Teams", key="diddy"):
                st.session_state.selected_teams = teamsList

            # 4. Link the multiselect to the session state
            selected_teams = st.sidebar.multiselect(
                "Filter by Team", 
                options=all_teams, 
                key="team_selector",
                default=st.session_state.selected_teams 
            )

            # 5. Filter the dataframe
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


def update( m1, m2, m3, m4,m5,m6):
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
        if st_image_button("","dog.jpeg", width=125, key="floyd"):
            update(
                st.session_state.get("multiplier_1", 1.00),
                st.session_state.get("multiplier_2", 1.00),
                st.session_state.get("multiplier_3", 1.00),
                st.session_state.get("multiplier_4", 1.00),
                st.session_state.get("multiplier_5", 1.00),
                st.session_state.get("multiplier_6", 1.00),
            )
            extra_df = pd.DataFrame(pd.read_csv("custom.csv"))
            df["avgAutoFuel"]=df["avgAutoFuel"].astype(float) * extra_df.iloc[-1][f"multiplier1"]
            df["avgTransitionFuel"]=df["avgTransitionFuel"].astype(float) * extra_df.iloc[-1][f"multiplier2"]
            df["avgFirstActiveHubFuel"]=df["avgFirstActiveHubFuel"].astype(float) * extra_df.iloc[-1][f"multiplier3"]
            df["avgSecondActiveHubFuel"]=df["avgSecondActiveHubFuel"].astype(float) * extra_df.iloc[-1][f"multiplier4"]
            df["avgEndgameFuel"]=df["avgEndgameFuel"].astype(float) * extra_df.iloc[-1][f"multiplier5"]
            df["avgTotalFuel"]=df["avgTotalFuel"].astype(float) * extra_df.iloc[-1][f"multiplier6"]
        updated_list = ["multiplier1","multiplier2","multiplier3","multiplier4","multiplier5","multiplier6"]
        categories = ["avgAutoFuel","avgTransitionFuel","avgFirstActiveHubFuel","avgSecondActiveHubFuel","avgEndgameFuel","avgTotalFuel"]
        pickability_list = []
        for i in range(0,6):
            if extra_df.iloc[-1][updated_list[i]] == 1:
                pass
            else:
                pickability_list.append(extra_df.iloc[-1][updated_list[i]]*df[categories[i]].astype(float))
        df["Pickability"] = sum(pickability_list)
    with col2:
        st.number_input("Auto", key="multiplier_1", value=1.00)
    with col3:
        st.number_input("Trans", key="multiplier_2", value=1.00)
    with col4:
        st.number_input("Shift 1", key="multiplier_3", value=1.00)
    with col5:
        st.number_input("Shift 2", key="multiplier_4", value=1.00)
    with col6:
        st.number_input("Endgame", key="multiplier_5", value=1.00)
    with col7:
        st.number_input("Total", key="multiplier_6", value=1.00)

    display_df = df.copy()

    def get_rank(team_num):
        try:
            clean_team = int(float(str(team_num).replace(".0", "")))
            return ranked.index(clean_team) + 1
        except (ValueError, IndexError):
            return None

    display_df.insert(0, "Live Rank", display_df["teamNumber"].apply(get_rank))

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
        disabled=True,  
        key="chud",
    )
with tab3:
    # Configuration
    teamsGroup = [
        ["a", "b", "c", "d", "e", "f"],
        ["g", "h", "i", "j", "k", "l"],
        ["m", "n", "o", "p", "q", "r"],
    ]
    matchOrder = [0, 1, 2, 1, 2, 1, 0]


    def getStackedCell(items, colors=None):
        """Generates a stacked HTML cell to replicate the layout."""
        htmlString = '<div style="display: flex; flex-direction: column; height: 100%; width: 100%; border: 1px solid #ccc; border-radius: 4px; overflow: hidden;">'
        for i, item in enumerate(items):
            bgColor = colors[i] if colors else "transparent"
            borderStyle = "border-bottom: 1px solid #ccc;" if i < len(items) - 1 else ""

            htmlString += f"""<div style="background-color: {bgColor}; 
                            flex: 1; padding: 4px; text-align: center; font-weight: bold; {borderStyle}">
                            {item}
                            </div>"""
        htmlString += "</div>"
        return htmlString


    def main():
        st.set_page_config(page_title="Match Schedule", layout="wide")
        st.title("📋 Match Schedule & Scout Verification")

        # Load TBA Match Schedule
        try:
            with open("matches.json", "r") as file:
                matchList = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            st.error("Error: Could not load tba_matches.json.")
            return

        # Load Scouting Data
        try:
            with open("fetched_data.json", "r") as file:
                scoutingData = json.load(file).get("root", {})
        except (FileNotFoundError, json.JSONDecodeError):
            scoutingData = {}

        # Header Row
        st.divider()
        h1, h2, h3, h4 = st.columns([1, 2, 2, 2])
        h1.write("**Match / Score**")
        h2.write("**Teams (Red/Blue)**")
        h3.write("**Assigned Scouters**")
        h4.write("**Scout Check (Status)**")
        st.divider()

        for idx, match in enumerate(matchList):
            if not isinstance(match, dict):
                continue

            matchNum = match.get("match_number", idx + 1)
            matchStr = str(matchNum)
            compLevel = match.get("comp_level", "qm").upper()
            alliances = match.get("alliances", {})

            # Alliance Scores
            redScore = alliances.get("red", {}).get("score", 0)
            blueScore = alliances.get("blue", {}).get("score", 0)

            # Get Team Keys
            redKeys = [
                t.replace("frc", "") for t in alliances.get("red", {}).get("team_keys", [])
            ]
            blueKeys = [
                t.replace("frc", "") for t in alliances.get("blue", {}).get("team_keys", [])
            ]
            displayTeams = redKeys + blueKeys

            if len(displayTeams) < 6:
                continue

            allianceColors = ["#8B0000"] * 3 + ["#00008B"] * 3

            # Scouter Assignments
            assignedScouters = teamsGroup[matchOrder[idx % len(matchOrder)]]

            # Scout Verification Logic
            checkLabels = []
            checkColors = []

            for i in range(6):
                teamNum = displayTeams[i]
                assignedName = assignedScouters[i]

                # Navigate JSON: root -> teamNum -> matchNum -> name
                teamData = scoutingData.get(teamNum, {})
                matchData = teamData.get(matchStr, {})
                actualScouterName = matchData.get("name", "")

                if actualScouterName.lower() == assignedName.lower():
                    checkLabels.append(f"Verified: {actualScouterName}")
                    checkColors.append("#00ff1e")  # Green
                elif actualScouterName != "":
                    checkLabels.append(f"Wrong Scouter: {actualScouterName}")
                    checkColors.append("#636300")  # Yellow
                else:
                    checkLabels.append("Missing")
                    checkColors.append("#8B0000")  # Red

            # Render UI Row
            r1, r2, r3, r4 = st.columns([1, 2, 2, 2])

            with r1:
                st.markdown(f"### {compLevel} {matchNum}")
                st.markdown(f"**Red: {redScore}**")
                st.markdown(f"**Blue: {blueScore}**")

            with r2:
                st.markdown(
                    getStackedCell(displayTeams, allianceColors), unsafe_allow_html=True
                )

            with r3:
                st.markdown(getStackedCell(assignedScouters), unsafe_allow_html=True)

            with r4:
                st.markdown(
                    getStackedCell(checkLabels, checkColors), unsafe_allow_html=True
                )

            st.divider()


    if __name__ == "__main__":
        main()
with tab4:
    with open("teamPredictor1.json", "r") as goy:
        stds = json.load(goy)

    st.markdown(f"## Standard Deviation Predictor")
    st.markdown(f"### {stds.get("output_cell", "")}")


with tab5:
    with open("teamPredictor.json", "r") as goy:
        preds = json.load(goy)

    reds = preds.get("red_alliance", {})
    blues = preds.get("blue_alliance", {})

    rteams = reds.get("Teams", [])
    bteams = blues.get("Teams", [])
    st.markdown(f"## ")