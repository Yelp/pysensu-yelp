## pysensu-yelp

[![Build Status](https://travis-ci.org/Yelp/pysensu-yelp.svg?branch=master)](https://travis-ci.org/Yelp/pysensu-yelp)

pysensu-yelp is a python library designed for interacting with the
custom Yelp sensu-handlers. 

This allows developers to get notified in the method of their choice,
on arbitrary events that might happen in their code.

Only a very specific type of situation calls for this kind of monitoring,
it does not replace general active checks against webservers and stuff.

See the [docs](http://pysensu-yelp.readthedocs.org/en/latest/) for more
information about the use-cases for this and examples on how to use it.

### Installation

TODO

### Usage

If you need to send an event, use `pysensu_yelp.send_event`:

```python
import pysensu_yelp

result_dict = {
    'check_name': 'my_cool_code',
    'runbook': 'http://lmgtfy.com/?q=my_cool_code',
    'status': 1,
    'output': 'CRITICAL: My code broke! Check the logs!',
    'team': 'backend', 
    'tip': 'This happens sometimes when you frobulate the flux restraint cannon',
    'page': True,
    'notification_email': None,
    'irc_channels': None,
    'slack_channels': None,
    'alert_after': '5m',
    'check_every': '1m',
    'realert_every': -1,
    'ttl': None
}
pysensu_yelp.send_event(**result_dict)
```

### More Docs!

[![Documentation Status](https://readthedocs.org/projects/pysensu-yelp/badge/?version=latest)](https://readthedocs.org/projects/pysensu-yelp/?badge=latest)

Full autogen docs are on [ReadTheDocs](http://pysensu-yelp.readthedocs.org/en/latest/).

### License

Apache 2.

### Contributing

Open an [issue](https://github.com/Yelp/pysensu-yelp/issues) or
[fork](https://github.com/Yelp/pysensu-yelp/fork) and open a
[Pull Request](https://github.com/Yelp/pysensu-yelp/pulls)

Please do not attempt to use `pysensu-yelp` without Yelp's `sensu_handlers`
unless you intend to write your own custom handlers.
