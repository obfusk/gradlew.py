SHELL   := /bin/bash
PYTHON  ?= python3

export PYTHONWARNINGS := default

.PHONY: all update_gradle_versions test doctest lint clean cleanup

all: update_gradle_versions

update_gradle_versions:
	$(PYTHON) -c $$'import gradlew\ngradlew.update_gradle_versions(verbose=True)'

test: doctest lint

doctest:
	$(PYTHON) -m doctest *.py

lint:
	flake8 *.py
	pylint *.py
	mypy --strict --disallow-any-unimported *.py

clean: cleanup

cleanup:
	find -name '*~' -delete -print
	rm -fr __pycache__/ .mypy_cache/
