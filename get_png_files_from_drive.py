#!/usr/bin/env python3

# Copyright 2020 Google, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License

from __future__ import print_function
import pickle
from os import path, makedirs, walk, listdir
import io
import fire
import sys
import shutil
from distutils.dir_util import copy_tree
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/drive"]


def main(folder_name="", reporting=False):

    # Remove combined_png dir if it exists
    if path.exists("./build/combined_png"):
        shutil.rmtree("./build/combined_png")

    # Create a token.pickle file to store the users session
    service = get_service()

    if folder_name == "":
        folder_name = input("Please enter the name of your drive folder: ")

    # Get the folder instance
    folder_id = get_folder_id(service, folder_name)

    # Create output_dir
    output_dir = create_dir("temp_download_folder")

    # Get the file IDs
    file_list = get_file_list(service, folder_id)

    # Download the files from the drive and put them in the output_dir
    download_files(service, file_list, output_dir)

    if reporting:
        # Generate a report on the downloaded files
        report_on_download(output_dir)

    # Create a combined PNG dir. Files in the png dir are the default
    merge_png_dirs(output_dir)


def get_service():
    """Autenticate yourself and create a token.pickle to use the google apiclient"""

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
                print("You are missing 'credentials.json'. "
                      "Please get this file here: "
                      "https://developers.google.com/drive/api/v3/quickstart/python "
                      "and include it in the root of your project.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("drive", "v3", credentials=creds)

    return service


def get_folder_id(service, folder_name):
    """Get the folder id instead of the folder name."""
    folder = service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
            fields='files(id, name, parents)').execute()

    total = len(folder['files'])

    if total != 1:
        print(f'{total} folders found, needs exactly one')
        sys.exit(1)

    else:
        folder_id = folder['files'][0]['id']

    return folder_id


def create_dir(dir_name):
    """Create dir if it does not yet exist."""
    if not path.exists(dir_name):
        makedirs(dir_name)

    return dir_name


def get_file_list(service, folder_id):
    """Get all files in the Google drive folder."""
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
    """Download all the files in the file_list."""

    print("Downloading files")
    for file in file_list:
        file_id = file['id']
        filename = file['name']

        if "emoji_u" in filename and ".png" in filename:

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

            filelocation = f"{output_dir}/{filename}"
            with open(filelocation, "wb") as f:
                f.write(fh.getbuffer())

        else:
            print(f"{filename} does not have a valid emoji name")


def report_on_download(output_dir):
    """Summarize the process and print findings."""
    path, dirs, files = next(walk("./png/128"))

    out_path, out_dirs, out_files = next(walk(output_dir))
    downloaded_file_count = len(out_files)

    overlap_count = 0
    new_file_count = 0
    for file in out_files:
        if file in files:
            overlap_count += 1
        else:
            new_file_count += 1

    print(f"Imported {downloaded_file_count} files,"
          f" of which {new_file_count} are new, and {overlap_count}"
          " will be used instead of local files.")


def merge_png_dirs(output_dir):
    """Combine local and downloaded PNGs."""

    copy_tree("./png/128", "./build/combined_png")
    src_files = listdir(output_dir)
    for file_name in src_files:
        full_file_name = path.join(output_dir, file_name)
        if path.isfile(full_file_name):
            shutil.copy(full_file_name, "./build/combined_png")
    shutil.rmtree(output_dir)


if __name__ == "__main__":
    fire.Fire(main)
