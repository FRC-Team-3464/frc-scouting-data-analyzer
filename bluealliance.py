import requests
import json

apiKey = "CVI6FjGLtHQbCUwrb7GYAUGGWkKV7w115MdXgjnQzNSijNGV3IDkgOuRxogOVLuy"
event = "2026week0"
method = "matches"  # matches rankings
headers = {"X-TBA-Auth-Key": apiKey}

def fetch(method):
    url = f"https://www.thebluealliance.com/api/v3/event/{event}/{method}"
    print(f"Fetching: {url}")
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"Successfully fetched {len(data)} matches!")
        with open(f"jsons/{method}.json", "w") as w:
            json.dump(data, w, indent=4)
    else:
        print(f"Error {response.status_code}: {response.text}")

def fetchAlreadyCompletedMatches(storedMatches):
    url = f"https://www.thebluealliance.com/api/v3/event/{event}/matches"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return []
    completedMatches = []
    for matches in response.json():
        if matches.get("comp_level") !="qm":#gets rid of practice and playoff mtches
            continue 
        if not matches.get("actual_time"):
            continue
        if str(matches["match_number"]) in storedMatches:
            continue
        teams = [
            team.replace("frc", "") for team in matches["alliances"]["red"]["team_keys"]
            +matches["alliances"]["blue"]["team_keys"]]
        completedMatches.append({"matchNumber" : matches["match_number"], "teams": teams})
    return completedMatches


if __name__ == "__main__":
    fetch(method)
