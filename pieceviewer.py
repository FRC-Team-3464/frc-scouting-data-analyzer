import json
from bokeh.io import output_file, show
from bokeh.models import ColumnDataSource, DataTable, TableColumn

COLUMN_ORDER = [
    "teamNumber",
    "entries",
    "avgautoFuel",
    "avgtransitionFuel",
    "avgFirstActiveHubFuel",
    "avgSecondActiveHubFuel",
    "avgTeleopFuel",
    "avgEndgameFuel",
    "avgTotalFuel",
]


def avg(lst):
    return round(sum(lst) / len(lst), 2) if lst else 0


with open("fetched_data.json", "r") as f:
    fetched_data = json.load(f)
TEAMS = fetched_data.get("team", {})
fetched_data = fetched_data.get("root", {})
print(f"Loaded data for {len(fetched_data)} teams")
processedData = {
    "teamNumber": TEAMS,
    "entries": [],
    "autoFuel": [],
    "transitionFuel": [],
    "firstActiveHubFuel": [],
    "secondActiveHubFuel": [],
    "teleopFuel": [],
    "endgameFuel": [],
    "totalFuel": [],
}
for team in TEAMS:
    team_matches = fetched_data.get(str(team), {})
    processedData["entries"].append(len(team_matches))
    autoFuels = []
    transitionFuels = []
    firstActiveHubFuels = []
    secondActiveHubFuels = []
    teleopFuels = []
    endgameFuels = []
    totalFuels = []
    for match_id, match_data in team_matches.items():

        def get_value(field):
            if isinstance(field, dict):
                if "integerValue" in field:
                    return int(field["integerValue"])
                elif "doubleValue" in field:
                    return float(field["doubleValue"])
                elif "booleanValue" in field:
                    return field["booleanValue"]
            return 0

        autoFuel = get_value(match_data.get("autoFuel", {}))
        transitionFuel = get_value(match_data.get("transitionFuel", {}))
        firstActiveHubShift = 1 if get_value(match_data.get("shift1HubActive")) else 2
        secondActiveHubShift = 3 if get_value(match_data.get("shift3HubActive")) else 4
        endgameFuel = get_value(match_data.get("endgameFuel", {}))

        totalFuel = (
            autoFuel
            + transitionFuel
            + endgameFuel
            + get_value(match_data.get(f"shift{firstActiveHubShift}Fuel", {}))
            + get_value(match_data.get(f"shift{secondActiveHubShift}Fuel", {}))
        )
        autoFuels.append(autoFuel)
        transitionFuels.append(transitionFuel)
        firstActiveHubFuels.append(
            get_value(match_data.get(f"shift{firstActiveHubShift}Fuel"))
        )
        secondActiveHubFuels.append(
            get_value(match_data.get(f"shift{secondActiveHubShift}Fuel"))
        )
        endgameFuels.append(endgameFuel)
        totalFuels.append(totalFuel)
    processedData["autoFuel"].append(avg(autoFuels))
    processedData["transitionFuel"].append(avg(transitionFuels))
    processedData["firstActiveHubFuel"].append(avg(firstActiveHubFuels))
    processedData["secondActiveHubFuel"].append(avg(secondActiveHubFuels))
    processedData["teleopFuel"].append(avg(teleopFuels))
    processedData["endgameFuel"].append(avg(endgameFuels))
    processedData["totalFuel"].append(avg(totalFuels))

output_file("datatable_example.html")

data = {
    "team": TEAMS,
    "match": processedData["entries"],
    "autoFuel": processedData["autoFuel"],
    "transitionFuel": processedData["transitionFuel"],
    "firstActiveHubFuel": processedData["firstActiveHubFuel"],
    "secondActiveHubFuel": processedData["secondActiveHubFuel"],
    "endgameFuel": processedData["endgameFuel"],
}

source = ColumnDataSource(data)

columns = [
    TableColumn(field="team", title="Team"),
    TableColumn(field="match", title="Match"),
    TableColumn(field="autoFuel", title="Auto Fuel"),
    TableColumn(field="transitionFuel", title="Avg Transition Fuel"),
    TableColumn(field="firstActiveHubFuel", title="Avg First Active Hub Fuel"),
    TableColumn(field="secondActiveHubFuel", title="Avg Second Active Hub Fuel"),
    TableColumn(field="endgameFuel", title="Avg Endgame Fuel"),
]

height = max(400, min(len(TEAMS) * 30 + 50, 800))

width = max(1200, 7 * 80)

table = DataTable(
    source=source,
    columns=columns,
    width=width,
    height=height,
    selectable=True,
    sortable=True,
)

show(table)
