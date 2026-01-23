from bokeh.io import show, curdoc
from bokeh.models import ColumnDataSource, DataTable, TableColumn
from bokeh.layouts import column
from bokeh.themes import Theme, built_in_themes
import json
import random
from bokeh.models import HTMLTemplateFormatter

# Define the desired column order here. Columns not in this list will appear at the end.
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

try:
    with open("fetched_data.json", "r") as f:
        data = json.load(f)
    data = data.get("root", {})
    
    print(f"Loaded data for {len(data)} teams")

    rows = []
    for teamnum, matches in data.items():
        for match_id, match_data in matches.items():
            row = {"team": teamnum, "match": match_id}

            for fieldName, fieldValue in match_data.items():
                if isinstance(fieldValue, dict):
                    if "integerValue" in fieldValue:
                        row[fieldName] = int(fieldValue["integerValue"])
                    elif "stringValue" in fieldValue:
                        row[fieldName] = fieldValue["stringValue"]
                    elif "doubleValue" in fieldValue:
                        row[fieldName] = float(fieldValue["doubleValue"])
                    elif "booleanValue" in fieldValue:
                        row[fieldName] = fieldValue["booleanValue"]
                    elif "mapValue" in fieldValue and fieldName == "robotError":
                        mapFields = fieldValue["mapValue"].get("fields", {})
                        trueErrors = []
                        for error_name, errorData in mapFields.items():
                            if (
                                isinstance(errorData, dict)
                                and "booleanValue" in errorData
                            ):
                                if errorData["booleanValue"] is True:
                                    trueErrors.append(error_name)
                        row[fieldName] = ", ".join(trueErrors) if trueErrors else ""
                    else:
                        row[fieldName] = str(fieldValue)
                else:
                    row[fieldName] = fieldValue

            rows.append(row)

    if rows:
        allColumns = set()
        for row in rows:
            allColumns.update(row.keys())

        orderedColumns = [col for col in COLUMN_ORDER if col in allColumns]
        remainingColumns = sorted(
            [col for col in allColumns if col not in COLUMN_ORDER]
        )
        allColumns = orderedColumns + remainingColumns

        data = {col: [] for col in allColumns}
        for row in rows:
            for col in allColumns:
                data[col].append(row.get(col, ""))

        print(f"Created table with {len(rows)} rows and {len(allColumns)} columns")
        print(f"Columns: {allColumns}")

except FileNotFoundError:
    print("data.json not found.")
except json.JSONDecodeError:
    print("Error parsing data.json.")


from bokeh.models import CellFormatter, HTMLTemplateFormatter
from bokeh.palettes import RdYlGn

# Generate color columns for gradient coloring
for col in NUMERIC_GRADIENT_COLUMNS:
    if col in allColumns and col in data:
        numericValues = [
            float(v)
            for v in data.get(col, [])
            if v and isinstance(v, (int, float, str))
        ]
        maxv = max(numericValues) if numericValues else 100

        colors = []
        for val in data[col]:
            try:
                v = float(val) if val else 0
                ratio = min(max(v / maxv, 0), 1)  # Clamp between 0 and 1
                # Light red to light green gradient
                red = int(255 - 105 * ratio)  # 255 to 150
                green = int(150 + 105 * ratio)  # 150 to 255
                blue = 150
                colors.append(f"rgb({red}, {green}, {blue})")
            except (ValueError, TypeError):
                colors.append("rgb(200, 200, 200)")
        data[f"{col}_color"] = colors

# Generate color columns for boolean coloring
boolean_cols = [col for col in allColumns if col not in NUMERIC_GRADIENT_COLUMNS]
for col in boolean_cols:
    if col in data:
        colors = []
        for val in data[col]:
            if val is True:
                
                colors.append("#00CC00")  # Green
            elif val is False:
                colors.append("#FFB3B3")  # Light red
            else:
                colors.append("white")  # White
        data[f"{col}_color"] = colors

source = ColumnDataSource(data)

columns = []
for col in allColumns:
    colWidth = 800 if (col == "robotError" or col == "eventName") else None
    colKwargs = {"field": col, "title": col}

    if f"{col}_color" in data:
        template = f'<div style="background-color: <%=  {col}_color %>; padding: 5px;"><%= {col} %></div>'
        colKwargs["formatter"] = HTMLTemplateFormatter(template=template)

    if colWidth:
        colKwargs["width"] = colWidth

    columns.append(TableColumn(**colKwargs))

rows = len(next(iter(data.values()))) if data else 7
cols = len(data.keys())

height = max(400, min(rows * 30 + 50, 800))

width = max(1200, cols * 80)

table = DataTable(
    source=source,
    columns=columns,
    width=width,
    height=height,
    index_position=0,
    sortable=True,
    selectable=True,
)

layout = column(table)


from bokeh.models import CustomJS

css = """
<style>
.bk-root .bk-data-table .slick-row {
    border-bottom: 1px solid #cccccc;
}
.bk-root .bk-data-table .slick-cell {
    border-right: 1px solid #cccccc;
}
.bk-root .bk-data-table .slick-header-column {
    border-right: 1px solid #999999;
}
</style>
"""

show(layout)
