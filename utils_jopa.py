import random
import string
import typing
import asyncio
import traceback

import discord
import destlogger

import database_jopa
import structures_jopa
from exceptions_jopa import ArgumentError

config = database_jopa.load_json_config('./config.json')
NICK_HISTORY_LIMIT = config['discord_bot']['nick_history_limit']

global_settings = structures_jopa.GlobalSettings(NICK_HISTORY_LIMIT)

log = destlogger.Logger(debug_mode=True)
loop = asyncio.get_event_loop()

symbols = string.ascii_letters + string.digits


def generate_nick(length=10):
    return ''.join(random.choices(symbols, k=length))


def parse_command(text):
    splitted_text = text.split()
    command = splitted_text[0]
    args = splitted_text[1:]
    return command, args


class Utils:
    def __init__(self, db):
        self.db = db

    async def get_member_profile(self, member: discord.Member) -> discord.Embed:
        db_member = self.db.get_member(member.id)
        nick_history = ''
        colour = member.top_role.colour if str(member.top_role.colour) != "#ffffff" else discord.Colour.from_rgb(255, 255, 254)
        for i, nick in enumerate(db_member.nick_history):
            nick_history += f'{i+1}) {nick};\n'
        badges = ', '.join(db_member.badges)
        badges = 'Нет доступных бейджей' if not badges else badges
        nick_history = 'История ников пуста' if not nick_history else nick_history
        member_profile = discord.Embed(title=f"Профиль {member.display_name}:",
                                       description=f"Test description {member.mention}",
                                       colour=colour)
        member_profile.add_field(name="Роль", value=db_member.role, inline=True)
        member_profile.add_field(name="Доступные бейджи", value=badges, inline=False)
        member_profile.add_field(name="История ников", value=nick_history, inline=True)
        member_profile.set_footer(icon_url=str(member.avatar_url), text="Test footer")

        return member_profile

    def command(self, role: str, ids: typing.Sequence = None):
        def decorator(func):
            async def wrapped(message, *args, **kwargs):
                log.debug(f'Command: {message.content}')
                async with message.channel.typing():
                    db_member = self.db.get_member(message.author.id)
                    try:
                        if role == 'ids':
                            if message.author.id in ids:
                                return await func(message, *args, **kwargs)
                        elif role == 'admins':
                            if db_member.role == 'admin':
                                return await func(message, *args, **kwargs)
                        elif role == 'beters':
                            if db_member.role == 'beter':
                                return await func(message, *args, **kwargs)
                        elif role == 'members':
                            if db_member.role != 'debotted':
                                return await func(message, *args, **kwargs)

                        await message.channel.send(f'{message.author.mention}, у вас недостаточно прав, чтобы использовать '
                                                   f'эту команду!')
                    except discord.Forbidden:
                        await message.channel.send(f'{message.author.mention}, у меня недостаточно прав, чтобы сделать '
                                                   f'это!')
                    except ArgumentError:
                        await message.channel.send(f'{message.author.mention}, вы ошиблись с аргументами!')
                    except:
                        await message.channel.send(f'{message.author.mention}, извиняюсь, что-то случилось! Что именно? '
                                                   f'Понятия не имею.')
                        log.warning(f'Ignoring warning in handling the {message.content} message \n{traceback.format_exc()}')

            return wrapped

        return decorator

    async def set_nick(self, member):
        db_member = self.db.get_member(member.id)
        nick = generate_nick()
        await member.edit(nick=nick + ' ' + ''.join(db_member.sorted_badges))
        await db_member.add_nick_to_history(nick, NICK_HISTORY_LIMIT)
        return member
