import json


def read_matches():
    try:
        with open("jsons/rankings.json", "r") as r:
            data = json.load(r)
        print(
            f"Successfully read {len(data['rankings'])} rankings from jsons/matches.json"
        )
        ranked = []
        for id, team in enumerate(data["rankings"], start=1):
            ranked.append(int(team["team_key"].replace("frc", "")))

        return ranked
    except FileNotFoundError:
        print("Error: jsons/matches.json not found.")
        return None
    except json.JSONDecodeError:
        print("Error: Failed to parse jsons/matches.json")
        return None


if __name__ == "__main__":
    ranked_teams = read_matches()
    print(ranked_teams)
