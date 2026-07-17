import time

import streamlit as st
import pandas as pd
import json
import time
from PIL import Image
from io import BytesIO
import requests
from ranking import read_matches
from bluealliance import fetch as bFetch
from fetchfromdb import RefreshNewData, fetch as ffetch
from avgs import processTeamAverages
from jsonToCsv import convertAvgsToCsv
from teamPredictor import main as predict
from stdTeamPredictor import predict as stdPred

# Requires Python 3.14 and the packages in requirements.txt.

# ffetch()
bFetch("matches")
bFetch("rankings")
#RefreshNewData()
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

tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["Individual", "Data", "Ranker", "Matches", "STD Predictor", "Game Predictor", "Cool Cards"]
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

        st.sidebar.header("Filters")

        if "teamNumber" in df.columns:
            allTeams = sorted(df["teamNumber"].unique().astype(str))
            st.session_state.teamSelector = [
                team
                for team in st.session_state.get("teamSelector", allTeams)
                if team in allTeams
            ]

            if st.sidebar.button("Select All Teams", key="selectAllBtn"):
                st.session_state.teamSelector = allTeams

            selectedTeams = st.sidebar.multiselect(
                "Filter by Team",
                options=allTeams,
                key="teamSelector",
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


        styledDf = df.copy()
        for col in numericGradientColumns:
            if col in styledDf.columns:
                styledDf[col] = styledDf[col].apply(
                    lambda x: f"{x}" if pd.notna(x) else ""
                )
#new ui starts here
    data_view = st.segmented_control(
            "Data",
            ["All", "Auto", "Transition", "Shifts", "Endgame", "Misc"],
            selection_mode = "multi",
            default = "All"
        )
    display_cols = []
    if"Auto" in data_view:
        display_cols+=[ "autoFuel", "autoClimbed"]
    if "Transition" in data_view:
        display_cols+=[ "transitionFuel"]
    if "Shifts" in data_view:
        display_cols+=[ "shift1Fuel", "shift2Fuel",  "shift3Fuel", "shift4Fuel"]
    if "Endgame" in data_view:
        display_cols+=[ "endgameFuel", "endgameClimbLevel"]
    if "Misc" in data_view:
        display_cols+=[ "crossedBump", "underTrench", "robotError", "notes", "static"]

    if display_cols and "All" not in data_view:
        df= df[["teamNumber", "matchNumber", "name" ]+display_cols]
    st.dataframe(df, use_container_width=True, hide_index=True)
        

with tab2:
    df = pd.read_csv("jsons/avgs.csv")
    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)

    if "Pickability" in df.columns:
        df["Pickability"] = pd.to_numeric(df["Pickability"], errors="coerce").fillna(0)
    else:
        df["Pickability"] = 0.0

    with c1:
        if st.button("Update Multipliers"):
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

    mango = [  # 0 1 and 2 cannot contain a or c, 2 and 3 cannot contain C, 3 4 5 cannot contain D, 5 6 cannot contain a 6 0 cannot contain B
        ["Kate Basun", "Agrawal", "Peter", "Nicol", "Jennings", "Caulfield"],  # 0
        ["Harsh G", "Precourt", "Owen Biamonte", "Browne", "Rishav", "Dong"],  # 1
        [
            "Aiden Vargas",
            "Lenarz",
            "Kaelyn",
            "Maxwell Dillion",
            "Jennings",
            "Tuthill",
        ],  # 2
        ["McGrath", "sam meng", "Senchukov", "Ding", "Kruger", "Ryan Hefferon"],  # 3
        ["Sauer", "Maxwell Miller", "Ismoedi", "Chang", "Daniel Sardinha", "KH"],  # 4
        ["Khan", "Senut W", "Aidan", "Ding", "Barcomb", "Conway"],  # 5
        ["Delport", "Rahban", "Prausa", "Jason Zhang", "sam meng", "Ding"],  # 6
    ]
    teamsGroup = [
        # 0: Cannot contain A, B, or C
        [
            "Kate Basun",
            "Sanjay Agrawal",
            "Peter Matos",
            "Dominic Nicol",
            "Michael Jennings",
            "Juliet Caulfield",
        ],
        # 1: Cannot contain A or C
        [
            "Harsh Gairola",
            "Julien Precourt",
            "Owen Biamonte",
            "Aoibheann Browne",
            "Rishav Mukherjee",
            "Mason Dong",
        ],
        # 2: Cannot contain A or C
        [
            "Aiden Vargas",
            "Hunter Lenarz",
            "Kaelyn Norton",
            "Maxwell Dillon",
            "Christopher Jennings",
            "Nathan Tuthill",
        ],
        # 3: Cannot contain C or D
        [
            "Matthew McGrath",
            "Sam Meng",
            "Daniel Senchukov",
            "William Ding",
            "Estiaan Kruger",
            "Ryan Hefferon",
        ],
        # 4: Cannot contain D
        [
            "Benjamin Sauer",
            "Maxwell Miller",
            "Dama Ismoedi",
            "Mac Chang",
            "Daniel Sardinha",
            "Kshitij Hegde",
        ],
        # 5: Cannot contain D or A
        [
            "Shayaan Khan",
            'Senuth W ',
            "Aidan Ahn",
            "Wesley Barcomb",
            "Zoe Conway",
            "Daniel Senchukov",
        ],
        # 6: Cannot contain A or B
        [
            "Tiana Delport",
            "Alex Rahban",
            "Evan Prausa",
            'Jason Zhang'
,
            "William Ding",
            "Sam Meng",
        ],
    ]

    def stepper(len, reps, maxNum):
        sequence = []

        for i in range(len):
            blockIndex = i // reps
            currentNum = blockIndex % (maxNum + 1)
            sequence.append(int(currentNum))

        return sequence

    st.title("Qual Matches")
    try:
        with open("jsons/matches.json", "r") as f:
            matchList = json.load(f)
        matchList.sort(key=lambda x: x.get("match_number", 0))
    except (FileNotFoundError, json.JSONDecodeError):
        st.error("Error: Could not load jsons/matches.json.")

    matchOrder = [
        0,  # est 10:50
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,  # est 12:00 match 9 id 8
        1,
        2,
        2,
        2,
        2,  # est 14:00 match 14 id 13
        2,
        3,
        3,
        3,
        3,
        3,  # est 15:00 match 20 id 19
        4,
        4,
        4,
        4,
        4,
        5,
        5,  # est 16:00 match 27 id 26
        5,
        5,
        5,
        6,
        6,
        6,  # est 17:00 match 33 id 32
        6,
        6,
        0,
        0,
        0,
        0,
        0,  # est 18:00 match 40 id 39
        1,
        1,
        1,
        1,
        1,
        2,
        2,  # est 19:00 match 47 id 46
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        3,
        4,
        4,
        4,
        4,
        4,
        5,
        5,
        5,
        5,
    ]
    try:
        with open("jsons/fetchedData.json", "r") as f:
            scoutingData = json.load(f).get("root", {})
    except (FileNotFoundError, json.JSONDecodeError):
        scoutingData = {}
        print("nothing")

    for match, matches in enumerate(matchList):
        if not matches.get("comp_level", "dih") == "qm":
            print("pass")
            continue

        matchNum = matches.get("match_number", match + 1)

        estTime = matches.get("predicted_time") or 0
        estOffset = -4 * 3600

        estEpoch = estTime + estOffset

        estStruct = time.gmtime(estEpoch)

        estTime = time.strftime('%H:%M', estStruct)
        actualTime = matches.get("actual_time", None)

        compLevel = matches.get("comp_level", "qm").upper()
        alliances = matches.get("alliances", {})

        redScore = alliances.get("red", {}).get("score", 0)
        blueScore = alliances.get("blue", {}).get("score", 0)

        redKeys = [
            team.replace("frc", "")
            for team in alliances.get("red", {}).get("team_keys", [])
        ]
        blueKeys = [
            team.replace("frc", "")
            for team in alliances.get("blue", {}).get("team_keys", [])
        ]

        allTeams = redKeys + blueKeys

        if len(allTeams) < 6:
            continue

        # put emojis cuz im not dealing with chud html
        with st.container(border=True):
            st.markdown(f"Estimated: {estTime}")
            if actualTime != None:
                if actualTime < time.time():
                    st.markdown("MATCH PASSED")
                else:
                    st.markdown("MATCH UPCOMING")
            else:
                st.markdown("MATCH UPCOMING")

            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

            st.markdown(f"Match : #{matchNum} 🟥{redScore } 🟦 {blueScore}")
            st.markdown("TEAM")

            for i in [3, 4, 5, 0, 1, 2]:
                selectedTeam = allTeams[i]

                scouter = (
                    scoutingData.get(selectedTeam, {})
                    .get(str(matchNum), {})
                    .get("name", "")
                )
                if i < 3:
                    allianceColor = "🟥"
                else:
                    allianceColor = "🟦"
                scouterfont = teamsGroup[matchOrder[(matchNum - 1) % len(matchOrder)]][i]
                isScouted = "✅" if scouter != "" else "❌"
                st.markdown(f"{allianceColor} {selectedTeam} — {isScouted} {scouterfont}", unsafe_allow_html=True)


with tab4:
    availableStdTeams = sorted(
        {
            int(row["teamNumber"])
            for row in allRows
            if row.get("teamNumber") not in (None, "")
        }
    )
    stdTeamOptions = [None, *availableStdTeams]
    colA, colB, colC = st.columns(3)
    with colA:
        with st.form(key="stdPredictForm"):
            coll0, coll1 = st.columns(2)
            with coll0:
                st.markdown("### red")
                st.selectbox("r1", stdTeamOptions, key="stdRedTeam1")
                st.selectbox("r2", stdTeamOptions, key="stdRedTeam2")
                st.selectbox("r3", stdTeamOptions, key="stdRedTeam3")
            with coll1:
                st.markdown("### blue")
                st.selectbox("b1", stdTeamOptions, key="stdBlueTeam1")
                st.selectbox("b2", stdTeamOptions, key="stdBlueTeam2")
                st.selectbox("b3", stdTeamOptions, key="stdBlueTeam3")
            stdPredictSubmit = st.form_submit_button("STD Predict")

    with colB:
        st.markdown("robots ranked in order")
        dictRank = {f"{i}": m for i, m in enumerate(ranked, start=1)}
        st.dataframe(data=dictRank, height=500, key="rankDataframe")

    with colC:
        st.markdown("## Standard Deviation Predictor")

        if stdPredictSubmit:
            redTeams = [
                st.session_state.get("stdRedTeam1"),
                st.session_state.get("stdRedTeam2"),
                st.session_state.get("stdRedTeam3"),
            ]
            blueTeams = [
                st.session_state.get("stdBlueTeam1"),
                st.session_state.get("stdBlueTeam2"),
                st.session_state.get("stdBlueTeam3"),
            ]

            if any(team is None for team in redTeams + blueTeams):
                st.session_state.stdPrediction = None
                st.session_state.stdPredictionError = (
                    "Select all three red and all three blue teams."
                )
            elif len(set(redTeams + blueTeams)) < 6:
                st.session_state.stdPrediction = None
                st.session_state.stdPredictionError = (
                    "Select six different teams for the prediction."
                )
            else:
                st.session_state.stdPrediction = stdPred(redTeams, blueTeams)
                st.session_state.stdPredictionTeams = {
                    "red": redTeams,
                    "blue": blueTeams,
                }
                st.session_state.stdPredictionError = None

        if st.session_state.get("stdPredictionError"):
            st.error(st.session_state.stdPredictionError)
        elif stds := st.session_state.get("stdPrediction"):
            predictionTeams = st.session_state.stdPredictionTeams
            st.caption(
                f"Red: {predictionTeams['red']} | Blue: {predictionTeams['blue']}"
            )
            st.markdown(f"### {stds['output_cell']}")
            calculationData = stds["calculation_data"]
            st.write(f"Red range: {calculationData['red_range']}")
            st.write(f"Blue range: {calculationData['blue_range']}")
        else:
            st.info("Select six teams and select STD Predict.")

with tab5:
    colL, colM, colN, colO = st.columns(4)

    with colL:
        with st.form(key="predictForm"):
            cl0, cl1 = st.columns(2)
            with cl0:
                st.markdown("### red")
                st.selectbox("r1", stdTeamOptions, key="gameRedTeam1")
                st.selectbox("r2", stdTeamOptions, key="gameRedTeam2")
                st.selectbox("r3", stdTeamOptions, key="gameRedTeam3")
            with cl1:
                st.markdown("### blue")
                st.selectbox("b1", stdTeamOptions, key="gameBlueTeam1")
                st.selectbox("b2", stdTeamOptions, key="gameBlueTeam2")
                st.selectbox("b3", stdTeamOptions, key="gameBlueTeam3")
            predictSubmit = st.form_submit_button("Predict")

    with colM:
        st.markdown("robots ranked in order")
        dictRank = {f"{i}": m for i, m in enumerate(ranked, start=1)}
        st.dataframe(dictRank, height=500)

    with colN:
        if predictSubmit:
            redTeams = [
                st.session_state.get("gameRedTeam1"),
                st.session_state.get("gameRedTeam2"),
                st.session_state.get("gameRedTeam3"),
            ]
            blueTeams = [
                st.session_state.get("gameBlueTeam1"),
                st.session_state.get("gameBlueTeam2"),
                st.session_state.get("gameBlueTeam3"),
            ]

            if any(team is None for team in redTeams + blueTeams):
                st.session_state.gamePrediction = None
                st.session_state.gamePredictionError = (
                    "Select all three red and all three blue teams."
                )
            elif len(set(redTeams + blueTeams)) < 6:
                st.session_state.gamePrediction = None
                st.session_state.gamePredictionError = (
                    "Select six different teams for the prediction."
                )
            else:
                st.session_state.gamePrediction = predict(redTeams, blueTeams)
                st.session_state.gamePredictionError = None

        if st.session_state.get("gamePredictionError"):
            st.error(st.session_state.gamePredictionError)
        elif st.session_state.get("gamePrediction") is None:
            st.info("Select six teams and select Predict.")

    with colO:
        if preds := st.session_state.get("gamePrediction"):
            reds = preds["Red_Alliance"]
            blues = preds["Blue_Alliance"]
            redScores = reds["Score_Prediction"]
            blueScores = blues["Score_Prediction"]

            st.caption(f"Red: {reds['Teams']} | Blue: {blues['Teams']}")
            st.markdown("## RED")
            st.markdown(f"Min: {redScores['min']}")
            st.markdown(f"Likely: {redScores['likely']}")
            st.markdown(f"Max: {redScores['max']}")
            st.markdown(f"Win chance: {reds['Win_Chance']}")

            st.markdown("## BLUE")
            st.markdown(f"Min: {blueScores['min']}")
            st.markdown(f"Likely: {blueScores['likely']}")
            st.markdown(f"Max: {blueScores['max']}")
            st.markdown(f"Win chance: {blues['Win_Chance']}")
with tab6:
    df = pd.read_csv("jsons/avgs.csv").sort_values("avgTotalFuel", ascending=False)
    with st.popover("weights"):
        weightAuto = st.slider("Auto", 0.0, 3.0, 1.0)
        weightTrans = st.slider("Trans", 0.0, 3.0, 1.0)
        weightShift = st.slider("Shift", 0.0, 3.0, 1.0)
        weightEnd = st.slider("End", 0.0, 3.0, 1.0)
    df["Pickability"] = (
        weightAuto * df["avgAutoFuel"]
        + weightTrans * df["avgTransitionFuel"]
        + weightShift * (df["avgTotalFuel"] - df["avgAutoFuel"] - df["avgTransitionFuel"] - df["avgEndgameFuel"])/4
        + weightEnd * df["avgEndgameFuel"]
    )
    df=df.sort_values("Pickability", ascending=False)
    team_data = df.to_dict(orient="records")

    for i in range(0, len(df), 2): #2 is max per row and adjust if neded
        team_row = team_data[i:i+2]
        columns = st.columns(2)

        for n in range(len(team_row)):
            team = team_row[n]
            with columns[n]:
                with st.container(border= True):
                    st.subheader(f"Team {team['teamNumber']}")
                    st.metric("Avg Fuel", round(team["avgTotalFuel"], 1))
                    st.metric("Avg Auto", round(team["avgAutoFuel"], 1))
                    st.metric("Avg Transition", round(team["avgTransitionFuel"], 1))
                    st.metric("AvgShifts", round(team["avgTotalFuel"]-team["avgAutoFuel"]-team["avgTransitionFuel"]-team["avgEndgameFuel"], 1))
                    st.metric("Avg Endgame", round(team["avgEndgameFuel"], 1))
                    st.metric("Pickability", round(team["Pickability"], 1))


