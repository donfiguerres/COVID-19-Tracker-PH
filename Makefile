PYTHON_VERSION=3.9.13

.PHONY: default build setup python-setup serve build deploy

default: build

setup:
	./install-dependencies.sh

setup-python:
	./setup-python.sh ${PYTHON_VERSION}

serve:
	bundle exec jekyll serve --drafts

build:
	bundle exec jekyll build

deploy:
	gh-pages -d _site