from typing import TypedDict
from config import Config


class Instant(TypedDict):
    __instant: int


def unix_time(instant: Instant):
    unix_delta = 1000
    return int(instant['__instant'] / unix_delta)


def time_for_amo(instant: Instant):
    return unix_time(instant) + Config.utc_delta_seconds
