# Application Improvement Roadmap

This document lists recommended improvements for the FRC Scouting Data Analyzer.
Items are ordered by priority, with deployment safety and runtime reliability first.

## Priority 1: Remove hardcoded credentials

### Current issue

The Blue Alliance API key and event identifier are hardcoded in `bluealliance.py`.
Firebase configuration is read from the committed `serviceAccountKey.json` file.

Hardcoded credentials are difficult to rotate and can be exposed when the repository
is shared or made public. The existing TBA key should be rotated because it has
already been committed to source control.

### Recommended change

Load local configuration from environment variables and deployed configuration from
Streamlit secrets. For example:

```python
import os

api_key = os.environ["TBA_API_KEY"]
event = os.getenv("TBA_EVENT", "2026week0")
```

For Streamlit Community Cloud, use `.streamlit/secrets.toml` locally and enter the
same values in the deployment settings. Never commit the local secrets file. Commit
only a sanitized example file.

### Affected files

- `bluealliance.py`
- `fetchfromdb.py`
- `serviceAccountKey.json`
- `.gitignore`
- Deployment documentation

## Priority 2: Stop fetching TBA data on every Streamlit rerun

### Current issue

`app.py` calls `bFetch("matches")` and `bFetch("rankings")` at the module level.
Streamlit reruns the complete script after widget interactions, so a filter or button
click can issue two new TBA API requests and overwrite two local files.

This increases startup latency, wastes API quota, and makes the app dependent on TBA
availability during unrelated user interactions.

### Recommended change

Return data from the TBA service instead of writing files, then cache it:

```python
@st.cache_data(ttl=300)
def load_tba_event(event):
    matches = fetch_tba(event, "matches")
    rankings = fetch_tba(event, "rankings")
    return matches, rankings
```

Add a manual refresh button that clears the cached data when fresh results are
required.

### Affected files

- `app.py`
- `bluealliance.py`
- `ranking.py`

## Priority 3: Add HTTP timeouts and structured error handling

### Current issue

Requests to Firestore, TBA, and remote images do not specify timeouts. A stalled
connection can therefore block the Streamlit script. API functions print errors but
often continue, leaving missing or stale files that fail elsewhere.

### Recommended change

Every network request should use a reasonable timeout and raise unsuccessful status
codes:

```python
response = requests.get(url, headers=headers, timeout=15)
response.raise_for_status()
```

Service functions should return data or raise a meaningful custom exception. The UI
should catch those exceptions and display `st.error()` or a warning with an explicit
fallback to previously cached data.

Consider using a shared `requests.Session` with a bounded retry policy for temporary
server and network failures.

### Affected files

- `bluealliance.py`
- `fetchfromdb.py`
- `app.py`

## Priority 4: Remove shared mutable runtime files

### Current issue

The predictor results have been moved into Streamlit session state, but `mult.csv`
remains shared and writable. In a deployed application:

- One user's multiplier changes affect other users.
- Simultaneous writes can corrupt the file.
- Local filesystem changes may disappear when the host restarts.
- Multiple application instances do not share a filesystem.

### Recommended change

Choose storage based on the desired behavior:

- Use `st.session_state` for per-user, temporary multiplier settings.
- Use Firestore for global, persistent team settings.
- Use a database document per user if settings should persist privately.

Avoid using CSV or JSON files as writable application state in a multi-user deployed
environment.

### Affected files

- `app.py`
- `mult.csv`

## Priority 5: Remove the required local Firestore snapshot

### Current issue

The app requires `jsons/fetchedData.json`, but the file is generated locally and
ignored by Git. A clean cloud deployment does not contain it, so application startup
fails until a separate fetch process creates it.

### Recommended change

Refactor `fetchfromdb.py` so its main operation returns a normalized Python dictionary.
Call that function from a cached Streamlit data loader:

```python
@st.cache_data(ttl=300)
def load_scouting_data():
    return fetch_firestore_data()
```

The app should process the returned object directly. A local JSON snapshot may remain
as an optional development or offline fallback, but it should not be required in
production.

### Affected files

- `fetchfromdb.py`
- `app.py`
- `avgs.py`
- Both predictor modules

## Priority 6: Improve predictor validity

### Current issue

The detailed Game Predictor derives win probability by treating its simulated
minimum-to-maximum range as six standard deviations. The range is made from heuristic
floor and ceiling scenarios rather than calibrated statistical confidence bounds.

Other limitations include:

- Sample size is not reflected in confidence.
- Recent and old matches receive equal weight.
- Team performances are assumed to be independent.
- Field interaction and defense are simplified.
- A single extreme performance can widen a range considerably.
- Inconsistent climb strings can omit points.

### Recommended change

Replace or supplement the current probability formula with an empirical bootstrap or
Monte Carlo simulation:

1. Calculate a total score for every historical team performance.
2. Sample one historical performance for every selected team.
3. Sum the three red and three blue sampled performances.
4. Repeat the simulation, for example 10,000 times.
5. Calculate win chance from the proportion of simulated wins.
6. Calculate prediction ranges from percentiles of the simulated alliance scores.

The UI should also display:

- Number of matches used for each team
- A warning for insufficient data
- The model/version used
- A clear label when a result remains heuristic rather than calibrated

### Affected files

- `teamPredictor.py`
- `stdTeamPredictor.py`
- Predictor sections in `app.py`

## Priority 7: Normalize the scouting schema

### Current issue

Modules interpret some values differently. One predictor expects climb values such
as `"1"`, while other code and current records use values such as `"Level 1"`.
Robot error names also vary in spelling and capitalization.

### Recommended change

Create one shared domain/scoring module that normalizes all external values before
calculation:

```python
def climb_points(value):
    normalized = str(value).strip().lower()
    return {
        "1": 10,
        "level 1": 10,
        "2": 20,
        "level 2": 20,
        "3": 30,
        "level 3": 30,
    }.get(normalized, 0)
```

Shared normalization should cover:

- Team and match numbers
- Numeric scoring fields
- Boolean values
- Endgame climb levels
- Robot error names
- Missing fields

Using typed data classes or validation models would further clarify the expected
schema and reject malformed records early.

### Affected files

- `avgs.py`
- `teamPredictor.py`
- `stdTeamPredictor.py`
- `fetchfromdb.py`
- A new shared domain/scoring module

## Priority 8: Split up `app.py`

### Current issue

`app.py` combines data retrieval, preprocessing, session management, table logic,
HTML generation, predictor orchestration, and all six tabs. This makes changes harder
to review and individual features difficult to test.

### Recommended structure

```text
app.py
ui/
├── individual.py
├── data_viewer.py
├── ranker.py
├── matches.py
└── predictors.py
services/
├── firebase.py
└── tba.py
domain/
├── scoring.py
├── averages.py
└── predictions.py
```

`app.py` should be limited to page configuration, data-loading coordination, and tab
composition. UI modules should render components, service modules should perform I/O,
and domain modules should contain calculations without Streamlit dependencies.

## Priority 9: Fix smaller defects and cleanup issues

The following issues should be addressed as focused maintenance changes:

- `jsonToCsv.py` calls nonexistent `convert_avgs_to_csv()` when executed directly.
- `ranking.py` reports errors for `matches.json` even though it reads `rankings.json`.
- `ranking.py` can return `None`, while UI code assumes rankings are iterable.
- `loadImageFromUrl()` appears unused and lacks timeout/status validation.
- Some imports, constants, and dependency pins appear unused.
- `.gitignore` contains duplicate entries.
- Match/scouter assignment names in `app.py` remain hardcoded placeholders.
- API functions use `print()` instead of structured logging or UI-friendly errors.
- CSV/JSON conversion is performed during normal UI reruns even when inputs have not
  changed.

## Priority 10: Add automated tests and continuous integration

### Current issue

The repository has no automated test suite or CI workflow. Regressions are discovered
only by starting the Streamlit interface and manually testing it.

### Recommended tests

Add unit tests for:

- Firestore typed-value conversion
- Empty team lists and teams with zero matches
- Missing and malformed fields
- Average score calculations
- Climb normalization
- Robot-error normalization
- STD Predictor output
- Game Predictor outputs and probabilities summing to 100%
- Unknown team handling
- TBA success, failure, and timeout behavior using mocked HTTP responses
- Multiplier/session behavior

Add a small Streamlit startup smoke test and a CI workflow that runs compilation,
tests, formatting, and lint checks on every pull request.

Suggested tooling:

- `pytest`
- `pytest-cov`
- `responses` or `requests-mock`
- `ruff`
- GitHub Actions

## Suggested implementation phases

### Phase 1: Safe deployment

1. Rotate and externalize credentials.
2. Add HTTP timeouts and reliable error handling.
3. Cache TBA and Firestore requests.
4. Remove the required generated Firestore JSON file.
5. Replace `mult.csv` writes with appropriate state storage.

### Phase 2: Correctness

1. Normalize the scouting schema.
2. Add unit tests for existing calculations.
3. Correct climb and robot-error handling.
4. Replace or relabel heuristic win probabilities.
5. Add sample-size and missing-data warnings.

### Phase 3: Maintainability

1. Split `app.py` into UI, service, and domain modules.
2. Remove unused dependencies and code.
3. Fix standalone script and error-message defects.
4. Add linting, formatting, coverage reporting, and CI.

## Recommended immediate scope

Before making the app publicly accessible, complete at least Priorities 1 through 5.
Those changes address credential exposure, excessive API usage, network hangs, shared
multi-user state, and clean-deployment failures. Predictor and schema improvements
should follow before the displayed probabilities are used for competition decisions.
