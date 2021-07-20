"""
Holds constant values for QueueTube.
Values may be changed to match user desire.
"""

if __name__ == '__main__':
    raise SystemExit(f"Running '{__file__.split('/')[-1]}' directly is unsupported.")

from typing import Union
null, true, false = None, True, False  # Provide non-Python-savvy users some alternatives.

QUEUE_DIR:                  str         = 'queue/'  # In which directory should queue videos be placed.
KEEPS_DIR:                  str         = 'queue/'  # In which directory should videos be kept.
INCLUDE_YOUTUBE_DL_ARGS:    bool        = False  # Should the program accept all the arguments YouTube-dl does.
CHANNEL_EXCLUDE = {
    #'CreepsMcPasta'  # First video is a quite large compilation.
}
DELETE_OLD_VIDEOS:          bool    = True  # Whether to delete old videos.
DELETE_DAYS:                int     = 7  # Amount of days a video may be located in the queue before being deleted.
DOWNLOAD_DAYS:              int     = 7  # How old a video may be in days, and still be downloaded.
MAX_DOWNLOADS_PER_CHANNEL:  int     = DOWNLOAD_DAYS * 3  # YouTube-dl will check every channel video if not specified,
                                                    # which takes a long time for channels with a large back catalog.
                                                    # Current setting assumes 3 videos per day.

# Default username and password. <ENTERING A DEFAULT PASSWORD IS NOT SECURE>
# The program will ask for the password if a username is specified when a password isn't.
USERNAME:       Union[str, None]        = None
PASSWORD:       Union[str, None]        = None

# YouTube API configs (less relevant for end users)
SECRETS_FILE:               str         = "client_secrets.json"
CREDENTIALS_FILE:           str         = 'token.pickle'
SCOPES:                     list[str]   = ['https://www.googleapis.com/auth/youtube.readonly']

VIDEO_EXTENSIONS = {'.mp4', '.part', '.ytdl'}  # File extensions for old video files that may be deleted.
