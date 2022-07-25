PYTHON_VERSION=3.9.13

.PHONY: default build setup serve build deploy setup-python update-charts test \
	lint lint-src lint-test

default: build

setup:
	./install-dependencies.sh

serve:
	bundle exec jekyll serve --drafts

build:
	bundle exec jekyll build

deploy:
	gh-pages -d _site


# Analytics

setup-python:
	./setup-python.sh ${PYTHON_VERSION}

# Skipping downloads here for the meantime due to errors in reading the
# Data Drop PDF files.
update-charts:
	updatetracker --skip-download

test:
	pytest tests

lint: lint-src lint-test

lint-src:
	pylint covid19trackerph --fail-under=7.5

lint-test:
	pylint tests --fail-under=8.5
