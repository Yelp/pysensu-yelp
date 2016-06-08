#!/usr/bin/env python

import argparse
import json
import socket
import subprocess
import re
try:
    from collections import OrderedDict
except ImportError:
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


def send_event(
    name,
    runbook,
    status,
    output,
    team,
    page=False,
    tip=None,
    notification_email=None,
    check_every='30s',
    realert_every=-1,
    alert_after='0s',
    dependencies=[],
    irc_channels=None,
    ticket=False,
    project=None,
    source=None,
    ttl=None,
    sensu_host='localhost',
    sensu_port=3030,
):
    """Send a new event with the given information. Requires a name, runbook,
    status code, and event output, but the other keys are kwargs and have
    defaults.

    :type name: str
    :param name: Name of the check

    :type runbook: str
    :param runbook: The runbook associated with the check

    :type status: int
    :param status: Exist status code, 0,1,2,3. Must comply with the Nagios
                   conventions. See `the Sensu docs <https://sensuapp.org/docs/latest/checks#sensu-check-specification>`_
                   for the exact specification.

    :type team: str
    :param team: Team responsible for this check. This team must already be defined
                 server-side in the Sensu handler configuration.

    :type page: bool
    :param page: Boolean on whether this alert is page-worthy. Activates
                 handlers that send pages.

    :type tip: str
    :param tip: A short 1-line version of the runbook. Example:
                "Set clip-jawed monodish to 6"

    :type notification_email: str
    :param notification_email: A comma-separated string of email destinations. Unset will
                               default to the "team" default.

    :type check_every: str
    :param check_every: Human readable time unit to let Sensu know how of then
                        this event is fired. Defaults to "30s". If this parameter
                        is not set correctly, the math for `alert_after` will be
                        incorrect.

    :type realert_every: int
    :param realert_every: Integer value for filtering repeat occurrences. A
                          value of 2 would send every other alert. Defaults to -1,
                          which is a special value representing exponential backoff.
                          (alerts on event number 1,2,4,8, etc)

    :type alert_after: str
    :param alert_after: A human readable time unit to suspend handler action until
                        enough occurrences have taken place. Only valid when
                        check_every is accurate.

    :type dependencies: array
    :param dependencies: An array of strings representing checks that *this*
                         check is dependent on.

    :type irc_channels: array
    :param irc_channels: An array of IRC channels to send the event
                         notification to. Defaults to the team setting.

    :type ticket: bool
    :param ticket: A Boolean value to enable ticket creation. Defaults to false.

    :type project: str
    :param project: A string representing the JIRA project that the ticket
                    should go under. Defaults to the team value.

    :type source: str
    :param source: Allows "masquerading" the source value of the event,
                   otherwise comes from the fqdn of the host it runs on.
                   This is especially important to set on events that could
                   potentially be created from multiple hosts. For example if
                   ``send_event`` is called from three different hosts in a cluster,
                   you wouldn't want three different events, you would only want
                   one event that looked like it came from ``the_cluster``, so
                   you would set ``source='the_cluster'``.

    :type ttl: str
    :param ttl: A human readable time unit to set the check TTL. If Sensu does
                not hear from the check after this time unit, Sensu will spawn a
                new failing event! (aka check staleness) Defaults to None,
                meaning Sensu will only spawn events when send_event is called.

    Note on TTL events and alert_after:
    ``alert_after`` and ``check_every`` only really make sense on events that are created
    periodically. Setting ``alert_after`` on checks that are not periodic is not advised
    because the math will be incorrect. For example, if check was written that called
    ``send_event`` on minute values that were prime, what should the ``check_every`` setting
    be? No matter what it was, it would be wrong, and therefore ``alert_after`` would be incorrectly
    calculated (as it is a function of the number of failing events seen multiplied by the ``check_every``
    setting). If in doubt, set ``alert_after`` to ``0`` to ensure you never miss an alert
    due to incorrect ``alert_after`` math on non-periodic events. (See also this
    `Pull request <https://github.com/sensu/sensu/pull/1200>`_)

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


def do_command_wrapper():
    parser = argparse.ArgumentParser(description='Execute a nagios plugin and report the results to a local Sensu agent')
    parser.add_argument('sensu_dict')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()

    sensu_dict = json.loads(args.sensu_dict)

    p = subprocess.Popen(args.command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    output, _ = p.communicate()
    status = p.wait()

    if status > 3:
        status = 3

    sensu_dict['status'] = status
    sensu_dict['output'] = output[:1200]
    send_event(**sensu_dict)

if __name__ == '__main__':
    do_command_wrapper()
