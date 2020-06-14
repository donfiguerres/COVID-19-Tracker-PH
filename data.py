"""
DOH data drop scraper

The data drop is a bit hard to pull since there is no fixed URL to pull the data
from. The data drop links are listed in the PDF files that are uploaded daily by
DOH to Google Drive.
This module will dowload the latest data to the 'data' directory if ran as a
script.
"""

import os
import sys
import logging
import traceback
import io

import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient import errors
from googleapiclient.http import MediaIoBaseDownload


README_FILE_NAME = "READ ME FIRST.pdf"

class RemoteFileNotFoundError(Exception):
    pass

class PDFParsingError(Exception):
    pass


def build_gdrive_service():
    """ This function is derived from the Google Drive API quickstart guide. """
    creds = None
    CREDENTIALS_FILE_PATH = "credentials.json"
    TOKEN_FILE_PATH = "token.pickle"
    GDRIVE_SCOPES = ['https://www.googleapis.com/auth/drive']
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE_PATH):
        with open(TOKEN_FILE_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                                CREDENTIALS_FILE_PATH, GDRIVE_SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_FILE_PATH, 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

def download_gdrive_file(drive_service, file_id):
    request = drive_service.files().get_media(fileId=file_id)
    fh = open(README_FILE_NAME, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        logging.info("Download %d%%." % int(status.progress() * 100))

def get_readme_id(drive_service):
    DOH_README_FOLDER_ID = '1ZPPcVU4M7T-dtRyUceb0pMAd8ickYf8o'
    results = drive_service.files().list(
                q=f"mimeType='application/pdf' and name contains 'READ ME' and parents in '{DOH_README_FOLDER_ID}' and trashed = false",
                fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    # We expect only one file in the folder.
    if len(items) > 1:
        logging.warning("The READ ME contents have changed.")
    for item in items:
        logging.info(f"Found file: {item['name']}")
        return item['id']
    raise RemoteFileNotFoundError("DOH Readme Not Found")


def extract_datadrop_link(filename):
    import PyPDF2
    pdf = PyPDF2.PdfFileReader(filename)
    for page in range(pdf.numPages):
        logging.debug(f"Reading PDF page: {page}")
        pdfPage = pdf.getPage(page)
        pageObject = pdfPage.getObject()
        if '/Annots' in pageObject.keys():
            ann = pageObject['/Annots']
            for a in ann:
                u = a.getObject()
                if '/URI' in u['/A'].keys():
                    url = u['/A']['/URI']
                    logging.debug(f"URL: {url}")
                    if "DataDropArchives" not in url and "mailto:" not in url:
                        return url
    raise PDFParsingError(f"Failed to extract datadrop link from {filename}")


def main():
    drive_service = build_gdrive_service()
    readme_file_id = get_readme_id(drive_service)
    download_gdrive_file(drive_service, readme_file_id)
    extracted_url = extract_datadrop_link(README_FILE_NAME)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        logging.error(traceback.format_exc())
        sys.exit(1)