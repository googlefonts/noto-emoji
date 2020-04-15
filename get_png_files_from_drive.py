#!/usr/bin/env python3

from __future__ import print_function
import pickle
from os import path, makedirs
import io
import fire
import sys
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/drive"]


def main(folder_name, output_dir):

    # Create a token.pickle file to store the users session
    service = get_service()

    # Get the folder instance
    folder_id = get_folder_id(service, folder_name)

    # Create output_dir
    output_dir = create_dir(output_dir)

    # Get the file IDs
    file_list = get_file_list(service, folder_id)

    # Download the files from the drive and put them in the output_dir
    download_files(service, file_list, output_dir)


def get_service():

    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    creds = None
    if path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not path.exists("credentials.json"):
                print("""
                      Your missing 'credentials.json'.
                      Please get this file here:
                      https://developers.google.com/drive/api/v3/quickstart/python
                      and include it in the root of your project.
                      """)
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("drive", "v3", credentials=creds)

    return service


def get_folder_id(service, folder_name):
    folder = service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
            fields='files(id, name, parents)').execute()

    total = len(folder['files'])

    if total != 1:
        print(f'{total} folders found, needs exately one')
        sys.exit(1)

    else:
        folder_id = folder['files'][0]['id']

    return folder_id


def create_dir(dir_name):
    if not path.exists(dir_name):
        makedirs(dir_name)

    return dir_name


def get_file_list(service, folder_id):

    result = []
    page_token = None
    while True:
        files = service.files().list(
                q=f"'{folder_id}' in parents",
                fields='nextPageToken, files(id, name, mimeType)',
                pageToken=page_token,
                pageSize=1000).execute()

        result.extend(files['files'])

        page_token = files.get("nextPageToken")

        if not page_token:
            break
    return result


def download_files(service, file_list, output_dir):

    print("Downloading files")
    for file in file_list:
        file_id = file['id']
        filename = file['name']

        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        filelocation = f"./{output_dir}/{filename}"
        with open(filelocation, "wb") as f:
            f.write(fh.getbuffer())

        print(f"Downloading: {filename} ({file_id})")
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        filelocation = f"downloaded_pngs/{filename}"
        with open(filelocation, "wb") as f:
            f.write(fh.getbuffer())


if __name__ == "__main__":
    fire.Fire()
