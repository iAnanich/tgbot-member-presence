import datetime
import logging

from telegram import Update, User
from telegram.ext import CallbackContext

from . import settings
from . import storage
from .utils import extract_usernames_from_args

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=settings.LOG_LEVEL,
)
logger = logging.getLogger(__name__)

HELP = '''
I was created to help you check out if user is in chat. 
Add me to a chat, write down nicknames (in a @nIck_Name14 format) and call me with /check command in separate message.
I will check if users listed in first message are present in chat and tell you if someone is missing.
'''


class CHAT_DATA:
    BEGAN_AT = 'began_at'
    MEMBERS_BY_USERNAME = 'members_by_username'


def _restore_chat_data(update: Update, context: CallbackContext) -> None:
    if not context.chat_data:
        from_file = storage.restore_chat_data(chat_id=update.effective_chat.id)
        if CHAT_DATA.BEGAN_AT in from_file:
            context.chat_data.update(from_file)
        else:
            context.chat_data.update({
                CHAT_DATA.MEMBERS_BY_USERNAME: {},
                CHAT_DATA.BEGAN_AT: datetime.datetime.utcnow().isoformat(),
            })


def _save_chat_data(update: Update, context: CallbackContext) -> None:
    storage.save_chat_data(chat_id=update.effective_chat.id, chat_data=context.chat_data)


def _remember_chat_member(username: str, user_data: dict, context: CallbackContext) -> None:
    context.chat_data[CHAT_DATA.MEMBERS_BY_USERNAME][username] = user_data


def _remember_user(user: User, context: CallbackContext) -> None:
    return _remember_chat_member(
        username=user.username,
        user_data={
            'id': user.id,
        },
        context=context,
    )


def _remember_caller(update: Update, context: CallbackContext) -> bool:
    """
    Remember command caller in chat data, and if it was not in chat data yet, return True.
    Otherwise, return False.
    """
    if update.effective_user.username not in context.chat_data[CHAT_DATA.MEMBERS_BY_USERNAME]:
        _remember_user(user=update.effective_user, context=context)
        return True
    else:
        return False


def _forget_chat_member(username: str, context: CallbackContext) -> bool:
    """
    Remove (forget) chat member data from chat data.
    Return True if data was removed, otherwise return False (if username was not in chat data).
    """
    try:
        context.chat_data[CHAT_DATA.MEMBERS_BY_USERNAME].pop(username)
    except KeyError:
        return False
    else:
        return True


def command_start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(HELP)


def command_help(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text(HELP)


def command_check(update: Update, context: CallbackContext) -> None:
    """Check presence of users listed in message, reply to which calls the command."""
    _restore_chat_data(update=update, context=context)

    _remember_caller(update=update, context=context)

    _save_chat_data(update=update, context=context)

    present_usernames = set(context.chat_data[CHAT_DATA.MEMBERS_BY_USERNAME].keys())
    mentioned_usernames = set(extract_usernames_from_args(arguments=context.args, clean=True))
    missing_usernames = mentioned_usernames.difference(present_usernames)

    if missing_usernames:
        reply_msg = f'Following chat members are missing: {" ".join("@" + un for un in missing_usernames)}'
    else:
        reply_msg = f'All mentioned users are present!'
    update.effective_message.reply_text(reply_msg)


def command_check_in(update: Update, context: CallbackContext) -> None:
    """Remember that user that called a command is a member of chat."""
    _restore_chat_data(update=update, context=context)

    caller_is_new = _remember_caller(update=update, context=context)

    _save_chat_data(update=update, context=context)

    if caller_is_new:
        reply_msg = f'Ok, now I will remember that you are in this chat.'
    else:
        reply_msg = f'Don\'t worry, I remember that you are here :)'
    update.effective_message.reply_text(reply_msg)


def command_forget_me(update: Update, context: CallbackContext) -> None:
    """Forget chat member who called this command."""
    _restore_chat_data(update=update, context=context)

    caller_was_in_memory = _forget_chat_member(update.effective_user.username, context=context)

    _save_chat_data(update=update, context=context)

    if caller_was_in_memory:
        reply_msg = 'Ok, now I don\'t know who You are.'
    else:
        reply_msg = 'I already don\'t know who You are.'
    update.effective_message.reply_text(reply_msg)


def command_forget(update: Update, context: CallbackContext) -> None:
    """Forget mentioned users."""
    _restore_chat_data(update=update, context=context)

    _remember_caller(update=update, context=context)

    mentioned_usernames = set(extract_usernames_from_args(arguments=context.args, clean=True))

    mismatched_usernames = set()
    forgot_usernames = set()
    caller_mentioned = False
    for username in mentioned_usernames:
        if username == update.effective_user.username:
            caller_mentioned = True
            continue
        if _forget_chat_member(username=username, context=context):
            forgot_usernames.add(username)
        else:
            mismatched_usernames.add(username)

    _save_chat_data(update=update, context=context)

    reply_msg = ''
    if forgot_usernames:
        reply_msg += 'Successfully forgot following chat members: ' + ' '.join(forgot_usernames) + '\n'
    if mismatched_usernames:
        reply_msg += 'Haven\'t found anything about following chat members: ' + ' '.join(mismatched_usernames) + '\n'
    if caller_mentioned:
        reply_msg += 'Not going to forget You that simple. Use /forget_me command for this.'
    if not reply_msg:
        reply_msg += 'Can not recognise any valid username.'
    update.effective_message.reply_text(
        reply_msg,
    )


def command_remember(update: Update, context: CallbackContext) -> None:
    """Remember mentioned users as if they are in chat."""
    _restore_chat_data(update=update, context=context)

    _remember_caller(update=update, context=context)

    mentioned_usernames = set(extract_usernames_from_args(arguments=context.args, clean=True))
    for username in mentioned_usernames:
        if username in context.chat_data[CHAT_DATA.MEMBERS_BY_USERNAME].keys():
            continue
        _remember_chat_member(username=username, user_data={}, context=context)

    _save_chat_data(update=update, context=context)

    reply_msg = f'Successfully remembered following chat members: ' + ' '.join(mentioned_usernames)
    update.effective_message.reply_text(reply_msg)


def command_list(update: Update, context: CallbackContext) -> None:
    """Remember mentioned users as if they are in chat."""
    _restore_chat_data(update=update, context=context)

    _remember_caller(update=update, context=context)

    _save_chat_data(update=update, context=context)

    all_usernames = context.chat_data[CHAT_DATA.MEMBERS_BY_USERNAME].keys()
    reply_msg = f'Listing all chat members in my memory:\n* ' + '\n* '.join(all_usernames)
    update.effective_message.reply_text(reply_msg)


def update_members(update: Update, context: CallbackContext) -> None:
    """Remember new chat users."""
    _restore_chat_data(update=update, context=context)

    if CHAT_DATA.MEMBERS_BY_USERNAME not in context.chat_data:
        context.chat_data[CHAT_DATA.MEMBERS_BY_USERNAME] = []

    # remember new members
    for user in update.message.new_chat_members:
        _remember_user(user=user, context=context)

    # FIXME - sometimes, it doesn't react as intended
    # forget left members
    if update.message.left_chat_member:
        _forget_chat_member(username=update.message.left_chat_member.username, context=context)

    _save_chat_data(update=update, context=context)
