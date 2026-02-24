import streamlit as st
import json
import datetime

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
    st.title("Match Schedule & Scout Verification")

    try:
        with open("tba_jsons/matches.json", "r") as file:
            matchList = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        st.error("Error: Could not load tba_jsons/matches.json.")
        return

    try:
        with open("jsons/fetchedData.json", "r") as file:
            scoutingData = json.load(file).get("root", {})
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
        if not isinstance(match, dict):
            continue

        matchNum = match.get("match_number", idx + 1)
        matchStr = str(matchNum)
        compLevel = match.get("comp_level", "qm").upper()
        alliances = match.get("alliances", {})

        redScore = alliances.get("red", {}).get("score", 0)
        blueScore = alliances.get("blue", {}).get("score", 0)

        redKeys = [
            t.replace("frc", "") for t in alliances.get("red", {}).get("team_keys", [])
        ]
        blueKeys = [
            t.replace("frc", "") for t in alliances.get("blue", {}).get("team_keys", [])
        ]
        displayTeams = redKeys + blueKeys

        if len(displayTeams) < 6:
            continue

        allianceColors = ["#ffb4b4"] * 3 + ["#b4b4ff"] * 3

        assignedScouters = teamsGroup[matchOrder[idx % len(matchOrder)]]

        checkLabels = []
        checkColors = []

        for i in range(6):
            teamNum = displayTeams[i]
            assignedName = assignedScouters[i]

            teamData = scoutingData.get(teamNum, {})
            matchData = teamData.get(matchStr, {})
            actualScouterName = matchData.get("name", "")

            if actualScouterName.lower() == assignedName.lower():
                checkLabels.append(f"Verified: {actualScouterName}")
                checkColors.append("#abffb5")  # Green
            elif actualScouterName != "":
                checkLabels.append(f"Wrong Scouter: {actualScouterName}")
                checkColors.append("#ffffab")  # Yellow
            else:
                checkLabels.append("Missing")
                checkColors.append("#ffabab")  # Red

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
