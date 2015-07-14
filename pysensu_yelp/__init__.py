#!/usr/bin/env python

import json
import socket
import re
from ordereddict import OrderedDict


# Status codes for sensu checks
# Code using this module can write pysensu_yelp.Status.OK, etc
# for easy status codes
Status = type('Enum', (), {
    'OK':       0,
    'WARNING':  1,
    'CRITICAL': 2,
    'UNKNOWN':  3
})


# Copied from:
# http://thomassileo.com/blog/2013/03/31/how-to-convert-seconds-to-human-readable-interval-back-and-forth-with-python/
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

    if string is None:
        return None
    while string:
        match = interval_regex.match(string)
        if match:
            value, unit = int(match.group("value")), match.group("unit")
            if unit in interval_dict:
                seconds += value * interval_dict[unit]
                string = string[match.end():]
            else:
                raise Exception("'{0}' unit not present in {1}".format(
                    unit, interval_dict.keys()))
        else:
            raise Exception(interval_exc)
    return seconds


def send_event(name,
               runbook,
               status,
               output,
               team,
               page=False,
               tip=None,
               notification_email=None,
               check_every='5m',
               realert_every=1,
               alert_after='0s',
               dependencies=[],
               irc_channels=None,
               ticket=False,
               project=None,
               source=None,
               ttl=None,
               sensu_host='localhost',
               sensu_port=3030):
    """Send a new event with the given information. Requires a name, runbook, status code,
    and event output, but the other keys are kwargs and have defaults.

    :type name: str
    :param name: Name of the check

    :type runbook: str
    :param runbook: The runbook associated with the check

    :type status: int
    :param status: Exist status code, 0,1,2,3. Must comply with the Nagios conventions.

    :type team: str
    :param team: Team responsible for this check

    :type page: bool
    :param page: Boolean on whether this alert is page-worhty. Activates handlers that send pages.

    :type tip: str
    :param tip: A short 1-line version of the runbook.

    :type notification_email: str
    :param notification_email: A string of email destinations. Unset will default to the "team" default.

    :type check_every: str
    :param check_every: Human readable time unit to let Sensu know how of then this event is fired. Defaults to "5m".

    :type realert_every: int
    :param realert_every: Integer value for filtering repeat occurences. A value of 2 would send every other alert. Defaults to 1.

    :type alert_after: str
    :param alert_after: A human readable time unit to suspend handlers until enough occurences have taken place. Only valid when check_every is accurate.

    :type dependencies: array
    :param dependencies: An array of strings representing checks that *this* check is dependent on.

    :type irc_channels: array
    :param irc_channels: An array of IRC channels to send the event notification to. Defaults to the team setting.

    :type ticket: bool
    :param ticket: A Boolean value to enable ticket creation. Defaults to false.

    :type project: str
    :param project: A string representing the JIRA project that the ticket should go under. Defaults to the team value.

    :type source: str
    :param source: Allows "masquerading" the source value of the event, otherwise comes from the fqdn of the host it runs on.

    :type ttl: str
    :param ttl: A human readable time unit to set the check TTL. If Sensu does not hear from the check after this time unit, Sensu will spawn a new failing event! (aka check staleness) Defaults to None, meaning Sensu will only spawn events when send_event is called.

    """
    if not (name and team):
        raise ValueError("Name and team must be present")
    if not re.match('^[\w\.-]+$', name):
        raise ValueError("Name cannot contain special characters")
    if not runbook:
        runbook = 'Please set a runbook!'
    result_dict = {
        'name': name,
        'status': status,
        'output': output,
        'handler': 'default',
        'team': team,
        'runbook': runbook,
        'tip': tip,
        'notification_email': notification_email,
        'interval': human_to_seconds(check_every),
        'page': page,
        'realert_every': int(realert_every),
        'dependencies': dependencies,
        'alert_after': human_to_seconds(alert_after),
        'ticket': ticket,
        'project': project,
        'source': source,
        'ttl': human_to_seconds(ttl),
    }
    if irc_channels:
        result_dict['irc_channels'] = irc_channels

    json_hash = json.dumps(result_dict)
    sock = socket.socket()
    try:
        sock.connect((sensu_host, sensu_port))
        sock.sendall(json_hash + '\n')
    finally:
        sock.close()
