PYTHON_VERSION=3.9.13

.PHONY: default build setup python-setup serve build deploy

default: build

setup:
	./install-dependencies.sh

setup-python:
	./setup-python.sh ${PYTHON_VERSION}

serve:
	bundle exec jekyll serve --drafts

build: update-charts
	bundle exec jekyll build

# Skipping downloads here for the meantime due to errors in reading the
# Data Drop PDF files.
update-charts:
	python update-tracker.py --skip-download

test:
	pytest tests

lint:
	pylint *.py

deploy:
	gh-pages -d _site
