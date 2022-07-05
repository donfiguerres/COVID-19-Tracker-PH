# COVID-19 Tracker Philippines

![example workflow](https://github.com/donfiguerres/COVID-19-Tracker-PH/actions/workflows/ci.yml/badge.svg)

This serves as a supplementary tracker for the
[COVID-19 Tracker](https://www.doh.gov.ph/covid19tracker) maintained by the
[Department of Health](https://www.doh.gov.ph/). The data set used in this
tracker are pulled from DOH's
[data drop](https://drive.google.com/drive/folders/1ZPPcVU4M7T-dtRyUceb0pMAd8ickYf8o).

In its current form, this project is actually a static report generator using 
the DOH Data Drop as a data source.

**Disclaimer: I am not affiliated with the DOH or any government agency. This is my own personal project.**


## Requirements

> ___NOTE___ This project runs best in Linux and MacOS. You might run into
problems that are not documented here if you try running it in Windows. It is
recommended to use WSL instead if you're on a Windows machine since it is my
current development setup.

### install-dependencies script

Run the dependency installation script below to install the needed Ruby and
NPM packages for building the site.

```bash
./install-dependencies.sh
```

### Python
Python can be installed from [python.org](https://www.python.org/). If you're
setting up your project on a then most probably it already has Python installed.


There are also several ways to setup a Python development environment which is
why I didn't create a script for it. Some people may have a personal preference
in setting up their development environments. I have listed below steps that
beginners can follow to setup their development environments. For more advanced,
developers, you can use whatever workflow you like. However, make sure to
install __Poetry__ for the dependency management.

#### pyenv

pyenv is a recommended way to manage multiple python versions and virtual
environments. You will need this to avoid changing your OS-installed Python
version. You may follow the steps below to install pyenv in a Linux distro.
If the steps below do not work, follow the installation instructions for your OS
or distro in the [pyenv GitHub page](https://github.com/pyenv/pyenv).

```bash
curl https://pyenv.run | bash
```

Once you have it installed, install python version 3.9.13.

```bash
pyenv install -v 3.9.13
```

Set 3.9.13 as the project's Python version.

```bash
pyenv local 3.9.13
```

#### Poetry

Poetry is used for dependency managemant.

```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```

You can see [https://python-poetry.org/](https://python-poetry.org/) for more info.

Once you have Poetry installed, create a virtual environment.

```bash
python -m venv venv
```

Then activate the virtual environment.

```bash
source venv/bin/activate
```

To install the Python dependencies using Poetry, run the command below.

```bash
poetry install
```

See [pyproject.toml](./pyproject.toml) for the list of dependencies in this
project.


### Hardware Requirements
Due to the amount of data that's available in the Data Drop, you will need
around 10GB of RAM to run the update-tracker.py script. If you only have ~8GB
of physical RAM, consider increasing your swap partition (if in Linux) or
virtual memory (if in Windows).

## Overview
The update-tracker.py script downloads the data from the [DOH Data Drop](https://drive.google.com/drive/folders/1ZPPcVU4M7T-dtRyUceb0pMAd8ickYf8o)
and generates the charts used in the [COVID-19 Tracker PH](https://donfiguerres.github.io/COVID-19-Tracker-PH/tracker)
page.

Go to [tracker](https://donfiguerres.github.io/COVID-19-Tracker-PH/tracker)

## How to Run
### Create a Client Secret
Create and download a OAth 2.0 client secret from the
[Google APIs site](https://console.developers.google.com/).
Follow the
[Quickstart Guide](https://developers.google.com/drive/api/v3/quickstart/python)
to understand how the API works and follow the
[Enable the Google Drive API Guide](https://developers.google.com/drive/api/v3/enable-drive-api)
to create your client secret file.

Copy the client secret file to your project directory and rename the file as
'client_secret.json'

### Open the Files in the DOH Data Drop Google Drive Folder
Open README file in the [DOH folder](https://drive.google.com/drive/folders/1ZPPcVU4M7T-dtRyUceb0pMAd8ickYf8o).
This link is also available at the [DOH Covid19 Tracker](https://ncovtracker.doh.gov.ph/).

The README file will have a link to the latest Data Drop folder at the last page. Click on that link to open the latest Data Drop folder.

Open all of the files in the Data Drop Folder.

You need to do this step due to a limitation in the Google Drive API. See [Limitations](#limitations)
below.

### Running the Script
Navigate to your project directory then run the 'update-tracker.py' script.

    cd /path/to/COVID-19-Tracker-PH
    python update-tracker.py

### Errors
Sometimes, the link in the PDF file is not annotated - meaning it is only a text
and not a link - so PyPDF2 will not be able to find it. To get around that, you
can use the --folder-id option of the script.

    python update-tracker.py --folder-id=<folder-id-of-latest-datadrop>
    # example
    python update-tracker.py --folder-id=12l_bfB_wuQ8wrauCbesKURswRJFl-ih_

## TODOs
### Plots
* Testing ang Confirmation Gap
* Death and Recovery Reporting
* Recovery Time
* Period from Infection to Death (what's the proper term for this?)
* R0 and projection
* Per region and city/municipality pages
* Hospital daily report - occupancy
* Hospital weekly report - PPE inventory
* Quarantine facility reports

### Theme
* Organize post tags.
* Create own icon.
* Change about image.
* Migrate to Hugo.

### Others
* git repo cleanup


## Limitations
You need to open each of the new files in the DOH datadrop before the script can
download the Google Drive files for you. This is because the files need to be
either explicitly shared to your account or need to be opened first in order
for them to be listed in your Drive. See this [Stackoverflow question](https://stackoverflow.com/questions/62414423/google-drive-api-list-files-in-a-shared-folder-that-are-i-have-not-accessed-ye).

## Other Useful Trackers
* [covid19stats.ph](https://covid19stats.ph/)
* [covid19ph](https://covid19ph.com/)
* [Baguio Covid19 Tracker](http://endcov19.baguio.gov.ph/)
* [Our World in Data](https://ourworldindata.org/coronavirus-data-explorer)
