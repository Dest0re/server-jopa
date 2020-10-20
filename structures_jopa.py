class GlobalSettings:
    def __init__(self, nick_history_limit: int):
        self.NICK_HISTORY_LIMIT = nick_history_limit


class GuildData:
    def __init__(self, guild_id, info_channel_id, rules_channel_id, chat_channel_id, bot_channel_id, admin_role_id,
                 beter_role_id, member_role_id, commands_prefix):
        self.GUILD_ID = guild_id
        self.INFO_CHANNEL_ID = info_channel_id
        self.RULES_CHANNEL_ID = rules_channel_id
        self.CHAT_CHANNEL_ID = chat_channel_id
        self.BOT_CHANNEL_ID = bot_channel_id
        self.ADMIN_ROLE_ID = admin_role_id
        self.BETER_ROLE_ID = beter_role_id
        self.MEMBER_ROLE_ID = member_role_id
        self.COMMANDS_PREFIX = commands_prefix


class ServerData:
    def __init__(self, url, port):
        self.URL = url
        self.PORT = port


class Member:
    def __init__(self, m_id: int, db):
        self.id = m_id
        self.db = db

    async def set_cols(self, **kwargs):
        return await self.db.set_member_cols(self.id, **kwargs)

    async def get_cols(self, *args: str):
        return await self.db.get_member_cols(self.id, *args)

    async def set_col(self, col: str, value):
        return await self.set_cols(**{col: value})

    async def get_col(self, col: str):
        return await self.get_cols(col)
