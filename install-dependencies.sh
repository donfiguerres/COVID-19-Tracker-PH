#!/usr/bin/sh

echo 
echo ======================================
echo Installing Jekyll dependencies
echo Note that Jekyll requires ruby to run
echo ======================================
echo
sudo apt install -y ruby-full build-essential zlib1g-dev
sudo gem install jekyll bundler
bundle install
bundle update

echo
echo =============================
echo Installing theme dependencies
echo =============================
echo
sudo apt install -y nodejs npm
sudo npm -g install yarn gh-pages
yarn install --modules-folder ./_assets/yarn
