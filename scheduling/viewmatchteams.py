import datetime
import json
from bokeh.io import output_file, show
from bokeh.models import ColumnDataSource, DataTable, TableColumn, HTMLTemplateFormatter
import random
import time

teams = [
    ["a", "b", "c", "d", "e", "f"],
    ["g", "h", "i", "j", "k", "l"],
    ["m", "n", "o", "p", "q", "r"],
]
matchOrder = [0, 1, 2, 1, 2, 1, 0]
with open("fetched_data.json", "r") as file:
    fetched_data = json.load(file)
fetched_data = fetched_data.get("root", {})


def view_match_schedule(file_path):
    try:
        with open(file_path, "r") as f:
            matches = json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    # 1. Filter and Deduplicate
    # We only want Qualification matches ('qm') to avoid repeating match numbers
    # from Finals ('f') or Semifinals ('sf')
    qual_matches = [m for m in matches if m.get("comp_level") == "qm"]

    # Sort matches by match number
    qual_matches.sort(key=lambda x: x.get("match_number", 0))

    table_data = {
        "match_num": [],
        "teams_html": [],
        "scouters_name": [],
        "scout_check": [],
    }

    # Use a set to track match numbers we've already added
    seen_matches = set()
    i = 1
    for match in qual_matches:
        m_num = match.get("match_number")

        if m_num in seen_matches:
            continue
        seen_matches.add(m_num)

        alliances = match.get("alliances", {})
        red = [
            t.replace("frc", "") for t in alliances.get("red", {}).get("team_keys", [])
        ]
        blue = [
            t.replace("frc", "") for t in alliances.get("blue", {}).get("team_keys", [])
        ]

        # 2. Build the stacked HTML cell
        # Using min-height and box-sizing to ensure it fills the Bokeh row perfectly
        html_string = '<div style="display: flex; flex-direction: column; height: 100%; width: 100%;">'

        for team in red:
            html_string += f'<div style="background-color: #ffb4b4; border-bottom: 1px solid #ccc; flex: 1; padding: 2px; text-align: center;">{team}</div>'
        for team in blue:
            html_string += f'<div style="background-color: #b4b4ff; border-bottom: 1px solid #ccc; flex: 1; padding: 2px; text-align: center;">{team}</div>'
        html_string += "</div>"

        scouter_list = '<div style="display: flex; flex-direction: column; height: 100%; width: 100%;">'
        j = 0
        for _ in range(6):
            scouter = teams[matchOrder[(i-1)%len(matchOrder)]][j%6]
            scouter_list += f'<div style="border-bottom: 1px solid #ccc; flex: 1; padding: 2px; text-align: center;">{scouter}</div>'
            j += 1

        scouter_list += "</div>"

        scout_check = '<div style="display: flex; flex-direction: column; height: 100%; width: 100%;">'

        teamNums = red + blue
        for team in teamNums:
            if team in fetched_data and str(m_num) in fetched_data[team]:
                scout_check += '<div style="background-color: #abffb5; border-bottom: 1px solid #ccc; flex: 1; padding: 2px; text-align: center;">Correct</div>'
            else:
                scout_check += '<div style="background-color: #ffabab; border-bottom: 1px solid #ccc; flex: 1; padding: 2px; text-align: center;">Incorrect</div>'
        scout_check += "</div>"

        table_data["match_num"].append(str(m_num) + datetime.datetime.fromtimestamp(match.get("actual_time", 0)).strftime(" (%H:%M)"))
        table_data["teams_html"].append(html_string)
        table_data["scouters_name"].append(scouter_list)
        table_data["scout_check"].append(scout_check)
        i += 1

    source = ColumnDataSource(table_data)
    team_formatter = HTMLTemplateFormatter(template="<%= value %>")

    columns = [
        TableColumn(field="match_num", title="Match", width=60),
        TableColumn(
            field="teams_html",
            title="Teams (Red/Blue)",
            formatter=team_formatter,
            width=120,
        ),
        TableColumn(
            field="scouters_name", title="Scouters", formatter=team_formatter, width=120
        ),
        TableColumn(
            field="scout_check",
            title="Scout check",
            formatter=team_formatter,
            width=120,
        ),
    ]

    data_table = DataTable(
        source=source,
        columns=columns,
        row_height=150,  # Adjusted height for 6 teams
        index_position=None,
        sizing_mode="stretch_height",
        width=540,
        height_policy="auto",
        selectable=True,
    )

    output_file("output/clean_schedule.html")
    show(data_table)


if __name__ == "__main__":
    start = time.time()
    view_match_schedule("output/tba_matches.json")
    print(f"Execution time: {time.time() - start} seconds")