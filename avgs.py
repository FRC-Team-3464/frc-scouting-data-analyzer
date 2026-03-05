import json

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
        teamMulti = False
        teamStatic = False

        for matchId, matchData in teamMatches.items():
            if (matchData.get("multiShooter")):
                teamMulti = True
            if (matchData.get("static")):
                teamStatic = True
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
        summaryData["multiTurret"].append(teamMulti)
        summaryData["static"].append(teamStatic)

    return summaryData