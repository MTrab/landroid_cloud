"""pyWorxCloud states definition."""
from __future__ import annotations

# Valid states - some are missing as these haven't been identified yet
StateDict = {
    0: "Idle",
    1: "Home",
    2: "Start sequence",
    3: "Leaving home",
    4: "Follow wire",
    5: "Searching home",
    6: "Searching wire",
    7: "Mowing",
    8: "Lifted",
    9: "Trapped",
    10: "Blade blocked",
    11: "Debug",
    12: "Remote control",
    30: "Going home",
    31: "Zoning",
    32: "Cutting edge",
    33: "Searching area",
    34: "Pause",
}

# Valid error states
ErrorDict = {
    0: "No error",
    1: "Trapped",
    2: "Lifted",
    3: "Wire missing",
    4: "Outside wire",
    5: "Rain delay",
    6: "Close door to mow",
    7: "Close door to go home",
    8: "Blade motor blocked",
    9: "Wheel motor blocked",
    10: "Trapped timeout",
    11: "Upside down",
    12: "Battery low",
    13: "Reverse wire",
    14: "Charge error",
    15: "Timeout finding home",
    16: "Locked",
    17: "Battery temperature error",
    18: "dummy model",
    19: "Battery trunk open timeout",
    20: "wire sync",
    21: "msg num",
}
