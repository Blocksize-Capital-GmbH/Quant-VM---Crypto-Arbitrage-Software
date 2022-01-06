import math
import time

import numpy as np
from typing import Callable


def interval_converter(interval_string: str) -> float:
    """
    Allowed formats s (seconds), m (minutes), h (hours), d (days), w (week), M (Month)
    Converts a time interval string (10s, 4h, 3d, ...) into seconds as float.
    :param interval_string:
    :return:
    """
    multipliers = {
        "s": 1,
        "m": 60,
        "h": 60 * 60,
        "d": 60 * 60 * 24,
        "w": 60 * 60 * 24 * 7,
        "M": 60 * 60 * 24 * 30
    }

    time_format = interval_string[-1]
    numeric_value = float(interval_string[:-1])

    if time_format in multipliers.keys():
        return numeric_value * multipliers[time_format]
    else:
        raise IntervalFormatError


def generate_sequence_intervals(start, end, interval_s):
    start_floor = math.floor(start / interval_s)
    start_floor = start_floor * interval_s
    sequence = np.arange(start_floor, end, interval_s)
    return sequence


class IntervalFormatError(Exception):
    """
    Raised when a time interval could not be parsed correctly.
    """
