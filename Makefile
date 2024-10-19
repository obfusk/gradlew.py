SHELL := /bin/bash

.PHONY: all

all:
	python3 -c $$'import gradlew\ngradlew.update_gradle_versions(verbose=True)'
