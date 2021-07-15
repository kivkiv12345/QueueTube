""" Holds utility functions for QueueTube """
import builtins
import os
import pickle

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from constants import CREDENTIALS_FILE, SECRETS_FILE, SCOPES


def get_youtube_credentials(suppress_prints=False) -> Credentials:
    """
    Either requests the user for credentials, or retrieves previously saved credentials from pickle file.
    :return: The retrieved credentials.
    """

    # Overrides and suppresses print when suppress_prints is True.
    print = builtins.print if not suppress_prints else (lambda *args, **kwargs: None)

    credentials = None

    # Constant: CREDENTIALS_FILE stores the user's credentials from previously successful logins.
    if os.path.exists(CREDENTIALS_FILE):
        print("Loading credentials from file...")
        with open(CREDENTIALS_FILE, "rb") as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("Refreshing access token...")
            credentials.refresh(Request())
        else:
            print("Fetching new tokens...")

            flow = InstalledAppFlow.from_client_secrets_file(SECRETS_FILE, scopes=SCOPES)
            flow.run_local_server(port=8080, prompt='consent', authorization_prompt_message='')

            credentials = flow.credentials

            # Save the credentials for the next run
            with open(CREDENTIALS_FILE, "wb") as file:
                print("Saving credentials for future use...")
                pickle.dump(credentials, file)

    return credentials
