import destlogger

import utils_jopa
from exceptions_jopa import ArgumentError

log = destlogger.Logger(debug_mode=True)


class Commands:
    def __init__(self, client, guild_data, db):
        self.gd = guild_data
        self.db = db
        self.client = client
        self.utils = utils_jopa.Utils(db)

    def parse_mention(self, mention):
        member_id = int(''.join([sym for sym in mention if sym.isdigit()]))
        member = self.client.GUILD.get_member(member_id)
        if member:
            return member
        else:
            raise KeyError

    async def get_profile(self, m, *a):
        @self.utils.command('members')
        async def command(message, *args):
            if not args:
                member_profile = await self.utils.get_member_profile(message.author)
                await message.channel.send(embed=member_profile)
            else:
                try:
                    member = self.parse_mention(args[0])
                except KeyError:
                    raise ArgumentError

                member_profile = await self.utils.get_member_profile(member)
                await message.channel.send(embed=member_profile)

        return await command(m, *a)

    async def change_nickname(self, m, *a):
        @self.utils.command('members')
        async def command(message, *args):
            if len(args) == 0:
                await self.utils.set_nick(message.author, on_command=True)
                await message.channel.send(f'{message.author.mention}, ник изменён.')
            elif len(args) == 1:
                db_member = self.db.get_member(message.author.id)

                try:
                    nick_num = int(args[0])
                except ValueError:
                    raise ArgumentError
                if nick_num <= 0:
                    raise ArgumentError
                nick_history = db_member.nick_history
                if nick_num > len(nick_history):
                    raise ArgumentError
                await message.author.edit(nick=nick_history[nick_num-1] + ' ' + ''.join(db_member.sorted_badges))
                await message.channel.send(f'{message.author.mention}, ник изменён.')
            else:
                raise ArgumentError
        return await command(m, *a)

    async def give_badges(self, m, *a):
        @self.utils.command('ids', (350206214782582784,))
        async def command(message, *args):
            if len(args) >= 2:
                try:
                    member = self.parse_mention(args[0])
                except KeyError:
                    raise ArgumentError
                db_member = self.db.get_member(member.id)
                await db_member.give_badges(*args[1:])
                await message.channel.send(f'{message.author.mention} дал {member.mention} один или несколько бейджей! '
                                           f'Так держать!')
            else:
                raise ArgumentError
        return await command(m, *a)

    async def remove_badges(self, m, *a):
        @self.utils.command('ids', (350206214782582784,))
        async def command(message, *args):
            if len(args) >= 2:
                try:
                    member = self.parse_mention(args[0])
                except KeyError:
                    raise ArgumentError
                db_member = self.db.get_member(member.id)
                await db_member.remove_badges(*args[1:])
                await member.edit(nick=member.nick.split()[0] + ' ' + ''.join(db_member.sorted_badges))
                await message.channel.send(f'{member.mention} лишился бейджика.')
            else:
                raise ArgumentError
        return await command(m, *a)

    async def edit_badges(self, m, *a):
        @self.utils.command('members')
        async def command(message, *args):
            db_member = self.db.get_member(message.author.id)
            if len(args) > 0:
                badges = db_member.badges
                unavailable_badges = []
                for badge in args:
                    if badge in badges:
                        badges.remove(badge)
                    else:
                        unavailable_badges.append(badge)
                if unavailable_badges:
                    await message.channel.send(f"У вас нет этих бейджиков: {', '.join(unavailable_badges)}!")
                    return
                await db_member.set_sorted_badges(args)
                await message.author.edit(nick=message.author.nick.split()[0] + ' ' + ''.join(db_member.sorted_badges))
                await message.channel.send('Бейджи обновлены!')
            else:
                await db_member.set_sorted_badges([])
                await message.author.edit(nick=message.author.nick.split()[0])
                await message.channel.send('Бейджи обновлены!')
        return await command(m, *a)

    async def watch_nick_history(self, m):
        @self.utils.command('members')
        async def command(message):
            db_member = self.db.get_member(message.author.id)
            nick_history = await db_member.nick_history
            if nick_history:
                msg = f'{message.author.mention}, история ваших ников:\n'
                for i, nick in enumerate(nick_history):
                    msg += f'{i+1}) {nick};\n'
            else:
                msg = f'{message.author.mention}, у вас нет истории ников!'
            await message.channel.send(msg)
        await command(m)

    async def test_command(self, m, *a):
        @self.utils.command('admins')
        async def command(message, *args):
            log.debug(f'Test message: "{message.content}", args: "{args}"')
            for arg in args:
                log.debug(f'{arg}: {len(arg)}')
        return await command(m, *a)

    async def error_command(self, m):
        @self.utils.command('admins')
        async def command(message):
            raise Exception
        await command(m)

    async def handle_command(self, text, message):
        command, args = utils_jopa.parse_command(text)
        if command == 'chnick':
            await self.change_nickname(message, *args)
        if command == 'bgive':
            await self.give_badges(message, *args)
        if command == 'bremove':
            await self.remove_badges(message, *args)
        if command == 'bedit':
            await self.edit_badges(message, *args)
        if command == 'watchnh':
            await self.watch_nick_history(message)
        if command == 'testc':
            await self.test_command(message, *args)
        if command == 'errorc':
            await self.error_command(message)
        if command == 'profile':
            await self.get_profile(message, *args)
