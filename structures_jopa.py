import destlogger
import emoji
import typing

from exceptions_jopa import ArgumentError

log = destlogger.Logger(debug_mode=True)
seq_ = typing.TypeVar('seq_', typing.List, typing.Tuple)


class GlobalSettings:
    def __init__(self, nick_history_limit: int):
        self.NICK_HISTORY_LIMIT = nick_history_limit


class GuildData:
    def __init__(self, guild_id, info_channel_id, rules_channel_id, chat_channel_id, bot_channel_id, admin_role_id,
                 beter_role_id, member_role_id, delayed_banned_role_id, commands_prefix):
        self.GUILD_ID = guild_id
        self.INFO_CHANNEL_ID = info_channel_id
        self.RULES_CHANNEL_ID = rules_channel_id
        self.CHAT_CHANNEL_ID = chat_channel_id
        self.BOT_CHANNEL_ID = bot_channel_id
        self.ADMIN_ROLE_ID = admin_role_id
        self.BETER_ROLE_ID = beter_role_id
        self.MEMBER_ROLE_ID = member_role_id
        self.DELAYED_BANNED_ROLE_ID = delayed_banned_role_id
        self.COMMANDS_PREFIX = commands_prefix


class DBData:
    def __init__(self, default_member_data):
        self.DEFAULT_MEMBER_DATA = default_member_data


class ServerData:
    def __init__(self, url, port):
        self.URL = url
        self.PORT = port


class Member:
    def __init__(self, db):
        self._db = db

        self.id = None
        self.role = None
        self.badges = None
        self.sorted_badges = None
        self.nick_history = None
        self.delayed_banned = None

    # Low-Level

    async def update_cols(self, **kwargs):
        log.debug(f'Updating member {self.id} with {kwargs}.')
        for key, value in kwargs.items():
            self.__setattr__(key, value)
        return await self._db.members_.find_one_and_update({'_id': self.id}, {'$set': kwargs})

    async def update_col(self, key, value):
        return await self.update_cols(**{key: value})

    # Utils

    async def update_role(self, role: str):
        await self.update_col('role', role)

    # Register

    async def register(self, id_, **kwargs):
        default_member = self._db.DB_DATA.DEFAULT_MEMBER_DATA
        kwargs.update({"_id": id_})
        default_member.update(kwargs)
        log.debug(f'Registering {id_} with {default_member}...')
        await self._db.members_.insert_one(default_member)

        return await self.create(id_)

    # Badges

    async def set_badges(self, badges):
        await self.update_col('badges', badges)

    async def set_sorted_badges(self, badges):
        await self.update_col('sorted_badges', badges)

    async def give_badge(self, badge):
        if badge not in emoji.UNICODE_EMOJI:
            raise ArgumentError
        old_badges = self.badges
        old_badges.append(badge)
        print(old_badges)
        await self.set_badges(old_badges)

    async def remove_badge(self, badge: str) -> None:
        if badge not in emoji.UNICODE_EMOJI:
            raise ArgumentError
        badges = self.badges
        if badge in badges:
            badges.remove(badge)
            await self.set_badges(badges)

    async def remove_sorted_badge(self, badge: str) -> None:
        if badge not in emoji.UNICODE_EMOJI:
            raise ArgumentError
        badges = self.sorted_badges
        if badge in badges:
            badges.remove(badge)
            await self.set_sorted_badges(badges)

    async def give_badges(self, *args):
        for badge in args:
            await self.give_badge(badge)

    async def remove_badges(self, *args):
        await self.remove_sorted_badges(*args)
        for badge in args:
            await self.remove_badge(badge)

    async def remove_sorted_badges(self, *args):
        for badge in args:
            await self.remove_sorted_badge(badge)

    # Nick

    async def set_nick_history(self, history: seq_) -> seq_:
        old_history = self.nick_history
        await self.update_col('nick_history', history)
        return old_history

    async def add_nick_to_history(self, nick: str, limit: int) -> seq_:
        old_nick_list = self.nick_history
        if len(old_nick_list) < limit:
            old_nick_list.append(nick)
        else:
            old_nick_list = old_nick_list[1:]
            old_nick_list.append(nick)
        return await self.set_nick_history(old_nick_list)

    # Delayed ban

    async def set_delayed_ban_status(self, status):
        await self.update_col('delayed_banned', status)

    async def ban_delayed(self):
        await self.set_delayed_ban_status(True)

    async def unban_delayed(self):
        await self.set_delayed_ban_status(False)

    # Prop Funcs

    async def create(self, id_):
        self.id = id_

        raw_member = await self._db.get_raw_member(self.id)
        for key, value in raw_member.items():
            self.__setattr__(key, value)

        return self
