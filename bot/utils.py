import re
from typing import List, Iterable, Iterator


def _find_all_usernames(string: str) -> List[str]:
    """
    Returns list of all usernames in format ["@username1", "@username2", ...]
    Credit to https://stackoverflow.com/a/63308482/6233648
    """
    tg_nick_pattern = r'.*\B@(?=\w{5,64}\b)[a-zA-Z0-9]+(?:_[a-zA-Z0-9]+)*.*'
    return re.findall(tg_nick_pattern, string)


def extract_usernames_from_args(arguments: List[str], clean: bool = False) -> List[str]:
    """Returns list of usernames extracted from command arguments."""
    return [
        full_username_list[0][1:] if clean else full_username_list[0]
        for full_username_list in (
            # take first and only element of a list
            _find_all_usernames(arg)
            for arg in arguments
        )
        if full_username_list
    ]


def iter_pack(iterable: Iterable, size: int) -> Iterator:
    pack_buffer = []
    for i, el in enumerate(iterable):
        pack_buffer.append(el)
        if (i + 1) % size == 0:
            yield iter(pack_buffer)
            pack_buffer = []
    else:
        yield iter(pack_buffer)
