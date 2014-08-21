.PHONY: all docs test tests coverage clean

docs:
	true

test:
	tox

tests: test
coverage: test

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -rf pysensu_yelp.egg-info/
