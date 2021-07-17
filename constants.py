"""
Holds constant values for QueueTube.
Values may be changed to match user desire.
"""

if __name__ == '__main__':
    raise SystemExit(f"Running '{__file__.split('/')[-1]}' directly is unsupported.")

from typing import Union
null, true, false = None, True, False

QUEUE_DIR:                  str         = 'queue/'  # In which directory should queue videos be placed.
INCLUDE_YOUTUBE_DL_ARGS:    bool        = False  # Should the program accept all the arguments YouTube-dl does.
CHANNEL_EXCLUDE = {
    'CreepsMcPasta'  # First video is a quite large compilation.
}

# Default username and password. <ENTERING A DEFAULT PASSWORD IS NOT SECURE>
# The program will ask for the password if a username is specified when a password isn't.
USERNAME:       Union[str, None]        = None
PASSWORD:       Union[str, None]        = None

# YouTube API configs (less relevant for end users)
SECRETS_FILE:               str         = "client_secrets.json"
CREDENTIALS_FILE:           str         = 'token.pickle'
SCOPES:                     list[str]   = ['https://www.googleapis.com/auth/youtube.readonly']
