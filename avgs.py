import json
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, DataTable, TableColumn, HTMLTemplateFormatter

# Configuration
COLUMN_ORDER = [
    "teamNumber",
    "entries",
    "avgAutoFuel",
    "avgTransitionFuel",
    "avgFirstActiveHubFuel",
    "avgSecondActiveHubFuel",
    "avgEndgameFuel",
    "avgTotalFuel",
]

GRADIENT_COLUMNS = [
    "avgAutoFuel",
    "avgTransitionFuel",
    "avgFirstActiveHubFuel",
    "avgSecondActiveHubFuel",
    "avgEndgameFuel",
    "avgTotalFuel",
]


def calculateAverage(lst):
    return round(sum(lst) / len(lst), 2) if lst else 0


def processTeamAverages(filePath, teams=None):

    with open(filePath, "r") as f:
        fetchedData = json.load(f)

    if teams is not None:
        teamList = teams
    else:
        teamList = fetchedData.get("team", [])

    rootData = fetchedData.get("root", {})

    summaryData = {
        "failureRate": [],
        "teamNumber": [],
        "entries": [],
        "avgAutoFuel": [],
        "avgTransitionFuel": [],
        "avgFirstActiveHubFuel": [],
        "avgSecondActiveHubFuel": [],
        "avgEndgameFuel": [],
        "avgTotalFuel": [],
        "endgameAvgClimbPoints": [],
        "autoClimbPercent": [],
        "multiTurret":[],
        "static": []
    }

    for team in teamList:
        teamMatches = rootData.get(str(team), {})
        matchCount = len(teamMatches)

        tempAutoClimb, tempAuto, tempTransition, tempFirstHub = 0, [], [], []
        tempEndgameClimbPoints, tempSecondHub, tempEndgame, tempTotal, tempFailure = (
            [],
            [],
            [],
            [],
            0,
        )

        for matchId, matchData in teamMatches.items():
            auto = matchData.get("autoFuel", 0)
            transition = matchData.get("transitionFuel", 0)
            endgame = matchData.get("endgameFuel", 0)
            firstShift = 1 if matchData.get("shift1HubActive") else 2
            secondShift = 3 if matchData.get("shift3HubActive") else 4
            firstHub = matchData.get(f"shift{firstShift}Fuel", 0)
            secondHub = matchData.get(f"shift{secondShift}Fuel", 0)
            total = auto + transition + endgame + firstHub + secondHub
            fail = matchData.get("failure", False)

            tempAutoClimb += 1 if matchData.get("autoClimbed") else 0

            if matchData.get("endgameClimbLevel") != "Didn't climb" and matchData.get(
                "endgameClimbLevel", ""
            ).startswith("Level "):
                print(matchData.get("endgameClimbLevel"), "")
                tempEndgameClimbPoints.append(
                    (int(matchData.get("endgameClimbLevel", "")[5:]) * 5)
                )
            else:
                tempEndgameClimbPoints.append(0)

            tempAuto.append(auto)
            tempTransition.append(transition)
            tempFirstHub.append(firstHub)
            tempSecondHub.append(secondHub)
            tempEndgame.append(endgame)
            tempTotal.append(total)
            tempFailure += 1 if fail else 0

        summaryData["teamNumber"].append(team)
        summaryData["entries"].append(matchCount)
        summaryData["avgAutoFuel"].append(calculateAverage(tempAuto))
        summaryData["avgTransitionFuel"].append(calculateAverage(tempTransition))
        summaryData["avgFirstActiveHubFuel"].append(calculateAverage(tempFirstHub))
        summaryData["avgSecondActiveHubFuel"].append(calculateAverage(tempSecondHub))
        summaryData["avgEndgameFuel"].append(calculateAverage(tempEndgame))
        summaryData["avgTotalFuel"].append(calculateAverage(tempTotal))
        summaryData["autoClimbPercent"].append(
            round((tempAutoClimb / matchCount) * 100, 2)
        )
        summaryData["failureRate"].append(round((tempFailure / matchCount) * 100, 2))
        summaryData["endgameAvgClimbPoints"].append(
            calculateAverage(tempEndgameClimbPoints)
        )

    return summaryData


def view(teams=None, color=False):
    processedSummary = processTeamAverages("jsons/fetchedData.json", teams)

    if processedSummary:
        output_file("team_averages.html")
        numTeams = len(processedSummary["teamNumber"])

        if color:
            teamColors = ["transparent"] * numTeams
            for i in range(numTeams):
                if i < 3:
                    teamColors[i] = "#ffb4b4"  # Light Red
                elif i >= numTeams - 3:
                    teamColors[i] = "#b4b4ff"  # Light Blue
            processedSummary["teamNumberColor"] = teamColors

        # 2. Apply Gradient Logic for data columns
        for col in GRADIENT_COLUMNS:
            if col in processedSummary:
                vals = [float(v) for v in processedSummary[col]]
                maxV = max(vals) if vals and max(vals) > 0 else 1
                colors = []
                for v in vals:
                    ratio = min(max(v / maxV, 0), 1)
                    r = int(255 - (75 * ratio))
                    g = int(180 + (75 * ratio))
                    colors.append(f"rgb({r}, {g}, 180)")
                processedSummary[f"{col}Color"] = colors

        source = ColumnDataSource(processedSummary)

        # 3. Build Columns with Formatters
        tableColumns = []
        for col in COLUMN_ORDER:
            title = col.replace("avg", "Avg ").replace("Fuel", " Fuel")

            if col == "teamNumber" and color:
                formatter = HTMLTemplateFormatter(
                    template="""
                    <div style="background-color: <%= teamNumberColor %>; 
                                padding: 4px; margin: -4px; height: 100%;">
                        <%= value %>
                    </div>
                """
                )
                tableColumns.append(
                    TableColumn(field=col, title=title, formatter=formatter, width=100)
                )

            elif col in GRADIENT_COLUMNS:
                formatter = HTMLTemplateFormatter(
                    template=f"""
                    <div style="background-color: <%= {col}Color %>; 
                                padding: 4px; margin: -4px; height: 100%;">
                        <%= value %>
                    </div>
                """
                )
                tableColumns.append(
                    TableColumn(field=col, title=title, formatter=formatter, width=120)
                )
            else:
                tableColumns.append(TableColumn(field=col, title=title, width=100))

        # Dynamic Sizing
        dynamicHeight = max(400, min(numTeams * 30 + 50, 800))
        dynamicWidth = max(1000, len(tableColumns) * 125)

        dataTable = DataTable(
            source=source,
            columns=tableColumns,
            width=dynamicWidth,
            height=dynamicHeight,
            selectable=True,
            sortable=True,
            index_position=None,
        )

        save(dataTable, "team_averages.html")


if __name__ == "__main__":
    # To see the colors, pass True here:
    view(color=False)
