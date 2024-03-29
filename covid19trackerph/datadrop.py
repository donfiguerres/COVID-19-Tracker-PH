"""
DOH data drop downloader.

The data drop is a bit tricky to pull since there is no fixed URL to pull the
data from. The data drop links are listed in the PDF files that are uploaded
daily by DOH to Google Drive.
This module will download the latest data to the 'data' directory.
"""

import os
import sys
import logging
import pickle
import re
import traceback

import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient import errors
from googleapiclient.http import MediaIoBaseDownload
import PyPDF2


CLIENT_KEY_PATH = "client_secret.json"
TOKEN = "token.pickle"
ACCESS_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
DOH_README_FOLDER_ID = '1ZPPcVU4M7T-dtRyUceb0pMAd8ickYf8o'
README_FILE_NAME = "READ ME FIRST.pdf"
DATA_DIR = "data"


class RemoteFileNotFoundError(Exception):
    """Remote Google Drive file not found"""


class PDFParsingError(Exception):
    """Failed to parse PDF file"""


def build_gdrive_service(credentials_path, token_path, scopes):
    """ This function is derived from the Google Drive API quickstart guide. """
    credentials = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            credentials = pickle.load(token)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, scopes)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(credentials, token)
    return build('drive', 'v3', credentials=credentials)


def get_gdrive_id(url):
    """Get the Google Drive id for the given URL."""
    matches = re.findall(r"[-\w]{25,}", url)
    # We only expect one match from the URL.
    for match in matches:
        return match


def trim_readme_name(name):
    """"Remove date in name for easier tracking in the repo."""
    if '/' in name:
        return re.sub(r" (\(\d+)/(\d+\))", r"", name)
    if '_' in name:
        return re.sub(r" (\(\d+)_(\d+\))", r"", name)
    return name


def trim_data_file_name(name):
    """"Remove date in name for easier tracking in the repo."""
    return re.sub(r"(.*DOH COVID Data Drop_ \d{8} - )", r"", name)


def trim_oddball_file_name(name):
    """"Remove date in name for easier tracking in the repo."""
    return re.sub(r"(.* \d{8} - )", r"", name)


def download_gdrive_file(drive_service, file_id, download_path):
    """Download the Google Drive file for the given file id."""
    request = drive_service.files().get_media(fileId=file_id)
    with open(download_path, 'wb+') as file_handle:
        downloader = MediaIoBaseDownload(file_handle, request)
        done = False
        logging.info("Downloading %s", download_path)
        while done is False:
            status, done = downloader.next_chunk()
            logging.info("Downloading %d%%.", int(status.progress() * 100))


def get_readme_id(drive_service):
    """Get the file id of the READ ME file"""
    results = drive_service.files().list(
        q=("mimeType='application/pdf' and name contains 'READ ME' and"
           f"arents in '{DOH_README_FOLDER_ID}' and trashed = false"),
        fields="nextPageToken, files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True).execute()
    items = results.get('files', [])
    # We expect only one file in the folder.
    if len(items) > 1:
        logging.warning("The READ ME contents have changed.")
    for item in items:
        logging.info("Found file: %s", item['name'])
        return item['id']
    raise RemoteFileNotFoundError("DOH Readme Not Found")


def list_data_files(drive_service, folder_id):
    """Get a list of data files for the given folder id"""
    results = drive_service.files().list(
        q=f"parents in '{folder_id}' and trashed = false",
        fields="nextPageToken, files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True).execute()
    items = results.get('files', [])
    if not items:
        raise RemoteFileNotFoundError(
            f"No files listed in folder ID: {folder_id}")
    while True:
        for item in items:
            logging.info("Found file: %s", item['name'])
            yield item
        if results.get('nextPageToken', None) is None:
            break


def download_data_files(drive_service, folder_id):
    """Download the data files from the given Google Drive folder id"""
    if not os.path.exists(DATA_DIR):
        os.mkdir(DATA_DIR)
    items = list_data_files(drive_service, folder_id)
    # These do not follow the naming convention of the rest of the files.
    oddballs = ["Changelog.xlsx", "DOH Data Drop.xlsx"]
    for item in items:
        item_file_name = item['name']
        if "READ ME" in item_file_name:
            file_name = trim_readme_name(item_file_name)
        elif any(x in item_file_name for x in oddballs):
            file_name = trim_oddball_file_name(item_file_name)
        else:
            file_name = trim_data_file_name(item_file_name)
        download_path = os.path.join(DATA_DIR, file_name)
        try:
            download_gdrive_file(drive_service, item['id'], download_path)
        except errors.HttpError as error:
            if "Changelog" in item_file_name:
                logging.info("Failed to download %s", item_file_name)
            else:
                raise error


def extract_datadrop_link(filename):
    """Extract the data drop link from the given PDF file"""
    pdf = PyPDF2.PdfFileReader(filename)
    for page in range(pdf.numPages):
        logging.debug("Reading PDF page: %s", page)
        pdf_page = pdf.getPage(page)
        page_object = pdf_page.getObject()
        if '/Annots' in page_object.keys():
            annotations = page_object['/Annots']
            for annotation in annotations:
                urls = annotation.getObject()
                if '/URI' in urls['/A'].keys():
                    url = urls['/A']['/URI']
                    logging.debug("URL: %s", url)
                    if "DataDropArchives" not in url and "mailto:" not in url:
                        return url
    raise PDFParsingError(f"Failed to extract datadrop link from {filename}")


def get_full_url(url):
    """Get full URL from the given URL"""
    return requests.head(url).headers['location']


def get_datadrop_url(drive_service):
    """Get the data drop URL"""
    readme_file_id = get_readme_id(drive_service)
    download_gdrive_file(drive_service, readme_file_id, README_FILE_NAME)
    extracted_url = extract_datadrop_link(README_FILE_NAME)
    os.remove(README_FILE_NAME)
    return extracted_url


def download(folder_id=None):
    """Download the data drop files"""
    drive_service = build_gdrive_service(CLIENT_KEY_PATH, TOKEN, ACCESS_SCOPES)
    if not folder_id:
        datadrop_short_url = get_datadrop_url(drive_service)
        datadrop_full_url = get_full_url(datadrop_short_url)
        folder_id = get_gdrive_id(datadrop_full_url)
    download_data_files(drive_service, folder_id)


def main():
    """Main data drop download function"""
    download()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # pylint: disable=broad-except
        logging.error(traceback.format_exc())
        sys.exit(1)
