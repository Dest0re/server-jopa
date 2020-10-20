import discord
import destlogger

import commands_jopa
import utils_jopa

log = destlogger.Logger(debug_mode=True)


class Client(discord.Client):
    def __init__(self, guild_data, db, *args, **kwargs):
        self.gd = guild_data
        self.db = db
        self.commands = commands_jopa.Commands(self, self.gd, self.db)
        self.utils = utils_jopa.Utils(db)

        self.is_first_on_ready = True
        self.MEMBER_ROLE = None
        self.ADMIN_ROLE = None
        self.BETER_ROLE = None
        self.GUILD = None
        super().__init__(*args, **kwargs)

    # Funcs

    # Async Funcs

    async def update_member(self, member):
        if self.ADMIN_ROLE in member.roles and self.BETER_ROLE in member.roles:
            await member.remove_roles(self.BETER_ROLE, reason="Каждый администратор уже бетер.")
        old_member_role = await self.db.get_member_status(member.id)
        if self.ADMIN_ROLE in member.roles:
            member_role = 'admin'
        elif member.bot:
            member_role = 'bot'
        elif self.BETER_ROLE in member.roles:
            member_role = 'beter'
        else:
            member_role = 'member'
        if old_member_role != member_role:
            await self.db.update_member(member.id, status=member_role)

    async def register_member(self, member):
        if self.ADMIN_ROLE in member.roles:
            await self.db.register_member(member.id, 'admin')
        elif member.bot:
            await self.db.register_member(member.id, 'bot')
        else:
            await self.db.register_member(member.id, 'member')

    async def check_member_registration(self, member):
        if not await self.db.is_registered(member.id):
            await self.register_member(member)
        else:
            await self.update_member(member)

    async def check_member_roles(self, member):
        if self.MEMBER_ROLE not in member.roles:
            await member.add_roles(self.MEMBER_ROLE)

    async def on_start_check_members(self):
        async for member in self.GUILD.fetch_members():
            await self.check_member_roles(member)
            await self.check_member_registration(member)

    async def prepare(self):
        self.GUILD = self.get_guild(self.gd.GUILD_ID)
        self.MEMBER_ROLE = self.GUILD.get_role(self.gd.MEMBER_ROLE_ID)
        self.ADMIN_ROLE = self.GUILD.get_role(self.gd.ADMIN_ROLE_ID)
        self.BETER_ROLE = self.GUILD.get_role(self.gd.BETER_ROLE_ID)

        await self.on_start_check_members()

    # Events

    async def on_member_update(self, before, after):
        if before.guild == self.GUILD:
            if before.roles != after.roles:
                await self.check_member_registration(after)

    async def on_ready(self):
        game = discord.Game("В разработке")
        await self.change_presence(activity=game)
        if self.is_first_on_ready:
            await self.prepare()
            self.is_first_on_ready = False

        log.info(f"Logged in Discord as {self.user}")

    async def on_message(self, message):
        if message.channel.guild.id == self.gd.GUILD_ID:
            if message.channel.id == self.gd.BOT_CHANNEL_ID:
                if message.content.startswith(self.gd.COMMANDS_PREFIX):
                    await self.commands.handle_command(message.content[len(self.gd.COMMANDS_PREFIX):], message)

    async def on_member_join(self, member):
        if member.guild.id == self.gd.GUILD_ID:
            await self.check_member_registration(member)
            await member.add_roles(self.MEMBER_ROLE)
            if not member.bot:
                await self.utils.set_nick(member)

    # Start

    async def start(self, *args, **kwargs):
        log.info("Starting Discord Client...")
        await super().start(*args, **kwargs)