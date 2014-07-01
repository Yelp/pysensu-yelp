#!/usr/bin/env python

import json
import datetime
import socket
import sys
import re

# Copied from: http://thomassileo.com/blog/2013/03/31/how-to-convert-seconds-to-human-readable-interval-back-and-forth-with-python/
def human_to_seconds(string):
    """Convert internal string like 1M, 1Y3M, 3W to seconds.

    :type string: str
    :param string: Interval string like 1M, 1W, 1M3W4h2s...
        (s => seconds, m => minutes, h => hours, D => days, W => weeks, M => months, Y => Years).

    :rtype: int
    :return: The conversion in seconds of string.
    """
    interval_exc = "Bad interval format for {0}".format(string)

    interval_regex = re.compile("^(?P<value>[0-9]+)(?P<unit>[{0}])".format("".join(interval_dict.keys())))
    seconds = 0

    while string:
        match = interval_regex.match(string)
        if match:
            value, unit = int(match.group("value")), match.group("unit")
            if int(value) and unit in interval_dict:
                seconds += value * interval_dict[unit]
                string = string[match.end():]
            else:
                raise Exception(interval_exc)
        else:
            raise Exception(interval_exc)
    return seconds

class SensuCheck():

    SENSU_ON_LOCALHOST = ('localhost', 3030)

    def __init__(self, name, runbook, team='operations', page=False, tip=''):
        self.name = name
        self.runbook = runbook
        self.team = team
        self.page = page
        self.tip = tip
