# FRC Scouting Data Analyzer — Technical Documentation

## 1. Project overview

This repository contains a Streamlit web application for FRC Team 3464, Sim-City.
It combines manually collected scouting records from Google Cloud Firestore with
event schedules and rankings from The Blue Alliance (TBA). The application presents
raw scouting data, team averages, a weighted ranking table, match/scouter status,
and two alliance score predictors.

The application is designed for the 2026 FRC game data model currently represented
by fields such as fuel scored during autonomous, transition, shifts, and endgame,
plus autonomous and endgame climbing.

This is a script-based application, not an installable Python package. There is no
separate compilation or frontend build step. Streamlit executes `app.py` from top to
bottom whenever a user opens the app or interacts with a widget.

## 2. Technology stack

| Component | Purpose |
| --- | --- |
| Python 3.14.6 | Application runtime, pinned by `.python-version` |
| Streamlit | Web UI and server |
| pandas | Tables, CSV loading, filtering, and calculated columns |
| requests | Firestore REST API, TBA API, and image requests |
| Pillow | Decoding images loaded over HTTP |
| streamlit-image-button | Image-based button in the ranker tab |
| Bokeh | Pinned UI/visualization dependency |
| Firestore REST API | Source of scouting records |
| The Blue Alliance API v3 | Source of event matches and official rankings |

`firebase`, `firebase_admin`, and `numpy` are pinned in `requirements.txt`, but the
current source files do not import them. Firestore access is implemented directly
with `requests`, not with either Firebase Python library.

## 3. Repository layout

| Path | Role |
| --- | --- |
| `app.py` | Streamlit entry point and all six UI tabs |
| `fetchfromdb.py` | Downloads and normalizes scouting data from Firestore |
| `bluealliance.py` | Downloads event matches or rankings from TBA |
| `avgs.py` | Calculates per-team aggregate scouting statistics |
| `jsonToCsv.py` | Converts aggregate JSON into a CSV table |
| `ranking.py` | Extracts the ordered team list from TBA rankings |
| `teamPredictor.py` | Detailed autonomous/teleop alliance simulator |
| `stdTeamPredictor.py` | Mean and standard-deviation alliance predictor |
| `requirements.txt` | Pinned Python dependencies |
| `.python-version` | pyenv runtime pin (`3.14.6`) |
| `serviceAccountKey.json` | Firebase web configuration used by the REST client |
| `mult.csv` | Persistent weighting history used by the ranker tab |
| `dog.jpeg` | Image used as the ranker update button |
| `jsons/` | Generated and downloaded runtime data |
| `oldJsons/` | Older sample/archive data not used at runtime |

## 4. Runtime architecture

The primary data flow is:

```text
Firestore REST API ──> fetchfromdb.py ──> jsons/fetchedData.json
                                                │
                                                ├──> avgs.py
                                                │      │
                                                │      └──> jsons/avgs.json
                                                │                │
                                                │                └──> jsonToCsv.py
                                                │                          │
                                                │                          └──> jsons/avgs.csv
                                                │
                                                ├──> teamPredictor.py
                                                └──> stdTeamPredictor.py

The Blue Alliance API ──> bluealliance.py ──> jsons/matches.json
                                             └──> jsons/rankings.json

Generated files + mult.csv ──> app.py ──> Streamlit UI on localhost:8501
```

### Startup sequence

When Streamlit evaluates `app.py`, the module immediately performs these operations
before rendering the page:

1. Calls `bFetch("matches")` and writes `jsons/matches.json`.
2. Calls `bFetch("rankings")` and writes `jsons/rankings.json`.
3. Reads `jsons/fetchedData.json` and computes team averages.
4. Writes `jsons/avgs.json`.
5. Converts those averages into `jsons/avgs.csv`.
6. Reads the TBA ranking order.
7. Builds the Streamlit page and its tabs.

Because Streamlit reruns the script after widget interactions, the two TBA requests
and aggregate-file writes can occur many times during a session. Firebase data is
not refreshed by `app.py`; the `ffetch()` call is currently commented out.

## 5. Configuration and external services

### Firebase/Firestore

`fetchfromdb.py` loads two values from `serviceAccountKey.json`:

- `apiKey`
- `projectId`

Despite its name, this file is not in the normal Firebase Admin service-account
format. It contains Firebase web-client configuration and no private key. The code
passes the API key as a query parameter to the public Firestore REST endpoint.

The expected Firestore organization is:

```text
datas/data                 document containing the `team` array
<team number>/<match ID>   one match document for each scouted team/match
```

`fetch()` first reads `/datas/data`, extracts the team list, requests the root
collection for every team number, converts Firestore typed values into ordinary
Python values, and saves the result locally.

The Firebase API key does not by itself authorize secure access. Effective access
control depends on the deployed Firestore Security Rules. Those rules are outside
this repository and should be reviewed separately.

### The Blue Alliance

`bluealliance.py` calls:

```text
https://www.thebluealliance.com/api/v3/event/<event>/<method>
```

Supported methods in current usage are `matches` and `rankings`. The event identifier
is hardcoded as `2026week0`, and the API key is hardcoded in the source. Before
deployment, the key should be rotated and loaded from an environment variable or
Streamlit secrets. The event should also be configurable rather than edited in code.

## 6. Local data model

### `jsons/fetchedData.json`

The normalized Firestore output has this structure:

```json
{
  "team": [3464, 1234],
  "root": {
    "3464": {
      "1": {
        "teamNumber": 3464,
        "matchNumber": 1,
        "eventName": "...",
        "autoFuel": 0,
        "autoClimbed": false,
        "transitionFuel": 0,
        "shift1HubActive": true,
        "shift1Fuel": 0,
        "endgameFuel": 0,
        "endgameClimbLevel": "Didn't climb"
      }
    }
  }
}
```

The `team` array is the complete configured team list. A team can appear there while
having no entry in `root`, so consumers must handle zero matches. Match fields found
in the current dataset include:

- Identification: `eventName`, `teamNumber`, `matchNumber`, `name`, `scoutingTeam`
- Autonomous: `autoFuel`, `autoHoardedFuel`, `autoClimbed`
- Transition: `transitionFuel`, `transitionCollected`
- Shifts 1–4: `shiftNHubActive`, `shiftNFuel`, `shiftNHoardedFuel`,
  `shiftNCollected`, and `shiftNDefense`
- Endgame: `endgameFuel`, `endgameClimbLevel`
- Robot traits: `multiShooter`, `static`, `crossedBump`, `underTrench`
- Reliability/notes: `failure`, `robotError`, `notes`

The application tolerates some absent fields by using default values, but string
formats such as climb levels are not interpreted consistently by every module.

### Generated files

| File | Producer | Consumer |
| --- | --- | --- |
| `jsons/fetchedData.json` | `fetchfromdb.py` | App, averages, both predictors |
| `jsons/matches.json` | `bluealliance.py` | Match schedule tab |
| `jsons/rankings.json` | `bluealliance.py` | `ranking.py`, predictor tabs |
| `jsons/avgs.json` | `app.py` + `avgs.py` | `jsonToCsv.py` |
| `jsons/avgs.csv` | `jsonToCsv.py` | Individual, ranker, and table views |

Most generated files are ignored by Git and must be recreated locally.

## 7. Module behavior

### `fetchfromdb.py`

- `getValue()` extracts a small subset of Firestore scalar/array types.
- `fetchAllDataRecursive()` walks a Firestore document path and stores documents
  containing fields.
- `fetchDataByTeamNum()` downloads match documents for one team.
- `cleanFirestoreData()` recursively converts Firestore's typed JSON representation,
  including maps and arrays, into normal JSON values.
- `fetch()` coordinates team discovery, downloads every team, and writes the result.

Network errors are printed and generally converted into partial or empty output
rather than raised. The REST requests have no explicit timeout, pagination token
handling, authentication session, or retry policy.

### `bluealliance.py`

`fetch(method)` performs one authenticated TBA request and writes the JSON response.
Errors are printed but not raised. The success log always calls the result “matches,”
even when downloading rankings.

### `avgs.py`

`processTeamAverages()` produces parallel arrays suitable for conversion into CSV.
For each team it calculates:

- Number of scouting entries
- Average autonomous fuel
- Average transition fuel
- Average fuel during the first active-hub shift
- Average fuel during the second active-hub shift
- Average endgame fuel
- Average total fuel
- Autonomous climb percentage
- Failure percentage
- Average endgame climb points
- Whether any match identifies the robot as multi-turret or static

The first active shift is selected as shift 1 or 2, and the second as shift 3 or 4,
based on the `shiftNHubActive` flags. Empty teams receive zero averages and zero
percentages.

### `jsonToCsv.py`

`convertAvgsToCsv()` treats each key in the aggregate JSON as a CSV column and writes
one row per team. Calling the function from `app.py` works. The module's standalone
`__main__` block contains a naming error (`convert_avgs_to_csv` rather than
`convertAvgsToCsv`), so `python jsonToCsv.py` currently fails.

### `ranking.py`

`read_matches()` reads the TBA rankings response, strips the `frc` prefix from each
`team_key`, and returns team numbers in API order. Its error messages incorrectly
refer to `matches.json` even though it reads `rankings.json`.

### `teamPredictor.py`

This predictor accepts three red and three blue team numbers and combines two
simulations:

1. **Autonomous calculation:** Excludes “Did not participate” records, scores fuel
   plus 15 points for an autonomous climb, divides performances into success/failure
   sets using half of the team's maximum score, and estimates floor/likely/ceiling.
   It limits alliance climb credit to two likely climbers.
2. **Teleop calculation:** Converts recorded fuel into rates, applies active-hub
   schedules, models hopper storage with a 24-fuel cap, optionally models defensive
   pressure, and adds endgame climbing.

The predictor adds autonomous and teleop ranges. It estimates win probability by
treating the alliance ranges as approximately six standard deviations and applying
a normal-distribution comparison. Results are returned directly to the caller.

This is a heuristic model, not a calibrated statistical forecast. Several constants
are embedded directly in the module, including shift durations, fuel cap, climb
points, congestion factors, and defensive effects.

### `stdTeamPredictor.py`

This simpler predictor sums each alliance's mean fuel and climb output. It calculates
alliance standard deviation as the square root of the sum of individual team score
variances. If one alliance's entire range is above the other's range, it declares a
winner; otherwise it reports “Too Close.”

`predict()` returns the result directly to its caller. Its optional `stdev_input`
argument controls the range multiplier and defaults to one standard deviation.

## 8. Streamlit interface

`app.py` creates six tabs.

### Individual

Provides red and blue alliance team selectors based on `avgs.csv`. It shows the
selected teams' aggregate rows and the sum of their average total fuel.

### Data

Flattens every team/match record into a pandas DataFrame. Sidebar controls filter by
team and event. The tab reports record, team, and match counts and displays all raw
fields. A `robotError` map is converted into a comma-separated list of true flags.

### Ranker

Loads aggregate team data and the latest row from `mult.csv`. Six number inputs apply
weights to aggregate categories and create a `Pickability` score. Clicking the dog
image appends the weights to `mult.csv`. The table also inserts each team's live TBA
rank.

### Matches

Displays TBA qualification matches, red/blue scores, the six teams, assigned scouting
initials/names, and verification status. Scout assignments are embedded as placeholder
groups (`a` through `r`) and rotated using a fixed match-order sequence.

### STD predictor

Provides selectors containing only teams with local scouting records. It accepts two
three-team alliances and executes `stdTeamPredictor.predict()` only when the STD
Predict button is selected. The result is retained in Streamlit session state and
the tab displays the submitted teams, predicted totals, and red/blue score ranges
without creating a shared output file.

### Game Predictor

Provides selectors containing teams with scouting records, validates two distinct
three-team alliances, and runs the detailed predictor after form submission. It
stores the result in the user's Streamlit session and displays the submitted teams,
minimum, likely, and maximum scores plus red/blue win chances.

## 9. Installation and operation

### Initial setup with pyenv

```sh
pyenv install 3.14.6
pyenv local 3.14.6
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The `.python-version` file makes pyenv select Python 3.14.6 in the repository.

### Download scouting data

```sh
source .venv/bin/activate
python fetchfromdb.py
```

This must succeed at least once before the app starts because `app.py` immediately
opens `jsons/fetchedData.json`.

### Start the application

```sh
source .venv/bin/activate
python -m streamlit run app.py
```

Keep the terminal process running and browse to <http://localhost:8501>. All commands
must run from the repository root because the application uses relative paths.

### Refresh data

To refresh scouting records, stop Streamlit or use another terminal and run:

```sh
source .venv/bin/activate
python fetchfromdb.py
```

Then reload the Streamlit page. TBA match and ranking data refreshes on Streamlit
reruns under the current architecture.

## 10. Troubleshooting

### Browser says localhost cannot be reached

No Streamlit server is listening. Start it with:

```sh
python -m streamlit run app.py
```

Use the exact URL shown in the terminal and keep that terminal open.

### Missing `jsons/fetchedData.json`

Run `python fetchfromdb.py`. Check the Firebase project configuration, Firestore
Security Rules, network access, and console response codes if the download fails.

### TBA errors or missing rankings/matches

Confirm the event identifier and API key in `bluealliance.py`, as well as internet
connectivity. An invalid event can leave stale files in place or lead to downstream
errors because API failures are not raised.

### Team has no records

This is a valid state: a team may exist in the top-level team list but not under
`root`. Aggregate percentages and averages should remain zero for such teams.

### Port 8501 is already occupied

Streamlit may select another port. Use its printed URL or choose one explicitly:

```sh
python -m streamlit run app.py --server.port 8502
```

## 11. Known limitations and risks

1. The TBA API key is committed in source and should be rotated.
2. Runtime settings are hardcoded rather than loaded from environment variables or
   Streamlit secrets.
3. TBA downloads and aggregate generation happen at import time and on Streamlit
   reruns, increasing latency and external API usage.
4. External HTTP requests do not specify timeouts and can block indefinitely.
5. API errors are printed rather than surfaced clearly in the UI or propagated.
6. Runtime JSON and CSV files act as shared mutable state; concurrent users can
   overwrite each other's predictor outputs and multiplier history.
7. `mult.csv` grows by appending a row on each ranker update and has no cleanup.
8. Predictor scoring rules and field formats are inconsistent in places. For example,
   one module expects endgame values like `Level 1`, while another checks `1`.
9. Predictor sleeps block Streamlit execution without providing synchronization.
10. There are no automated tests, lint configuration, CI workflow, structured
    logging, or deployment configuration.
11. Some dependency pins appear unused and increase installation time considerably.
12. Scouter assignment values in `app.py` are placeholders and hardcoded.

## 12. Recommended improvement order

1. Rotate the committed TBA key and move all configuration to `.streamlit/secrets.toml`
   or environment variables, with a checked-in example file.
2. Move network fetching out of module import/startup. Add explicit refresh controls
   and cache successful responses with `st.cache_data`.
3. Add request timeouts, `raise_for_status()`, useful UI error messages, and protection
   against incomplete generated files.
4. Normalize the scouting schema, particularly climb levels and robot-error names,
   before calculations.
5. Extract the six tabs from `app.py` into focused UI modules.
6. Add unit tests for Firestore conversion, zero-match teams, aggregates, and both
   predictors, followed by a small app startup smoke test.
7. Remove unused dependencies after confirming that no deployment tooling relies on
   them.
8. Fix the standalone CSV converter and ranking error messages.

## 13. Development notes

- Use Python 3.14.6 to match the repository pin.
- Do not commit generated scouting or predictor JSON files; they may contain names,
  notes, and operational scouting information.
- Treat `jsons/fetchedData.json` as potentially sensitive team data.
- Validate changes against both populated teams and teams with zero matches.
- Remember that a normal Streamlit widget interaction reruns the full script unless
  work is moved behind forms, buttons, fragments, or cache decorators.
