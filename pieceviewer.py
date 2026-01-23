import json
from bokeh.io import show
from bokeh.models import ColumnDataSource, DataTable, TableColumn, HTMLTemplateFormatter
from bokeh.layouts import column

# Configuration
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


def load_and_flatten_data(filepath):
    try:
        with open(filepath, "r") as f:
            full_data = json.load(f)

        root_data = full_data.get("root", {})
        print(f"Loaded data for {len(root_data)} teams")

        rows = []
        for teamnum, matches in root_data.items():
            for match_id, match_fields in matches.items():
                # Start row with identifiers
                row = {"team": teamnum, "match": match_id}

                # Since data is pre-cleaned, we just iterate fields
                for key, value in match_fields.items():
                    # Special handling for robotError if it's still a dict of booleans
                    if key == "robotError" and isinstance(value, dict):
                        true_errors = [k for k, v in value.items() if v is True]
                        row[key] = ", ".join(true_errors)
                    else:
                        row[key] = value
                rows.append(row)
        return rows
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return []


rows = load_and_flatten_data("fetched_data.json")

if rows:
    # 1. Determine Columns
    all_keys = set().union(*(row.keys() for row in rows))
    ordered_cols = [c for c in COLUMN_ORDER if c in all_keys]
    other_cols = sorted(list(all_keys - set(COLUMN_ORDER)))
    final_columns = ordered_cols + other_cols

    # 2. Build Data Dictionary for Bokeh
    plot_data = {col: [row.get(col, "") for row in rows] for col in final_columns}

    # 3. Logic for Gradients
    for col in NUMERIC_GRADIENT_COLUMNS:
        if col in plot_data:
            vals = [float(v) if v not in ["", None] else 0 for v in plot_data[col]]
            max_v = max(vals) if vals and max(vals) > 0 else 1

            colors = []
            for v in vals:
                ratio = min(max(v / max_v, 0), 1)
                # Linear interpolation: Light Red (255, 180, 180) to Light Green (180, 255, 180)
                r = int(255 - (75 * ratio))
                g = int(180 + (75 * ratio))
                colors.append(f"rgb({r}, {g}, 180)")
            plot_data[f"{col}_color"] = colors

    # 4. Logic for Booleans
    for col in final_columns:
        if col not in NUMERIC_GRADIENT_COLUMNS:
            colors = []
            for val in plot_data[col]:
                if val is True:
                    colors.append("#d4edda")  # Light Green
                elif val is False:
                    colors.append("#f8d7da")  # Light Red
                else:
                    colors.append("white")
            plot_data[f"{col}_color"] = colors

    source = ColumnDataSource(plot_data)

    # 5. Build Table Columns with Formatters
    table_columns = []
    for col in final_columns:
        formatter = HTMLTemplateFormatter(
            template=f"""
            <div style="background-color: <%= {col}_color %>; 
                        padding: 4px; margin: -4px; height: 100%;">
                <%= value %>
            </div>
        """
        )

        width = 250 if col in ["notes", "robotError", "eventName"] else 100
        table_columns.append(
            TableColumn(field=col, title=col, formatter=formatter, width=width)
        )

    # 6. Create Layout
    table = DataTable(
        source=source,
        columns=table_columns,
        width=1400,
        height=600,
        sortable=True,
        editable=False,
    )

    show(column(table))
else:
    print("No data to display.")
