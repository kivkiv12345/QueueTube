""" Main file for QueueTube, this is the file which should be run to download videos and manage the queue. """

import os
from typing import Union
from os.path import isdir
from getpass import getpass
from subprocess import run, PIPE, DEVNULL
from datetime import datetime, timedelta
from constants import QUEUE_DIR, INCLUDE_YOUTUBE_DL_ARGS, USERNAME, PASSWORD, CHANNEL_EXCLUDE

from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource

import argparse
from argparse import ArgumentTypeError
from utils import get_youtube_credentials, add_youtube_dl_arguments

parser = argparse.ArgumentParser(description='Uses the YouTube API and YouTube-dl to download videos of your'
                                             'subscriptions newer than the specified or default date.'
                                             'Also deletes videos older than this date, to conserve space.')

# Specify the arguments the program may receive.
parser.add_argument('--exclude', type=set, metavar='', default=CHANNEL_EXCLUDE,
                    help=f"Set of names of channels to exclude. Defaults to {CHANNEL_EXCLUDE}")

if INCLUDE_YOUTUBE_DL_ARGS:
    add_youtube_dl_arguments(parser)
else:  # Certain arguments of YouTube-dl should still be included.
    parser.add_argument('-u', '--username', type=str, metavar='USERNAME', default=USERNAME,
                        help=f"Login with this account ID. Defaults to: '{USERNAME}'")
    parser.add_argument('-p', '--password', type=str, metavar='PASSWORD', default=PASSWORD,
                        help=f"Account password. If this option is left out, QueueTube may ask interactively. Defaults to '{PASSWORD}'")

args = parser.parse_args()

# Remove attributes of args, not applicable for YouTube-dl.
CHANNEL_EXCLUDE = args.exclude
del args.exclude


if __name__ == '__main__':

    if args.username and not args.password:  # Prompt the user for a password when a username is specified without a password.
        args.password = PASSWORD = getpass()

    try:  # Run youtube-dl command, to check whether it is installed.
        run(['youtube-dl', ], stderr=DEVNULL, stdout=DEVNULL)
    except FileNotFoundError as e:  # Raises FileNotFoundError, when not installed.
        print(f"Youtube-dl does not appear to be installed\n{e}")
        raise SystemExit("Quitting program, due to missing requirement.")

    youtube = build("youtube", "v3", credentials=get_youtube_credentials())

    page_token = None  # Page token should be None for the first iteration, to get the first page.
    subscriptions = {}  # Dictionary for holding channel names and their summary.

    # Construct the dictionary of subscriptions by continuously querying the next page,
    # until the current page lacks a next page token (last page).
    while (page_token := (response := youtube.subscriptions().list(
            part="snippet",  # snippet = a summary of the subscription and the corresponding channel
            mine=True,
            maxResults=50,
            pageToken=page_token,
    ).execute()).get('nextPageToken')):

        # Merge channels of the current page into the dictionary of all subscriptions.
        subscriptions |= {sub['snippet']['title']: sub for sub in response['items'] if
                          sub['snippet']['title'] not in CHANNEL_EXCLUDE}

    # Create and enter the video queue directory.
    if not isdir(QUEUE_DIR):
        os.mkdir(QUEUE_DIR)
    os.chdir(QUEUE_DIR)

    # Videos must be newer than this date to be downloaded.
    download_date = (datetime.today() - timedelta(weeks=1)).strftime('%Y%m%d')

    for channel_name, subscription in subscriptions.items():

        print(f"[QueueTube]: Now downloading videos for {channel_name}...")

        # Create and enter a channel specific directory.
        if not isdir(currdir := f"{channel_name}/"):
            os.mkdir(currdir)
        os.chdir(currdir)

        # Download specified videos for the current channel.
        run(['youtube-dl',
             f"https://www.youtube.com/channel/{subscription['snippet']['resourceId']['channelId']}/videos",
             '--dateafter', download_date, '--playlist-end', '15'])

        os.chdir('../')  # Go back to the queue directory.

    print('All done')
