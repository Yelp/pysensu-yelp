#!/usr/bin/env python

import argparse
import json
import socket
import subprocess
import re
import sys

import six

"""
pysensu-yelp
============

A library to send `Sensu <https://sensuapp.org/>`_ events from Python
using `Yelp's Sensu-Handlers <https://github.com/Yelp/sensu_handlers>`_.

What This is Used For
^^^^^^^^^^^^^^^^^^^^^

Sensu is a very flexible monitoring framework. Combined it with
Yelp's ``sensu_handlers`` and you have the ability to create
arbitrary alerts for teams with no configuration necessary on the
Sensu server.

This is commonly used in infrastructure code, but can also be used
to instrument service-level code. For example, you might use this library
to track the health periodic tasks. Or you might use it to send special
alerts for rare exceptions that require manual intervention.

**Note:** Sending Sensu events to the infrastructure is not "free".
Care should be taken to ensure a script does not flood the monitoring
infrastructure with lots of events to process. In practice humans are
not responding to rapidly occurring events, sending anything more
than about 1 event per minute is probably just wasting CPU resources
on the monitoring infrastructure.

Basic Example
^^^^^^^^^^^^^

Here is an example that uses an internal function, ``check_the_thing`` to
verify the health of something, and uses ``send_event`` to send a Sensu
event based on the health of that something::

    import pysensu_yelp

    def check_the_thing():
        return True

    is_it_ok = check_the_thing()
    if is_it_ok is True:
        status=0
        output="Everything is fine"
    else:
        status=2
        output="Critical: Everything is NOT fine"

    pysensu_yelp.send_event(
        name="my_cool_check",
        output=output,
        status=status,
        team="my_team",
        runbook="http://hellogiggles.hellogiggles.netdna-cdn.com/wp-content/uploads/2014/12/28/this-is-fine-meme.jpg",
    )


Staleness Alerts (TTL)
^^^^^^^^^^^^^^^^^^^^^^

Sometimes you want Sensu to alert you when something hasn't checked
in and reported its status in a while. In Nagios this concept is
referenced as `freshness_threshold` and is a server-side configuration.

In Sensu it is called `ttl` and is a check-defined configuration option.
`pysensu-yelp` exposes this parameter as `ttl`, as a human-readable time
unit. (`ttl=1h` will make Sensu send an alert if the `send_event` function
isn't called at least once an hour)

**Note**: If you have removed a check, renamed it, or moved it to a different
host, Sensu will *still* fire a staleness alert. This is because the
`source/check_name` is the primary key to distinguish events in Sensu.
Changing anything that adjusts that primary key will cause a new event to be
created, and the old one will linger forever. You must manually "resolve" that
old alert, either using the sensu-cli or using a Sensu dashboard to make it go
away.


Using pysensu-yelp in a Docker Container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

At Yelp we use the `yocalhost` ip, `169.254.255.254` to allow things in docker
containers to utilize services on the host. ``pysensu-yelp`` uses this yocalhost
IP by default.

Additionally, docker containers should be considered ephemeral and potentially
launched from any number of hosts. This is potentially confusing to Sensu, because
the "hostname" is part of the identifier of an alert. The more correct thing to do
is to specify the `source` of the alert, so that it will use your unique source
instead of the hostname of the server that happens to host the docker container
at that exact moment.

A final invocation might look like this::

    pysensu_yelp.send_event(
        name="my_cool_check",
        output="The thing is broken",
        status=2,
        team="ops",
        runbook="http://pysensu-yelp.readthedocs.org",
        ttl="1h",
        source="my_cool_service",
    )

"""

from collections import OrderedDict

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
    slack_channels=None,
    ticket=False,
    project=None,
    priority=None,
    source=None,
    tags=[],
    ttl=None,
    sensu_host='169.254.255.254',
    sensu_port=3030,
    component=None,
    description=None,
):
    """Send a new event with the given information. Requires a name, runbook,
    status code, event output, and team but the other keys are kwargs and have
    defaults.

    :type name: str
    :param name: Name of the check

    :type runbook: str
    :param runbook: The runbook associated with the check

    :type status: int
    :param status: Exit status code, 0,1,2,3. Must comply with the Nagios
                   conventions. See `the Sensu docs <https://sensuapp.org/docs/latest/checks#sensu-check-specification>`_
                   for the exact specification.

    :type output: str
    :param output: The output of the check itself. May include CRIT/WARN/OK to make
                   it easy to evaluate how things went. Should be newline separated,
                   but try to put the most relevant data in the first line.
                   Example:
                   OK: Everything is fine
                   or
                   CRIT: Accounts are locked. Users can't buy widgets.

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

    :type dependencies: list
    :param dependencies: An list of strings representing checks that *this*
                         check is dependent on.

    :type irc_channels: list
    :param irc_channels: An list of IRC channels to send the event
                         notification to. Defaults to the team setting. Set an empty
                         list to specify no IRC notifications.

    :type slack_channels: list
    :param slack_channels: An list of Slack channels to send the event
                         notification to. Defaults to the team setting. Set an empty
                         list to specify no Slack notifications.

    :type ticket: bool
    :param ticket: A Boolean value to enable ticket creation. Defaults to false.

    :type project: str
    :param project: A string representing the JIRA project that the ticket
                    should go under. Defaults to the team value.

    :type priority: str
    :param priority: A JIRA priority to use when creating a ticket. This only
                     makes sense to use when in combination with the ticket
                     parameter set to true.

    :type source: str
    :param source: Allows "masquerading" the source value of the event,
                   otherwise comes from the fqdn of the host it runs on.
                   This is especially important to set on events that could
                   potentially be created from multiple hosts. For example if
                   ``send_event`` is called from three different hosts in a cluster,
                   you wouldn't want three different events, you would only want
                   one event that looked like it came from ``the_cluster``, so
                   you would set ``source='the_cluster'``.

    :type tags: list
    :param tags: An list of arbitrary tags that can be used in handlers for
                 different metadata needs such as labels in JIRA handlers.

    :type ttl: str
    :param ttl: A human readable time unit to set the check TTL. If Sensu does
                not hear from the check after this time unit, Sensu will spawn a
                new failing event! (aka check staleness) Defaults to None,
                meaning Sensu will only spawn events when send_event is called.

    :type sensu_host: str
    :param sensu_host: The IP or Name to connect to for sending the event.
                       Defaults to the yocalhost IP.

    :type component: list
    :param component: Component(s) affected by the event. Good example here would
                      would be to include the service that is being affected or a
                      module of that service such as healthcheck.

    :type description: str
    :param description: Human readable text giving more context on the event. This could
                        include information on what the check means or why was it
                        created.


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
    if not re.match(r'^[\w\.-]+$', name):
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
        'priority': priority,
        'source': source,
        'tags': tags,
        'ttl': human_to_seconds(ttl),
    }
    if irc_channels is not None:
        result_dict['irc_channels'] = irc_channels

    if slack_channels is not None:
        result_dict['slack_channels'] = slack_channels

    if component is not None:
        result_dict['component'] = component

    if description is not None:
        result_dict['description'] = description

    json_hash = json.dumps(result_dict)

    sock = socket.socket()
    try:
        sock.connect((sensu_host, sensu_port))
        sock.sendall(six.b(json_hash) + b'\n')
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

    if status > Status.WARNING:
        status = Status.WARNING

    sensu_dict['status'] = status
    sensu_dict['output'] = output
    send_event(**sensu_dict)

    return 0


if __name__ == '__main__':
    sys.exit(do_command_wrapper())
