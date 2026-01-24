import pieceviewer as pv
import logger

red = [
    3464,
    9998,
    3467,
]
blue = [
    3461,
    3441,
    6728
]
logger.log(f"Viewing teams: Red {red}, Blue {blue}")
pv.view(red + blue)