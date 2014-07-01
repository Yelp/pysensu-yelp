#!/usr/bin/env python

import json
import datetime
import socket
import sys
import re
from ordereddict import OrderedDict

SENSU_ON_LOCALHOST = ('localhost', 3030)
# Copied from: http://thomassileo.com/blog/2013/03/31/how-to-convert-seconds-to-human-readable-interval-back-and-forth-with-python/
interval_dict = OrderedDict([("Y", 365*86400),  # 1 year
                             ("M", 30*86400),   # 1 month
                             ("W", 7*86400),    # 1 week
                             ("D", 86400),      # 1 day
                             ("h", 3600),       # 1 hour
                             ("m", 60),         # 1 minute
                             ("s", 1)])         # 1 second

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

def send_event(name, runbook, status, output, team='operations', page=False, tip='',
               check_every='5m', realert_every=1, alert_after='0s', irc_channels=None):
    """Send a new event with the given information. Requires a name, runbook, status code,
    and event output, but the other keys are kwargs and have defaults.

    Valid status codes are 0, 1, and 2. Any other code will raise a ValueError."""
    if not name or not runbook:
        raise ValueError("Name and runbook must be present")
    if status not in range(3):
        raise ValueError("Invalid status code: %i", status)
    result_dict = {
        'name': name,
        'status': status,
        'output': output,
        'handler': 'default',
        'team': team,
        'runbook': runbook,
        'tip': tip,
        'interval': human_to_seconds(check_every),
        'page': page,
        'realert_every': int(realert_every),
        'alert_after': human_to_seconds(alert_after),
    }
    if irc_channels:
        result_dict['irc_channels'] = irc_channels

    json_hash = json.dumps(result_dict)
    sock = socket.socket()
    try:
        sock.connect(SENSU_ON_LOCALHOST)
        sock.sendall(json_hash + '\n')
    finally:
        sock.close()

def send_event_from_check(check, status, output):
    """Send a new event given check information, status, and output of the event.

    'check' must be a dict containing the following keys:
    name, runbook, team, page, tip, check_every, realert_every,
    alert_after, irc_channels

    Valid status codes are 0, 1, and 2. Any other code will raise a ValueError."""
    send_event(
        check['name'],
        check['runbook'],
        status,
        output,
        team=check['team'],
        page=check['page'],
        tip=check['tip'],
        check_every=check['check_every'],
        realert_every=check['realert_every'],
        alert_after=check['alert_after'],
        irc_channels=check['irc_channels']
    )

class SensuEventEmitter:
    """A small class to store redundant informations between events.

    Requires a name and runbook for the event to emit, but the other keys
    are kwargs and have defaults."""

    def __init__(self, name, runbook,
                 team='operations', page=False, tip='', check_every='5m', realert_every=1,
                 alert_after='0s', irc_channels=None):
        if not name or not runbook:
            raise ValueError("Name and runbook must be present")
        self.name = name
        self.runbook = runbook
        self.team = team
        self.page = page
        self.tip = tip
        self.check_every = check_every
        self.realert_every = realert_every
        self.alert_after = alert_after
        self.irc_channels = irc_channels

    def emit_event(self, status, output):
        """Emit a new event with the given status code and output.

        Valid status codes are 0, 1, and 2. Any other code will raise a ValueError."""
        send_event(
            self.name,
            self.runbook,
            status,
            output,
            team=self.team,
            tip=self.tip,
            check_every=self.check_every,
            page=self.page,
            realert_every=self.realert_every,
            alert_after=self.alert_after,
            irc_channels=self.irc_channels
        )
