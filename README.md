# COVID-19 Tracker Philippines


This serves as a supplementary tracker for the
[COVID-19 Tracker](https://www.doh.gov.ph/covid19tracker) maintained by the
[Department of Health](https://www.doh.gov.ph/). The data set used in this
tracker are pulled from DOH's
[data drop](https://drive.google.com/drive/folders/1ZPPcVU4M7T-dtRyUceb0pMAd8ickYf8o).

In its current form, this project is actually a static report generator using 
the DOH Data Drop as a data source.

**Disclaimer: I am not affiliated with the DOH or any government agency. This is my own personal project.**


## Requirements
### Python
* google-api-client
* google-auth-oauthlib
* pypdf2
* pandas
* numpy
* plotly

### Ruby
* bundle
* gems
* jekyll

### Node.js
* npm

### Hardware
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
* Refactor to use functional programming principles to make it more readable.
* Modify gh-pages commit script to fit into the current setup.
* git repo cleanup
* Faster loading time


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
