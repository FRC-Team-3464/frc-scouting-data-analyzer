import json
import statistics
import math


def determine_winner(red_min, red_max, blue_min, blue_max):
    if red_min > blue_max:
        return "Red Win"
    elif blue_min > red_max:
        return "Blue Win"
    else:
        return "Too Close"


def get_team_matches(data_root, team_num):
    t_str = str(team_num)
    return list(data_root.get(t_str, {}).values())


def calculate_fuel(data_root, alliance_teams):
    total_fuel_points = 0
    for team in alliance_teams:
        matches = get_team_matches(data_root, team)
        if not matches:
            continue

        scores = []
        for m in matches:
            match_fuel = m.get("autoFuel", 0)
            match_fuel += m.get("transitionFuel", 0) + m.get("endgameFuel", 0)
            for i in range(1, 5):
                if m.get(f"shift{i}HubActive", False):
                    match_fuel += m.get(f"shift{i}Fuel", 0)
            scores.append(match_fuel)

        if scores:
            total_fuel_points += statistics.mean(scores)

    return total_fuel_points


def calculate_tower(data_root, alliance_teams):
    total_climb_points = 0
    for team in alliance_teams:
        matches = get_team_matches(data_root, team)
        if not matches:
            continue

        scores = []
        for m in matches:
            p = 15 if m.get("autoClimbed") else 0

            lvl = str(m.get("endgameClimbLevel", "0"))
            if lvl == "Level 1":
                p += 10
            elif lvl == "Level 2":
                p += 20
            elif lvl == "Level 3":
                p += 30
            scores.append(p)

        if scores:
            total_climb_points += statistics.mean(scores)

    return total_climb_points


def calculate_stdev(data_root, alliance_teams):
    sum_of_variances = 0

    for team in alliance_teams:
        matches = get_team_matches(data_root, team)
        if len(matches) < 2:
            continue

        team_total_scores = []
        for m in matches:
            score = m.get("autoFuel", 0)
            score += m.get("transitionFuel", 0) + m.get("endgameFuel", 0)
            for i in range(1, 5):
                if m.get(f"shift{i}HubActive", False):
                    score += m.get(f"shift{i}Fuel", 0)

            lvl = str(m.get("endgameClimbLevel", "0"))
            if lvl == "Level 1":
                score += 10
            elif lvl == "Level 2":
                score += 20
            elif lvl == "Level 3":
                score += 30

            if m.get("autoClimbed"):
                score += 15

            team_total_scores.append(score)

        sum_of_variances += statistics.variance(team_total_scores)

    return math.sqrt(sum_of_variances)


def game_predictor(json_input, red_teams, blue_teams, percent_stdev):
    data_root = json_input.get("root", {})

    red_fuel = calculate_fuel(data_root, red_teams)
    red_tower = calculate_tower(data_root, red_teams)

    blue_fuel = calculate_fuel(data_root, blue_teams)
    blue_tower = calculate_tower(data_root, blue_teams)

    red_total = red_fuel + red_tower
    blue_total = blue_fuel + blue_tower

    red_raw_stdev = calculate_stdev(data_root, red_teams)
    blue_raw_stdev = calculate_stdev(data_root, blue_teams)

    red_adj_stdev = red_raw_stdev * percent_stdev
    blue_adj_stdev = blue_raw_stdev * percent_stdev

    blue_min = blue_total - blue_adj_stdev
    blue_max = blue_total + blue_adj_stdev
    red_min = red_total - red_adj_stdev
    red_max = red_total + red_adj_stdev

    if blue_min < 0:
        blue_min = 0
    if red_min < 0:
        red_min = 0

    result_text = determine_winner(red_min, red_max, blue_min, blue_max)

    return {
        "output_cell": f"{result_text}s blue {blue_total: .2f} to red {red_total: .2f}",
        "confidence_factor_used": percent_stdev,
        "calculation_data": {
            "red_range": [round(red_min), round(red_max)],
            "blue_range": [round(blue_min), round(blue_max)],
            "red_total": round(red_total),
            "blue_total": round(blue_total),
        },
    }


def predict(redAlliance, blueAlliance, stdev_input=1.0):
    with open("jsons/fetchedData.json", "r") as inFile:
        rawJsonString = inFile.read()
    data = json.loads(rawJsonString)
    
    stdev_input = 1.0

    with open("jsons/stdTeamPredictor.json", "w") as outFile:
        json.dump(
            game_predictor(data, redAlliance, blueAlliance, stdev_input),
            outFile,
            indent=4,
        )


if __name__ == "__main__":
    predict([811, 1768, 1512], [5687, 9644, 131])