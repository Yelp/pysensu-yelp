.PHONY: all production docs test tests coverage clean

all: production

production:
	@true

docs:
	tox -e docs

test:
	tox

tests: test
coverage: test

clean:
	rm -rf docs/build/*
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete