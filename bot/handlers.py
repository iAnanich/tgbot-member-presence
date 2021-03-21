import datetime
import logging

from telegram import Update, User
from telegram.ext import CallbackContext

from . import settings
from . import storage
from .utils import extract_usernames_from_args, iter_pack

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=settings.LOG_LEVEL,
)
logger = logging.getLogger(__name__)

HELP = '''
I was created to help you check out if users are in chat.
Source code: https://github.com/iAnanich/tgbot-member-presence

How it works - bot tracks chat updates about users joining or leaving a chat.
Bot does not require any permissions and functions well with privacy mode enabled.

First - add me to a group chat and call /start command to enable my user joined/left tracking.
Optionally, you can pass usernames (with @ character) with it and I will remember mentioned users as present in chat.
Second - add some users.
Third - /list to known who I remember and /check to ensure everyone is present.
Note: /check command looks for usernames in both command arguments (message with command itself) 
and message that you are replying to. this can be useful if you have a list of usernames already, 
and want to re-check it a few times. Although, changing message with /check command will trigger me too.

Available commands:
/start - begin my work in new chat, arguments work identical to /remember
/check - check that every mentioned (both in command arguments and reply-to message) user is a member of this chat
/list - list all chat members in memory
/check_in - tell me that you are in this chat
/forget_me - tell me to forget your presence in this chat
/help - get more instructions on how to use me
/remember - (admin only) tell me to remember mentioned users for this chat
/forget - (admin only) tell me to forget mentioned users for this chat
/disable - (admin only) tell me to stop tracking users (it's enabled by default)
/enable - (admin only) tell me to start tracking users

Note: Admin only commands can be executed only by pre-defined admins.
'''


class CHAT_DATA:
    BEGAN_AT = 'began_at'
    MEMBERS_BY_USERNAME = 'members_by_username'
    ENABLED = 'enabled'
    TITLE = 'title'
    TGID = 'tgid'


def _restore_chat_data(update: Update, context: CallbackContext, create: bool = False) -> bool:
    """Return False if data is not present nor in memory nor in storage."""
    if not context.chat_data:
        from_file = storage.restore_chat_data(chat_id=update.effective_chat.id)
        if CHAT_DATA.BEGAN_AT in from_file:
            context.chat_data.update(from_file)
        elif create:
            context.chat_data.update({
                CHAT_DATA.MEMBERS_BY_USERNAME: {},
                CHAT_DATA.BEGAN_AT: datetime.datetime.utcnow().isoformat(),
                CHAT_DATA.ENABLED: False,
                CHAT_DATA.TITLE: update.effective_chat.title,
                CHAT_DATA.TGID: update.effective_chat.id,
            })
        else:
            return False
    return True


def _save_chat_data(update: Update, context: CallbackContext) -> None:
    storage.save_chat_data(chat_id=update.effective_chat.id, chat_data=context.chat_data)


def _enable_tracking(update: Update, context: CallbackContext) -> None:
    context.chat_data[CHAT_DATA.ENABLED] = True


def _disable_tracking(update: Update, context: CallbackContext) -> None:
    context.chat_data[CHAT_DATA.ENABLED] = False


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


def command_help(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text(HELP)


def command_debug(update: Update, context: CallbackContext) -> None:
    """Display debug info."""
    chat = update.effective_chat
    text = (
        f'Chat ID: `{chat.id}`\n'
        f'Chat type: `{chat.type}`\n'
        f'Chat title: `{chat.title}`\n'
    )
    if chat.type in {chat.GROUP, chat.SUPERGROUP}:
        try:
            if _restore_chat_data(update=update, context=context):
                text += (
                    f'Tracking enabled: `{context.chat_data[CHAT_DATA.ENABLED]}`\n'
                    f'Began at: `{context.chat_data[CHAT_DATA.BEGAN_AT]}`'
                )
            else:
                text += f'No data for this chat yet.'
        except Exception:
            text += f'Could not retrieve additional chat data.\n'
    update.message.reply_markdown(text)


def command_start(update: Update, context: CallbackContext) -> None:
    """Remember mentioned users as if they are in chat."""
    if update.effective_user.username not in settings.TGBOT_ADMIN_USERNAMES:
        update.effective_message.reply_text(f'Bot can be activated only by pre-defined admin.')
        return

    _restore_chat_data(update=update, context=context, create=True)

    _remember_caller(update=update, context=context)

    _enable_tracking(update=update, context=context)

    mentioned_usernames = set(extract_usernames_from_args(arguments=context.args, clean=True))

    if mentioned_usernames:
        for username in mentioned_usernames:
            if username in context.chat_data[CHAT_DATA.MEMBERS_BY_USERNAME].keys():
                continue
            _remember_chat_member(username=username, user_data={}, context=context)
        reply_msg = f'Successful activation!\nRemembered following chat members: ' + ' '.join(mentioned_usernames)
    else:
        reply_msg = f'Successful activation!'

    _save_chat_data(update=update, context=context)

    update.effective_message.reply_text(reply_msg)


def command_check(update: Update, context: CallbackContext) -> None:
    """Check presence of users listed in message, reply to which calls the command."""
    if not _restore_chat_data(update=update, context=context):
        update.effective_message.reply_text(f'Initialise me with /start command first.')

    _remember_caller(update=update, context=context)

    _save_chat_data(update=update, context=context)

    # potential usernames from reply-to message
    if update.effective_message.reply_to_message:
        reply_to_msg_text = update.effective_message.reply_to_message.text
        reply_to_potential_mentions = reply_to_msg_text.replace('\n', ' ').split(' ')
    else:
        reply_to_potential_mentions = []

    mentioned_usernames = set(extract_usernames_from_args(
        arguments=context.args + reply_to_potential_mentions,
        clean=True,
    ))
    present_usernames = set(context.chat_data[CHAT_DATA.MEMBERS_BY_USERNAME].keys())
    missing_usernames = mentioned_usernames.difference(present_usernames)

    if missing_usernames:
        username_packs = list(iter_pack(missing_usernames, size=settings.TGBOT_MAX_MENTIONS_PER_MESSAGE))
        for i, usernames_pack in enumerate(username_packs):
            mentions = [f'@{un}' for un in usernames_pack]
            reply_html = (
                f'Following <code>{len(mentions)}</code> chat members '
                f'(<code>{len(missing_usernames)}</code> in total) are missing '
                f'(message <code>{i + 1}</code> of <code>{len(username_packs)}</code>):\n'
            )
            reply_html += ' '.join(mentions) + '\n'
            reply_html += (
                f'If <b>You</b> got mentioned by this message, '
                f'please, click on /check_in command.'
            )
            update.effective_message.reply_html(reply_html)
    else:
        reply_text = f'All mentioned users are present!'
        update.effective_message.reply_text(reply_text)


def command_check_in(update: Update, context: CallbackContext) -> None:
    """Remember that user that called a command is a member of chat."""
    if not _restore_chat_data(update=update, context=context):
        update.effective_message.reply_text(f'Initialise me with /start command first.')

    caller_is_new = _remember_caller(update=update, context=context)

    _save_chat_data(update=update, context=context)

    if caller_is_new:
        reply_msg = f'Ok, now I will remember that you are in this chat.'
    else:
        reply_msg = f'Don\'t worry, I remember that you are here :)'
    update.effective_message.reply_text(reply_msg)


def command_forget_me(update: Update, context: CallbackContext) -> None:
    """Forget chat member who called this command."""
    if not _restore_chat_data(update=update, context=context):
        update.effective_message.reply_text(f'Initialise me with /start command first.')

    caller_was_in_memory = _forget_chat_member(update.effective_user.username, context=context)

    _save_chat_data(update=update, context=context)

    if caller_was_in_memory:
        reply_msg = 'Ok, now I don\'t know who You are.'
    else:
        reply_msg = 'I already don\'t know who You are.'
    update.effective_message.reply_text(reply_msg)


def command_forget(update: Update, context: CallbackContext) -> None:
    """Forget mentioned users."""
    if not _restore_chat_data(update=update, context=context):
        update.effective_message.reply_text(f'Initialise me with /start command first.')

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
    if not _restore_chat_data(update=update, context=context):
        update.effective_message.reply_text(f'Initialise me with /start command first.')

    _remember_caller(update=update, context=context)

    mentioned_usernames = set(extract_usernames_from_args(arguments=context.args, clean=True))

    if mentioned_usernames:
        for username in mentioned_usernames:
            if username in context.chat_data[CHAT_DATA.MEMBERS_BY_USERNAME].keys():
                continue
            _remember_chat_member(username=username, user_data={}, context=context)
        reply_msg = f'Successfully remembered following chat members: ' + ' '.join(mentioned_usernames)
    else:
        reply_msg = f'No users mentioned - done nothing.'

    _save_chat_data(update=update, context=context)

    update.effective_message.reply_text(reply_msg)


def command_list(update: Update, context: CallbackContext) -> None:
    """Remember mentioned users as if they are in chat."""
    if not _restore_chat_data(update=update, context=context):
        update.effective_message.reply_text(f'Initialise me with /start command first.')

    _remember_caller(update=update, context=context)

    _save_chat_data(update=update, context=context)

    all_usernames = context.chat_data[CHAT_DATA.MEMBERS_BY_USERNAME].keys()
    reply_msg = f'Listing all chat members in my memory:\n* ' + '\n* '.join(all_usernames)
    update.effective_message.reply_text(reply_msg)


def command_enable(update: Update, context: CallbackContext) -> None:
    """Enable users tracking."""
    if not _restore_chat_data(update=update, context=context):
        update.effective_message.reply_text(f'Initialise me with /start command first.')

    _remember_caller(update=update, context=context)

    if context.chat_data[CHAT_DATA.ENABLED]:
        reply_msg = 'User tracking already enabled.'
    else:
        _enable_tracking(update=update, context=context)
        reply_msg = f'User tracking successfully enabled.'

    _save_chat_data(update=update, context=context)

    update.effective_message.reply_text(reply_msg)


def command_disable(update: Update, context: CallbackContext) -> None:
    """Disable users tracking."""
    if not _restore_chat_data(update=update, context=context):
        update.effective_message.reply_text(f'Initialise me with /start command first.')

    _remember_caller(update=update, context=context)

    if not context.chat_data[CHAT_DATA.ENABLED]:
        reply_msg = 'User tracking already disabled.'
    else:
        _disable_tracking(update=update, context=context)
        reply_msg = f'User tracking successfully disabled.'

    _save_chat_data(update=update, context=context)

    update.effective_message.reply_text(reply_msg)


def update_members(update: Update, context: CallbackContext) -> None:
    """Remember new chat users."""
    if not _restore_chat_data(update=update, context=context):
        return

    # Quit if tracking is disabled
    if not context.chat_data[CHAT_DATA.ENABLED]:
        return

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
