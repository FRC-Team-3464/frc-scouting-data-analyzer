import os
import sys
import datavis.pieceviewer as pv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logger

red = [
    1,2,3
]
blue = [
    4,5,6
]
logger.log(f"Viewing teams: Red {red}, Blue {blue}")
pv.view(red + blue, True)
