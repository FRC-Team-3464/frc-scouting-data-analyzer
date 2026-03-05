import streamlit as st
import pandas as pd
import time
import json
from PIL import Image
from io import BytesIO
import requests
from ranking import read_matches
from bluealliance import fetch as bFetch
from fetchfromdb import fetch as ffetch
from avgs import processTeamAverages
from jsonToCsv import convertAvgsToCsv
from st_image_button import st_image_button
from teamPredictor import main as predict
from stdTeamPredictor import predict as stdPred

"""
required pip installs:
pip install streamlit pandas st_image_button requests

with python 3.13
"""

# ffetch()
bFetch("matches")
bFetch("rankings")
with open("jsons/avgs.json", "w") as goy:
    json.dump(processTeamAverages("jsons/fetchedData.json"), goy, indent=4)
convertAvgsToCsv()
ranked = read_matches()

def loadImageFromUrl(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return img

columnOrder = [
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
    "transitionCollected",
    "shift1HubActive",
    "shift1Fuel",
    "shift1HoardedFuel",
    "shift1Collected",
    "shift1Defense",
    "shift2HubActive",
    "shift2Fuel",
    "shift2HoardedFuel",
    "shift2Collected",
    "shift2Defense",
    "shift3HubActive",
    "shift3Fuel",
    "shift3HoardedFuel",
    "shift3Collected",
    "shift3Defense",
    "shift4HubActive",
    "shift4Fuel",
    "shift4HoardedFuel",
    "shift4Collected",
    "shift4Defense",
    "endgameFuel",
    "endgameClimbLevel",
    "crossedBump",
    "underTrench",
    "robotError",
    "notes",
    "static",
    "multiTurret",
]

numericGradientColumns = [
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
        st.write(f"Loaded data for {len(rootData)} teams")

        rows = []

        for teamNum, matches in rootData.items():
            for matchId, matchFields in matches.items():
                row = {"team": teamNum, "match": matchId}

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
dataPath = "jsons/fetchedData.json"
allRows = loadAndFlattenData(dataPath)

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["individual", "data", "ranker", "matches", "STD predictor", "Game Predictor"]
)
df = pd.DataFrame(pd.read_csv("jsons/avgs.csv"))

extraDf = pd.DataFrame(pd.read_csv("mult.csv"))


def updateMultipliers(m1, m2, m3, m4, m5, m6):
    row = {
        "multiplier1": m1,
        "multiplier2": m2,
        "multiplier3": m3,
        "multiplier4": m4,
        "multiplier5": m5,
        "multiplier6": m6,
    }
    localExtraDf = pd.read_csv("mult.csv")
    localExtraDf = pd.concat([localExtraDf, pd.DataFrame([row])], ignore_index=True)
    localExtraDf.to_csv("mult.csv", index=False)


maxRows = len(df[["teamNumber"]])
criteriaMapping = {
    "rank": "rank",
    "auto points": "avgAutoFuel",
    "auto climb": "autoClimbPercent",
    "transition": "avgTransitionFuel",
    "first shift": "avgFirstActiveHubFuel",
    "second shift": "avgSecondActiveHubFuel",
    "Endgame Points": "avgEndgameFuel",
    "Climb": "endgameAvgClimbPoints",
}

with tab0:
    try:
        df = pd.read_csv("jsons/avgs.csv")
        df["teamNumber"] = df["teamNumber"].astype(str)
        teamList = sorted(df["teamNumber"].unique(), key=int)
    except FileNotFoundError:
        st.error("File 'jsons/avgs.csv' not found. Please check the file path.")

    st.header("Match Selection")
    redSel = st.multiselect("Red Alliance", teamList, max_selections=3)
    blueSel = st.multiselect("Blue Alliance", teamList, max_selections=3)

    def getAllianceTable(selectedTeams):
        if not selectedTeams:
            return None
        return df[df["teamNumber"].isin(selectedTeams)].copy()

    def displayAllianceSection(allianceData, colorLabel, themeColor):
        if allianceData is not None:
            st.markdown(f"### {colorLabel} Alliance")

            headerCol1, headerCol2 = st.columns([1, 4])
            with headerCol1:
                st.markdown(f":{themeColor}[**AUTO**]")
            with headerCol2:
                st.markdown(f":{themeColor}[**TELEOP & ENDGAME**]")

            st.dataframe(allianceData, hide_index=True)

            totalFuel = allianceData["avgTotalFuel"].sum()
            st.metric(f"{colorLabel} Total Avg", f"{totalFuel:.2f}")
            st.divider()

    displayAllianceSection(getAllianceTable(redSel), "Red", "red")
    displayAllianceSection(getAllianceTable(blueSel), "Blue", "blue")

with tab1:
    if allRows:
        df = pd.DataFrame(allRows)
        allKeys = set(df.columns)
        orderedCols = [c for c in columnOrder if c in allKeys]
        otherCols = sorted(list(allKeys - set(columnOrder)))
        finalColumns = orderedCols + otherCols

        df = df[finalColumns]

        with open("jsons/fetchedData.json", "r") as goy:
            teamsList = [str(t) for t in json.load(goy).get("team", [])]

        st.sidebar.header("Filters")

        if "teamNumber" in df.columns:
            allTeams = sorted(df["teamNumber"].unique().astype(str))
            if "selectedTeams" not in st.session_state:
                st.session_state.selectedTeams = allTeams

            if st.sidebar.button("Select All Teams", key="selectAllBtn"):
                st.session_state.selectedTeams = teamsList

            selectedTeams = st.sidebar.multiselect(
                "Filter by Team",
                options=allTeams,
                key="teamSelector",
                default=st.session_state.selectedTeams,
            )

            df = df[df["teamNumber"].astype(str).isin(selectedTeams)]

        if "eventName" in df.columns:
            events = sorted(df["eventName"].dropna().unique())
            selectedEvents = st.sidebar.multiselect(
                "Filter by Event", events, default=events if events else []
            )
            if selectedEvents:
                df = df[df["eventName"].isin(selectedEvents)]

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
        st.subheader("data")

        styledDf = df.copy()
        for col in numericGradientColumns:
            if col in styledDf.columns:
                styledDf[col] = styledDf[col].apply(
                    lambda x: f"{x}" if pd.notna(x) else ""
                )

        st.dataframe(
            styledDf,
            height=600,
            column_config={
                "notes": st.column_config.TextColumn(width=250),
                "robotError": st.column_config.TextColumn(width=200),
                "eventName": st.column_config.TextColumn(width=150),
            },
        )
    else:
        st.warning("No data to display. Please ensure jsons/fetchedData.json exists.")

with tab2:
    df = pd.read_csv("jsons/avgs.csv")
    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)

    if "Pickability" in df.columns:
        df["Pickability"] = pd.to_numeric(df["Pickability"], errors="coerce").fillna(0)
    else:
        df["Pickability"] = 0.0

    with c1:
        if st_image_button("", "dog.jpeg", width=125, key="dogBtn"):
            updateMultipliers(
                st.session_state.get("multiplier1", 1.00),
                st.session_state.get("multiplier2", 1.00),
                st.session_state.get("multiplier3", 1.00),
                st.session_state.get("multiplier4", 1.00),
                st.session_state.get("multiplier5", 1.00),
                st.session_state.get("multiplier6", 1.00),
            )
            extraDf = pd.DataFrame(pd.read_csv("mult.csv"))

            # Application of multipliers
            lastMults = extraDf.iloc[-1]
            df["avgAutoFuel"] = (
                df["avgAutoFuel"].astype(float) * lastMults["multiplier1"]
            )
            df["avgTransitionFuel"] = (
                df["avgTransitionFuel"].astype(float) * lastMults["multiplier2"]
            )
            df["avgFirstActiveHubFuel"] = (
                df["avgFirstActiveHubFuel"].astype(float) * lastMults["multiplier3"]
            )
            df["avgSecondActiveHubFuel"] = (
                df["avgSecondActiveHubFuel"].astype(float) * lastMults["multiplier4"]
            )
            df["avgEndgameFuel"] = (
                df["avgEndgameFuel"].astype(float) * lastMults["multiplier5"]
            )
            df["avgTotalFuel"] = (
                df["avgTotalFuel"].astype(float) * lastMults["multiplier6"]
            )

        updatedList = [
            "multiplier1",
            "multiplier2",
            "multiplier3",
            "multiplier4",
            "multiplier5",
            "multiplier6",
        ]
        categories = [
            "avgAutoFuel",
            "avgTransitionFuel",
            "avgFirstActiveHubFuel",
            "avgSecondActiveHubFuel",
            "avgEndgameFuel",
            "avgTotalFuel",
        ]

        pickabilityList = []
        for i in range(0, 6):
            if extraDf.iloc[-1][updatedList[i]] != 1:
                pickabilityList.append(
                    extraDf.iloc[-1][updatedList[i]] * df[categories[i]].astype(float)
                )

        if pickabilityList:
            df["Pickability"] = sum(pickabilityList)

    with c2:
        st.number_input("Auto", key="multiplier1", value=1.00)
    with c3:
        st.number_input("Trans", key="multiplier2", value=1.00)
    with c4:
        st.number_input("Shift 1", key="multiplier3", value=1.00)
    with c5:
        st.number_input("Shift 2", key="multiplier4", value=1.00)
    with c6:
        st.number_input("Endgame", key="multiplier5", value=1.00)
    with c7:
        st.number_input("Total", key="multiplier6", value=1.00)

    displayDf = df.copy()

    def getRank(teamNum):
        try:
            cleanTeam = int(float(str(teamNum).replace(".0", "")))
            return ranked.index(cleanTeam) + 1
        except (ValueError, IndexError):
            return None

    displayDf.insert(0, "Live Rank", displayDf["teamNumber"].apply(getRank))

    st.subheader("Ranked Performance Overview")
    st.data_editor(
        displayDf,
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
        disabled=True,
        key="performanceEditor",
    )

with tab3:
    teamsGroup = [
        ["a", "b", "c", "d", "e", "f"],
        ["g", "h", "i", "j", "k", "l"],
        ["m", "n", "o", "p", "q", "r"],
    ]
    matchOrder = [0, 1, 2, 1, 2, 1, 0, 1, 2, 0, 1, 2, 1, 2, 0]

    def getStackedCell(items, colors=None):
        htmlString = '<div style="display: flex; flex-direction: column; height: 100%; width: 100%; border: 1px solid #ccc; border-radius: 4px; overflow: hidden;">'
        for i, item in enumerate(items):
            bgColor = colors[i] if colors else "transparent"
            borderStyle = "border-bottom: 1px solid #ccc;" if i < len(items) - 1 else ""
            htmlString += f"""<div style="background-color: {bgColor}; flex: 1; padding: 4px; text-align: center; font-weight: bold; {borderStyle}">{item}</div>"""
        htmlString += "</div>"
        return htmlString

    def mainSchedule():
        st.title("Match Schedule & Scout Verification")
        try:
            with open("jsons/matches.json", "r") as f:
                matchList = json.load(f)
            matchList.sort(key=lambda x: x.get("match_number", 0))
        except (FileNotFoundError, json.JSONDecodeError):
            st.error("Error: Could not load jsons/matches.json.")
            return

        try:
            with open("jsons/fetchedData.json", "r") as f:
                scoutingData = json.load(f).get("root", {})
        except (FileNotFoundError, json.JSONDecodeError):
            scoutingData = {}

        st.divider()
        h1, h2, h3, h4 = st.columns([1, 2, 2, 2])
        h1.write("**Match / Score**")
        h2.write("**Teams (Red/Blue)**")
        h3.write("**Assigned Scouters**")
        h4.write("**Scout Check (Status)**")
        st.divider()

        for idx, match in enumerate(matchList):
            if (not isinstance(match, dict)) or not match.get(
                "comp_level", "qm"
            ) == "qm":
                continue

            matchNum = match.get("match_number", idx + 1)
            matchStr = str(matchNum)
            compLevel = match.get("comp_level", "qm").upper()
            alliances = match.get("alliances", {})

            redScore = alliances.get("red", {}).get("score", 0)
            blueScore = alliances.get("blue", {}).get("score", 0)

            redKeys = [
                t.replace("frc", "")
                for t in alliances.get("red", {}).get("team_keys", [])
            ]
            blueKeys = [
                t.replace("frc", "")
                for t in alliances.get("blue", {}).get("team_keys", [])
            ]
            displayTeams = redKeys + blueKeys

            if len(displayTeams) < 6:
                continue

            allianceColors = ["#8B0000"] * 3 + ["#00008B"] * 3
            assignedScouters = teamsGroup[matchOrder[idx % len(matchOrder)]]

            checkLabels, checkColors = [], []
            for i in range(6):
                teamNum = displayTeams[i]
                assignedName = assignedScouters[i]
                actualScouterName = (
                    scoutingData.get(teamNum, {}).get(matchStr, {}).get("name", "")
                )

                if actualScouterName.lower() == assignedName.lower():
                    checkLabels.append(f"Verified: {actualScouterName}")
                    checkColors.append("#00ff1e")
                elif actualScouterName != "":
                    checkLabels.append(f"Scouter: {actualScouterName}")
                    checkColors.append("#636300")
                else:
                    checkLabels.append(f"Missing: {assignedName}")
                    checkColors.append("#8B0000")

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

    mainSchedule()

with tab4:
    colA, colB, colC = st.columns(3)
    with colA:
        with st.form(key="stdPredictForm"):
            coll0, coll1 = st.columns(2)
            with coll0:
                st.markdown("### red")
                st.number_input("r1", key="srTeam1", value=0)
                st.number_input("r2", key="srTeam2", value=0)
                st.number_input("r3", key="srTeam3", value=0)
            with coll1:
                st.markdown("### blue")
                st.number_input("b1", key="sbTeam1", value=0)
                st.number_input("b2", key="sbTeam2", value=0)
                st.number_input("b3", key="sbTeam3", value=0)
            st.form_submit_button("STD Predict")

    with colB:
        st.markdown("robots ranked in order")
        dictRank = {f"{i}": m for i, m in enumerate(ranked, start=1)}
        st.dataframe(data=dictRank, height=500, key="rankDataframe")

    with colC:
        stdPred(
            [
                st.session_state.get("srTeam1"),
                st.session_state.get("srTeam2"),
                st.session_state.get("srTeam3"),
            ],
            [
                st.session_state.get("sbTeam1"),
                st.session_state.get("sbTeam2"),
                st.session_state.get("sbTeam3"),
            ],
        )
        time.sleep(1)
        with open("jsons/stdTeamPredictor.json", "r") as goy:
            stds = json.load(goy)
        st.markdown(f"## Standard Deviation Predictor")
        st.markdown(f"### {stds.get('output_cell', '')}")

with tab5:
    colL, colM, colN, colO = st.columns(4)
    rMin, rAvg, rMax, bMin, bAvg, bMax, rWin, bWin = 0, 0, 0, 0, 0, 0, 0, 0

    with colL:
        with st.form(key="predictForm"):
            cl0, cl1 = st.columns(2)
            with cl0:
                st.markdown("### red")
                st.number_input("r1", key="rTeam1", value=0)
                st.number_input("r2", key="rTeam2", value=0)
                st.number_input("r3", key="rTeam3", value=0)
            with cl1:
                st.markdown("### blue")
                st.number_input("b1", key="bTeam1", value=0)
                st.number_input("b2", key="bTeam2", value=0)
                st.number_input("b3", key="bTeam3", value=0)
            predictSubmit = st.form_submit_button("Predict")

    with colM:
        st.markdown("robots ranked in order")
        dictRank = {f"{i}": m for i, m in enumerate(ranked, start=1)}
        st.dataframe(dictRank, height=500)

    with colN:
        if predictSubmit:
            if st.session_state.get("rTeam1", 0) != 0:
                predict(
                    [
                        st.session_state.get("rTeam1"),
                        st.session_state.get("rTeam2"),
                        st.session_state.get("rTeam3"),
                    ],
                    [
                        st.session_state.get("bTeam1"),
                        st.session_state.get("bTeam2"),
                        st.session_state.get("bTeam3"),
                    ],
                )
                time.sleep(3)
                with open("jsons/teamPredictor.json", "r") as goy:
                    preds = json.load(goy)

                reds = preds.get("Red_Alliance", {})
                blues = preds.get("Blue_Alliance", {})

                rMin = reds.get("Score_Prediction", {}).get("min", 0)
                rAvg = reds.get("Score_Prediction", {}).get("likely", 0)
                rMax = reds.get("Score_Prediction", {}).get("max", 0)

                bMin = blues.get("Score_Prediction", {}).get("min", 0)
                bAvg = blues.get("Score_Prediction", {}).get("likely", 0)
                bMax = blues.get("Score_Prediction", {}).get("max", 0)

                rWin = reds.get("Win_Chance", 0)
                bWin = blues.get("Win_Chance", 0)

    with colO:
        st.markdown(f"## RED")
        st.markdown(f"Min: {rMin}")
        st.markdown(f"Likely: {rAvg}")
        st.markdown(f"Max: {rMax}")
        st.markdown(f"Win chance: {rWin}")

        st.markdown(f"## BLUE")
        st.markdown(f"Min: {bMin}")
        st.markdown(f"Likely: {bAvg}")
        st.markdown(f"Max: {bMax}")
        st.markdown(f"Win chance: {bWin}")
