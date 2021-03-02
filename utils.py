from typing import List

import re


def _find_all_usernames(string: str) -> List[str]:
    """
    Returns list of all usernames in format ["@username1", "@username2", ...]
    Credit to https://stackoverflow.com/a/63308482/6233648
    """
    tg_nick_pattern = r'.*\B@(?=\w{5,64}\b)[a-zA-Z0-9]+(?:_[a-zA-Z0-9]+)*.*'
    return re.findall(tg_nick_pattern, string)


def extract_usernames_from_args(arguments: List[str]) -> List[str]:
    """Returns list of usernames extracted from command arguments."""
    return [
        # take first and only element of a list
        _find_all_usernames(arg)[0]
        for arg in arguments
    ]
