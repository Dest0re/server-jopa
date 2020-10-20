import destlogger

import utils_jopa

log = destlogger.Logger(debug_mode=True)


class Commands:
    def __init__(self, client, guild_data, db):
        self.gd = guild_data
        self.db = db
        self.client = client
        self.utils = utils_jopa.Utils(db)

    def parse_mention(self, mention):
        member_id = int(''.join([sym for sym in mention if sym.isdigit()]))
        return self.client.GUILD.get_member(member_id)

    async def get_profile(self, m, *args):
        @self.utils.command('members')
        async def command(message):
            if not args:
                member_profile = await self.utils.get_member_profile(message.author)
                await message.channel.send(embed=member_profile)
            else:
                member = self.parse_mention(args[0])
                if member:
                    member_profile = await self.utils.get_member_profile(member)
                    await message.channel.send(embed=member_profile)
                else:
                    raise AttributeError
        return await command(m)

    async def change_nickname(self, m, *a):
        @self.utils.command('members')
        async def command(message, *args):
            if len(args) == 0:
                await self.utils.set_nick(message.author)
                await message.channel.send(f'{message.author.mention}, ник изменён.')
            elif len(args) == 1:
                try:
                    nick_num = int(args[0])
                except ValueError:
                    raise AttributeError
                if nick_num <= 0:
                    raise AttributeError
                nick_history = await self.db.get_nick_history(message.author.id)
                if nick_num > nick_history:
                    raise ValueError
                await message.author.edit(nick=nick_history[nick_num-1])
                await message.channel.send(f'{message.author.mention}, ник изменён.')
            else:
                raise AttributeError
        return await command(m, *a)

    async def give_badges(self, m, *a):
        @self.utils.command('ids', (350206214782582784,))
        async def command(message, *args):
            if len(args) >= 2:
                try:
                    member = self.parse_mention(args[0])
                    assert member, None
                except AssertionError:
                    raise AttributeError
                await self.db.give_badges(member.id, *args[1:])
                await message.channel.send(f'{message.author.mention} дал {member.mention} один или несколько бейджей! '
                                           f'Так держать!')
            else:
                raise AttributeError
        return await command(m, *a)

    async def remove_badges(self, m, *a):
        @self.utils.command('ids', (350206214782582784,))
        async def command(message, *args):
            if len(args) >= 2:
                try:
                    member = self.parse_mention(args[0])
                    assert member, None
                except AssertionError:
                    raise AttributeError
                await self.db.remove_badges(member.id, *args[1:])
                await member.edit(nick=member.nick.split()[0] + ' ' + ''.join(
                    await self.db.get_sorted_badges(member.id)))
                await message.channel.send(f'{member.mention} лишился бейджика.')
            else:
                raise AttributeError
        return await command(m, *a)

    async def edit_badges(self, m, *a):
        @self.utils.command('members')
        async def command(message, *args):
            if len(args) > 0:
                badges = await self.db.get_badges(message.author.id)
                unavailable_badges = []
                for badge in args:
                    if badge in badges:
                        badges.remove(badge)
                    else:
                        unavailable_badges.append(badge)
                if unavailable_badges:
                    await message.channel.send(f"У вас нет этих бейджиков: {', '.join(unavailable_badges)}!")
                    return
                await self.db.set_sorted_badges(message.author.id, args)
                await message.author.edit(nick=message.author.nick.split()[0] + ' ' + ''.join(await self.db.get_sorted_badges(message.author.id)))
                await message.channel.send('Бейджи обновлены!')
            else:
                await self.db.set_sorted_badges(message.author.id, [])
                await message.author.edit(nick=message.author.nick.split()[0])
                await message.channel.send('Бейджи обновлены!')
        return await command(m, *a)

    async def watch_nick_history(self, m):
        @self.utils.command('members')
        async def command(message):
            nick_history = await self.db.get_nick_history(message.author.id)
            if nick_history:
                msg = f'{message.author.mention}, история ваших ников:\n'
                for i, nick in enumerate(nick_history):
                    msg += f'{i+1}) {nick};\n'
            else:
                msg = f'{message.author.mention}, у вас нет истории ников!'
            await message.channel.send(msg)
        await command(m)

    async def delayed_ban(self, m, *a):
        @self.utils.command('admins')
        async def command(message, *args):
            if len(args) == 1:
                member = self.parse_mention(args[0])
                if member:
                    await self.db.delayed_ban_member(member.id)
                else:
                    raise AttributeError
        return await command(m, *a)

    async def delayed_unban(self, m, *a):
        @self.utils.command('admins')
        async def command(message, *args):
            if len(args) == 1:
                member = self.parse_mention(args[0])
                if member:
                    await self.db.delayed_unban_member(member.id)
                else:
                    raise AttributeError
        return await command(m, *a)

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
        if command == 'dban':
            await self.delayed_ban(message, *args)
        if command == 'dunban':
            await self.delayed_unban(message, *args)
        if command == 'testc':
            await self.test_command(message, *args)
        if command == 'errorc':
            await self.error_command(message)
        if command == 'profile':
            await self.get_profile(message, *args)
