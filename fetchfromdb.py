import requests
import json
import logger
import traceback
import sys

logger.clear()

def getValue(field):
    if isinstance(field, dict):
        if "integerValue" in field:
            return int(field["integerValue"])
        elif "doubleValue" in field:
            return float(field["doubleValue"])
        elif "booleanValue" in field:
            return field["booleanValue"]
        elif "arrayValue" in field:
            values = field["arrayValue"].get("values", [])
            return [getValue(val) for val in values]
    return 0


# Load credentials from serviceAccountKey.json
try:
    with open("serviceAccountKey.json", "r") as f:
        config = json.load(f)
    apiKey = config.get("apiKey")
    projectId = config.get("projectId")
    logger.log("Credentials loaded successfully from serviceAccountKey.json")
except FileNotFoundError:
    logger.log("Error: Service account key file not found.")
    logger.log("Please ensure serviceAccountKey.json exists in the current directory.")
    sys.exit()
except json.JSONDecodeError:
    logger.log("Error: Invalid JSON in serviceAccountKey.json")
    sys.exit()


def fetchDataByTeamNum(teamNum, allData=None):
    """
    Recursively fetch all data for a specific team number.
    Traverses {teamNum}/{match}/... structure
    """
    if allData is None:
        allData = {}

    path = f"{teamNum}"
    logger.log(f"\n--- Fetching team: '{teamNum}' ---")
    try:
        url = f"https://firestore.googleapis.com/v1/projects/{projectId}/databases/(default)/documents/{path}"
        logger.log(f"URL: {url}")
        params = {"key": apiKey, "pageSize": "1000"}

        response = requests.get(url, params=params)
        logger.log(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            if "documents" in result and result["documents"]:
                logger.log(
                    f"Found {len(result['documents'])} matches for team {teamNum}"
                )
                allData["root"][teamNum] = {}

                for doc in result["documents"]:
                    docName = doc["name"].split("/")[-1]

                    if "fields" in doc and doc["fields"]:
                        allData["root"][teamNum][docName] = doc["fields"]

                return allData
            else:
                logger.log(f"No matches found for team {teamNum}")
                return allData
        else:
            logger.log(
                f"Error {response.status_code} fetching team {teamNum}: {response.text}"
            )
            return allData

    except Exception as e:
        logger.log(f"Error fetching team {teamNum}: {e}")
        traceback.print_exc()
        return allData


def fetchAllDataRecursive(path="", allData=None):
    """
    Recursively fetch all data from nested collections.
    Assumes structure: {teamNum}/{match}/...
    """
    if allData is None:
        allData = {}

    logger.log(f"\n--- Fetching from path: '{path}' ---")
    try:
        url = f"https://firestore.googleapis.com/v1/projects/{projectId}/databases/(default)/documents{path}"
        logger.log(f"URL: {url}")
        params = {"key": apiKey, "pageSize": "1000"}

        response = requests.get(url, params=params)
        logger.log(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            if "documents" in result and result["documents"]:
                logger.log(f"Found {len(result['documents'])} items at {path}")

                for doc in result["documents"]:
                    docName = doc["name"].split("/")[-1]
                    docPath = f"{path}/{docName}"

                    if "fields" in doc and doc["fields"]:
                        allData[docPath] = doc["fields"]
                        logger.log(f"  Stored: {docPath}")
                    else:
                        logger.log(f"  Checking subcollections of {docPath}...")
                        fetchAllDataRecursive(docPath, allData)

                return allData
            else:
                logger.log(f"No documents found at {path}")
                return allData
        else:
            logger.log(f"Error {response.status_code}: {response.text}")
            return allData

    except Exception as e:
        logger.log(f"Error: {e}")
        traceback.print_exc()
        return allData


def getTeamList(path):
    url = f"https://firestore.googleapis.com/v1/projects/{projectId}/databases/(default)/documents/{path}"
    params = {"key": apiKey}

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        try:
            teamFields = data["fields"]["team"]["arrayValue"]["values"]
            return [list(val.values())[0] for val in teamFields]
        except KeyError:
            logger.log("Field 'team' not found in document.")
            return []
    return []


def cleanFirestoreData(data):
    """
    Recursively removes Firestore type wrappers (e.g., 'integerValue', 'stringValue').
    """
    if isinstance(data, dict):
        typeKeys = {
            "integerValue",
            "stringValue",
            "doubleValue",
            "booleanValue",
            "arrayValue",
            "mapValue",
        }
        foundKey = next((k for k in typeKeys if k in data), None)

        if foundKey:
            if foundKey == "integerValue":
                return int(data[foundKey])
            if foundKey == "doubleValue":
                return float(data[foundKey])
            if foundKey == "arrayValue":
                return [cleanFirestoreData(v) for v in data[foundKey].get("values", [])]
            if foundKey == "mapValue":
                return cleanFirestoreData(data[foundKey].get("fields", {}))
            return data[foundKey]

        return {k: cleanFirestoreData(v) for k, v in data.items()}

    elif isinstance(data, list):
        return [cleanFirestoreData(i) for i in data]

    return data


def fetch():
    teamNumsRaw = fetchAllDataRecursive("/datas")
    teamNumsRaw = teamNumsRaw.get("/datas/data", {})
    teamNumsField = teamNumsRaw.get("team", [])
    teamList = getValue(teamNumsField)

    allData = {"team": teamList, "root": {}}

    for teamNum in teamList:
        fetchDataByTeamNum(teamNum, allData)

    if allData:
        cleanedData = cleanFirestoreData(allData)
        outputFilename = "fetched_data.json"
        try:
            with open(outputFilename, "w") as outFile:
                json.dump(cleanedData, outFile, indent=4)
            logger.log(f"\nSuccess! Cleaned data saved to {outputFilename}")
        except Exception as e:
            logger.log(f"Error writing to file: {e}")

if __name__ == "__main__":
    fetch()