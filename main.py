""" Main file for QueueTube, this is the file which should be run to download videos and manage the queue. """

import os
import sys
import shutil
from time import time
from os.path import isdir
from getpass import getpass
from subprocess import run, DEVNULL
from datetime import datetime, timedelta
from constants import QUEUE_DIR, INCLUDE_YOUTUBE_DL_ARGS, USERNAME, PASSWORD, CHANNEL_EXCLUDE, DELETE_OLD_VIDEOS, \
    VIDEO_EXTENSIONS, DELETE_DAYS, DOWNLOAD_DAYS, MAX_DOWNLOADS_PER_CHANNEL, KEEPS_DIR

from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource

import argparse
from argparse import ArgumentTypeError
from utils import get_youtube_credentials, add_youtube_dl_arguments, UtilityFunctionClass as UtilFuncCls, move_util

parser = argparse.ArgumentParser(description='Uses the YouTube API and YouTube-dl to download videos of your'
                                             'subscriptions newer than the specified or default date.'
                                             'Also deletes videos older than this date, to conserve space.')

# Specify the arguments the program may receive.
parser.add_argument('--exclude', type=set, metavar='', default=CHANNEL_EXCLUDE,
                    help=f"Set of names of channels to exclude. Defaults to {CHANNEL_EXCLUDE}")
parser.add_argument('--delete_old', type=bool, metavar='', default=DELETE_OLD_VIDEOS,
                    help=f"Whether old videos should be deleted. Defaults to {DELETE_OLD_VIDEOS}")
parser.add_argument('--delete_days', type=int, metavar='', default=DELETE_DAYS,
                    help=f"How long videos may remain in the queue before being deleted. Defaults to {DELETE_DAYS}")
parser.add_argument('--download_days', type=int, metavar='', default=DOWNLOAD_DAYS,
                    help=f"How old channel videos may be and still be downloaded. Defaults to {DOWNLOAD_DAYS}")
parser.add_argument('--save_queue', default=False, action='store_true',
                    help=f"Save current queue to keeps directory (directory default: '{KEEPS_DIR}').")

if INCLUDE_YOUTUBE_DL_ARGS:
    add_youtube_dl_arguments(parser)
else:  # Certain arguments of YouTube-dl should still be included.
    parser.add_argument('-u', '--username', type=str, metavar='USERNAME', default=USERNAME,
                        help=f"Login with this account ID. Defaults to: '{USERNAME}'")
    parser.add_argument('-p', '--password', type=str, metavar='PASSWORD', default=PASSWORD,
                        help=f"Account password. If this option is left out, QueueTube will ask interactively. Defaults to '{PASSWORD}'")

args = parser.parse_args()

# Remove attributes of args, not applicable for YouTube-dl.
CHANNEL_EXCLUDE = UtilFuncCls.pop(args, 'exclude')
DELETE_OLD_VIDEOS = UtilFuncCls.pop(args, 'delete_old')
DELETE_DAYS = UtilFuncCls.pop(args, 'delete_days')
DOWNLOAD_DAYS = UtilFuncCls.pop(args, 'download_days')


if __name__ == '__main__':

    if UtilFuncCls.pop(args, 'save_queue'):  # '--save_queue' was passed on command line. Save queue and exit.
        print(f"Moving queue to '{KEEPS_DIR}' directory...")
        shutil.copytree(QUEUE_DIR, KEEPS_DIR, dirs_exist_ok=True, copy_function=move_util)
        shutil.rmtree(QUEUE_DIR)
        print(f"Finished moving queue to '{KEEPS_DIR}' directory.")
        sys.exit(0)  # Early exit when using this mode.

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
    download_date = (datetime.today() - timedelta(days=DOWNLOAD_DAYS)).strftime('%Y%m%d')

    for channel_name, subscription in subscriptions.items():

        _new_directory = False

        # Create and enter a channel specific directory.
        if not isdir(currdir := f"{channel_name}/"):
            os.mkdir(currdir)
            _new_directory = True
        os.chdir(currdir)

        if not _new_directory and DELETE_OLD_VIDEOS and (dir_contents := os.listdir()):  # Skip deleting videos in directories we just made ourselves.
            print(f"[QueueTube]: Now deleting old videos for {channel_name}...")
            for video in dir_contents:
                if next((True for extension in VIDEO_EXTENSIONS if video.endswith(extension)), False) and \
                        time() > os.path.getmtime(video) + 86400 * DOWNLOAD_DAYS:  # 86400 = 1 day in seconds.
                    print(f"[QueueTube] Deleting video: '{video}'...")
                    os.remove(video)

        print(f"[QueueTube]: Now downloading videos for {channel_name}...")

        youtube_dl_kwargs = ['--dateafter', download_date, '--playlist-end', str(MAX_DOWNLOADS_PER_CHANNEL)] + \
        [item for sublist in  # Listcomp to iterate over the args namespace, filters out None arguments (default values). Also handles 'store_true'-like arguments.
         [([f"--{key}"] if value is ... else [f"--{key}", value]) for key, value in args.__dict__.items() if
          value is not None] for item in sublist]

        # Download specified videos for the current channel.
        run(['youtube-dl',
             f"https://www.youtube.com/channel/{subscription['snippet']['resourceId']['channelId']}/videos",
             ] + youtube_dl_kwargs)

        os.chdir('../')  # Go back to the queue directory.

    print('[QueueTube]: All done')
