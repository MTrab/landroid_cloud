"""pyWorxCloud states definition."""
from __future__ import annotations

# Valid states - some are missing as these haven't been identified yet
STATE_TO_DESCRIPTION = {
    0: "idle",
    1: "home",
    2: "start sequence",
    3: "leaving home",
    4: "follow wire",
    5: "searching home",
    6: "searching wire",
    7: "mowing",
    8: "lifted",
    9: "trapped",
    10: "blade blocked",
    11: "debug",
    12: "remote control",
    30: "going home",
    31: "zoning",
    32: "cutting edge",
    33: "searching area",
    34: "pause",
}

# Valid error states
ERROR_TO_DESCRIPTION = {
    0: "no error",
    1: "trapped",
    2: "lifted",
    3: "wire missing",
    4: "outside wire",
    5: "rain delay",
    6: "close door to mow",
    7: "close door to go home",
    8: "blade motor blocked",
    9: "wheel motor blocked",
    10: "trapped timeout",
    11: "upside down",
    12: "battery low",
    13: "reverse wire",
    14: "charge error",
    15: "timeout finding home",
    16: "locked",
    17: "battery temperature error",
    18: "dummy model",
    19: "battery trunk open timeout",
    20: "wire sync",
    21: "msg num",
}
