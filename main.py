

from subprocess import run, PIPE
from googleapiclient.discovery import build, Resource
from google.auth.transport.requests import Request
from utils import get_youtube_credentials


if __name__ == '__main__':

    try:  # Run youtube-dl command, to check whether it is installed.
        command = run(['youtube-dl', ], stdout=PIPE, stderr=PIPE)
    except FileNotFoundError as e:  # Apparently raises FileNotFoundError, when not installed.
        print(f"Youtube-dl does not appear to be installed\n{e}")
        raise SystemExit("Quitting program, due to missing requirement.")

    youtube = build("youtube", "v3", credentials=get_youtube_credentials())

    subscriptions = []
    subscriptions_set = set()

    page_token = None

    while (response := youtube.subscriptions().list(
        part="snippet",
        mine=True,
        maxResults=50,
        pageToken=page_token,
    ).execute()).get('nextPageToken'):

        print(response['nextPageToken'])

        # Query the next page for the next iteration.
        page_token = response['nextPageToken']

        subscriptions += [i for i in response['items']]
        subscriptions_set.update(i['snippet']['title'] for i in response['items'])

        dupecheck = subscriptions[0]['snippet']['title']
        dupetuple = tuple(i for i in subscriptions[1:] if i['snippet']['title'] == dupecheck)
        print(dupecount := len(dupetuple))

    print(response)
    print(subscriptions)
