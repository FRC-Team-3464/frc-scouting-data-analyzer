thank you sam

# FRC Scouting App Data Viewer for Team 3464 "Sim-City"
## _Visualizing data_

[![N|Solid](https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRpCOfbpv0-ShoWwaPwG9dHOmSqrFWk7k0Gew&s)](https://firebase.google.com)

Built for the First Robotics Competition REBUILT 2026

> [!NOTE]
>The code is not fully finished yet

## Features
-Fetch data from Firebase
-View the raw data, with gradients indicating better scores
-Look at one game at a time
-Calculate outcomes of games
-Predict which team will win

## Requirements

- Python 3.14.6
- Internet access to Firebase and The Blue Alliance

## Installation with pyenv

Clone the repository, enter its directory, and install the pinned Python version:

```sh
pyenv install 3.14.6
pyenv local 3.14.6
python --version
```

The committed `.python-version` file makes pyenv select Python 3.14.6 automatically
inside this repository. Then create a virtual environment and install the project
dependencies:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Fetching scouting data

The Streamlit app expects `jsons/fetchedData.json`. Generate it before the first run:

```sh
python fetchfromdb.py
```

Firebase configuration is read from `serviceAccountKey.json`.

## Running the app

```sh
python -m streamlit run app.py
```

Open <http://localhost:8501> if Streamlit does not open a browser automatically.
Run the commands from the repository root because the app uses relative paths for
its data and image files.
