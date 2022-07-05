PYTHON_VERSION=3.9.13

default: build

setup:
	./install-dependencies.sh

python-setup:
	pyenv install -v ${PYTHON_VERSION}
	pyenv local ${PYTHON_VERSION}
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
	python -m venv venv
	source venv/bin/activate
	poetry install

serve:
	bundle exec jekyll serve --drafts

build:
	bundle exec jekyll build

deploy:
	gh-pages -d _site