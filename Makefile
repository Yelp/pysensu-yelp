.PHONY: all docs test tests coverage clean

docs:
	mkdir -p docs/build/
	cp -a .docs_redirect docs/build/html

install-hooks:
	tox -e pre-commit

test:
	tox

tests: test
coverage: test

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -rf pysensu_yelp.egg-info/

package: clean
	python setup.py sdist bdist_wheel

upload:
	python setup.py sdist upload
