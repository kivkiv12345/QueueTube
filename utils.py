""" Holds utility functions for QueueTube """

if __name__ == '__main__':
    raise SystemExit(f"Running '{__file__.split('/')[-1]}' directly is unsupported.")

import os
import shutil
import pickle
import builtins
from typing import Any
from subprocess import run, PIPE
from argparse import ArgumentParser

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
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


def move_util(src, dst, *, follow_symlinks=True):
    """
    Copy data and metadata. Remove the original file afterwards.

    Metadata is copied with copystat(). Please see the copystat function
    for more information.

    The destination may be a directory.

    :param follow_symlinks: When False symlinks won't be followed.
        This resembles GNU's "cp -P src dst".
    :return: The file's destination.
    """
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    shutil.copyfile(src, dst, follow_symlinks=follow_symlinks)
    shutil.copystat(src, dst, follow_symlinks=follow_symlinks)
    os.remove(src)
    return dst


class UtilityFunctionClass:
    """ class which contains different utilities potentially relevant for subclasses. """

    def pop(self: object, key: str) -> Any:
        """
        Deletes and returns the specified attribute.
        :param key: The string name of the attribute to delete and return.
        :return: The item found and deleted in self.
        """
        item = getattr(self, key)  # Get the item from self, before we delete it.
        delattr(self, key)  # Delete the item.
        return item  # Return the item post-delete.


class ItemCycler:
    """ Will cycle the items passed to __init__ whenever the 'next_item' property is called. """
    current_item = None
    _cycle_dict = {}

    def __init__(self, items, *args) -> None:
        self.change_items(items, *args)
        super().__init__()

    @property
    def next_item(self) -> Any:
        """ Replaces self.current_item with the next in the series, and returns it thereafter. """
        self.current_item = self._cycle_dict[self.current_item]
        return self.current_item

    def change_items(self, items, *args) -> None:
        """ Replaces the current series of items with the one provided. """
        # Combine items with args.
        items = (list(items) if isinstance(items, (list, tuple, set)) else [items]) + list(args)
        # Check that 'items' are hashable.
        assert not next((True for item in items if not getattr(item, '__hash__')), False), \
            'Provided arguments must be hashable. Ensure that args does not contains lists.'
        # Create a repeatable dict of provided items, and assign a starting item.
        self._cycle_dict = {items[i - 1]: items[i] for i in range(len(items))}
        self.current_item = items[-1]

    def reset(self) -> None:
        """ Useful for resetting the current item in templates. """
        self.current_item = list(self._cycle_dict.keys())[0]
        return ''  # Return an empty string as to prevent templates from writing 'None', whenever reset is called.

    def __setattr__(self, name: str, value: Any) -> None:
        if name == 'current_item' and value not in self._cycle_dict:
            raise ValueError("'current_item' may only be assigned to keys present in the '_cycle_dict' dictionary. "
                             f"These are: {', '.join(self._cycle_dict.keys())}")
        super().__setattr__(name, value)


def add_youtube_dl_arguments(parser: ArgumentParser) -> None:
    """
    Adds the command-line arguments of YouTube-dl to the passed parser.
    :param parser: Argparse ArgumentParse to which arguments should be added.
    """

    # get the help text of YouTube-dl, wherein the arguments reside.
    result = run(['youtube-dl', '--help'], stderr=PIPE, stdout=PIPE)
    stdout = result.stdout.decode()
    raw_arguments = stdout.split('-h, --help                           Print this help text and exit')[1]

    help_lines = ['-' + i for i in raw_arguments.split('\n    -')[1:]]

    SPACING_SEPARATOR = '    '  # YouTube-dl uses multiple spaces to separate the argument from its description.

    cycler = ItemCycler('<', '>')  # '%' must be replaced for argparse to work, as it is recognized as a format character.

    for i in help_lines:
        arg_kwargs = {}
        test4 = i.split(SPACING_SEPARATOR)
        test5 = test4[0].split(', ')
        temp = test5[-1].split()
        if len(temp) > 1:  # Retain the YouTube-dl metavar
            test5[-1] = temp[0]
            arg_kwargs['metavar'] = temp[-1]
        else:  # YouTube-dl arguments that do not specify a metavar should use a sentinel value we may recognize later.
            arg_kwargs['action'] = 'store_const'
            arg_kwargs['const'] = ...

        arg_kwargs['help'] = ''.join(
            [char if char != '%' else cycler.next_item for char in ''.join([i for i in test4[1:] if i]).strip()])

        cycler.reset()

        parser.add_argument(*test5, **arg_kwargs)
