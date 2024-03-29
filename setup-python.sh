#!/usr/bin/sh

PYTHON_VERSION=$1

if [ -z "${PYTHON_VERSION}" ]
then
    echo You must provide the Python version as argument.
    exit 1
fi

if ! command -v pyenv 2>&1 > /dev/null
then
    echo 
    echo ================
    echo Installing pyenv
    echo ================
    echo
    sudo apt update
    sudo apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
        libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev \
        xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
    curl https://pyenv.run | bash
    # Appending the needed commands to .bashrc so you don't have to do it manually
    echo '# PYENV' >> ~/.profile
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile
    echo 'eval "$(pyenv init -)"' >> ~/.profile
    echo '' >> ~/.profile
    # Loading pyenv so we can install the needed Python version
    export PYENV_ROOT="$HOME/.pyenv"
    command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    # Installing the needed Python version
	pyenv install -v ${PYTHON_VERSION}
    pyenv global ${PYTHON_VERSION}
	pyenv local ${PYTHON_VERSION}
fi

if ! command -v poetry 2>&1 > /dev/null
then
    echo 
    echo =================
    echo Installing poetry 
    echo =================
    echo
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
    . $HOME/.poetry/env
fi

echo
echo ==============================
echo Installing Python dependencies
echo ==============================
echo 
poetry install

echo
echo REMINDER: You still need to activate the virtual environment in your \
 current shell.
echo You can activate it by executing \'poetry shell\'.
