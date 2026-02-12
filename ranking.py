import json

def read_matches():
    """Read the tba_matches.json file and return the data"""
    try:
        with open("rankings.json", "r") as r:
            data = json.load(r)
        print(
            f"Successfully read {len(data['rankings'])} rankings from tba_matches.json"
        )
        ranked=[]
        for id, team in enumerate(data["rankings"], start=1):
            ranked.append(int(team["team_key"].replace("frc", "")))
        
        return ranked
    except FileNotFoundError:
        print("Error: tba_matches.json not found.")
        return None
    except json.JSONDecodeError:
        print("Error: Failed to parse tba_matches.json")
        return None

if __name__ == "__main__":
    ranked_teams = read_matches()
    print(ranked_teams)