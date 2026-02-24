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


if __name__ == "__main__":
    fetch(method)
