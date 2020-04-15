#!/usr/bin/env python3

from __future__ import print_function
import pickle
import os.path
import io
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/drive"]


def main(folder_name, output_dir):
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """

    # Create a token.pickle file to store the users session
    service = get_service()

    # Get the folder instance
    folder = get_folder_id(service, folder_name)

    # Create output dir
    output_dir = create_dir("downloaded_png")



    # Call the Drive v3 API
    results = (
        service.files()
        .list(
            pageSize=1000,
            fields="nextPageToken, files(id, name)",
            q=f"'{folder_id}' in parents",
        )
        .execute()
    )
    items = results.get("files", [])

    if not items:
        print("No files found.")
    else:
        print("Downloading files")
        for item in items:
            print("Downloading: {0} ({1})".format(item["name"], item["id"]))
            file_id = item["id"]
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()

            filelocation = f"downloaded_pngs/{item['name']}"
            with open(filelocation, "wb") as f:
                f.write(fh.getbuffer())


def get_service():

    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
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
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    folder = os.path(dir_name)

    return folder



def download_files():
    



if __name__ == "__main__":
    main()
