# COVID-19 Tracker Philippines

![actions workflow](https://github.com/donfiguerres/COVID-19-Tracker-PH/actions/workflows/ci.yml/badge.svg)

This serves as a supplementary tracker for the
[COVID-19 Tracker](https://www.doh.gov.ph/covid19tracker) maintained by the
[Department of Health](https://www.doh.gov.ph/). The data set used in this
tracker are pulled from DOH's
[data drop](https://drive.google.com/drive/folders/1ZPPcVU4M7T-dtRyUceb0pMAd8ickYf8o).

This project started as a report generator initially to track the dalays between
testing and confirmation/reporting but evolved into a tracking and reports page
where I've experimented with Python tools, frontend frameworks, and CI/CD
workflows.

In its current form, it is a static report generator using the DOH Data Drop as
a data source.

**Disclaimer: I am not affiliated with the DOH or any government agency. This is
my own personal project.**

## Requirements

> _**NOTE**_ This project runs best in Linux and MacOS. You might run into
problems that are not documented here if you try running it in Windows. It is
recommended to use WSL instead if you're on a Windows machine since it is my
current development setup.

### install-dependencies script

Run the `setup` make target to install the needed Ruby and NPM packages for
building the site.

```bash
make setup
```

In its current form, it runs the `install-dependencies.sh` script which installs
the dependency packages. However, this is written for Ubuntu which uses the apt
package manager. If you're on a different platform, please consider updating the
the script to accomodate your specific environment. I'll be happy to merge your
pull request if you submit one.

### Python

Python can be installed from [python.org](https://www.python.org/). If you're
setting up your project on a then most probably it already has Python installed.

There are also several ways to setup a Python development environment but I have
created a script for it for my typical development environment setup which is
pyenv + Poetry. For those who are using Ubuntu (or WSL Ubuntu), you can run the
`setup-python` make target.

```bash
make setup-python
```

This target executes the `setup-python.sh` script which installs pyenv and
Poetry. If you prefer a different method of creating your virtual environments
then you may do so. The required packages are listed in the `pyproject.toml`
file.

### Hardware Requirements

Due to the amount of data that's available in the Data Drop, you will need
around 10GB of RAM to run the update-tracker.py script on an 8-core machine.
If you only have ~8GB of physical RAM, consider increasing your swap partition
(if in Linux).

If you're on WSL, you can set your memory through the `.wslconfig` or
`wsl.config` files. The configuration settings are documented
[here](https://docs.microsoft.com/en-us/windows/wsl/wsl-config).

```conf
[wsl2]
memory=12GB
swap=10GB
```

## Overview

The update-tracker.py script downloads the data from the
[DOH Data Drop](https://drive.google.com/drive/folders/1ZPPcVU4M7T-dtRyUceb0pMAd8ickYf8o)
and generates the charts used in the
[COVID-19 Tracker PH](https://donfiguerres.github.io/COVID-19-Tracker-PH/tracker)
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
`client_secret.json`.

### Open the Files in the DOH Data Drop Google Drive Folder

Open README file in the [DOH folder](https://drive.google.com/drive/folders/1ZPPcVU4M7T-dtRyUceb0pMAd8ickYf8o).
This link is also available at the
[DOH Covid19 Tracker](https://ncovtracker.doh.gov.ph/).

The README file will have a link to the latest Data Drop folder at the last
page. Click on that link to open the latest Data Drop folder.

Open all of the files in the Data Drop Folder.

You need to do this step due to a limitation in the Google Drive API. See
[Limitations](#limitations) below.

### Running the Script

Navigate to your project directory then run the `updatetracker` script.

> _**NOTE**_ Make sure that the `covid19trackerph` project package has been
installed in your virtual environment before running the script.

```bash
updatetracker
```

### Errors

Sometimes, the link in the PDF file is not annotated - meaning it is only a text
and not a link - so PyPDF2 will not be able to find it. To get around that, you
can use the --folder-id option of the script.

```bash
updatetracker --folder-id=<folder-id-of-latest-datadrop>

# example
updatetracker --folder-id=12l_bfB_wuQ8wrauCbesKURswRJFl-ih_
```

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
* Migrate to [Next.js](https://nextjs.org/).

## Limitations

You need to open each of the new files in the DOH datadrop before the script can
download the Google Drive files for you. This is because the files need to be
either explicitly shared to your account or need to be opened first in order
for them to be listed in your Drive. See this
[Stackoverflow question](https://stackoverflow.com/questions/62414423/google-drive-api-list-files-in-a-shared-folder-that-are-i-have-not-accessed-ye).

## Other Useful Trackers

* [covid19stats.ph](https://covid19stats.ph/)
* [covid19ph](https://covid19ph.com/)
* [Baguio Covid19 Tracker](http://endcov19.baguio.gov.ph/)
* [Our World in Data](https://ourworldindata.org/coronavirus-data-explorer)
