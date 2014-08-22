.PHONY: all docs test tests coverage clean

docs:
	mkdir -p docs/build/
	cp -a .docs_redirect docs/build/html

test:
	tox -e py26

tests: test
coverage: test

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -rf pysensu_yelp.egg-info/
