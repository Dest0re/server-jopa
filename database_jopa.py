import os
import typing
import json

import aiosqlite
import destlogger
import emoji

import structures_jopa


log = destlogger.Logger(debug_mode=True)
seq_ = typing.TypeVar('seq_', typing.List, typing.Tuple)


def load_json_config(fp: str):
    with open(fp) as f:
        return json.load(f)


class DB:
    def __init__(self, path, global_settings: structures_jopa.GlobalSettings, event_loop):
        self.loop = event_loop
        self.is_ready = False

        self.conn = None
        self.path = path
        self.GS = global_settings

    # Low-Level

    async def update_row(self, table: str, row_id: int, **kwargs) -> None:
        async with self.conn.cursor() as cur:
            to_be_updated = []
            for key in kwargs.keys():
                to_be_updated.append(f'{key} = "{kwargs[key]}"')
                to_be_updated_string = ", ".join(to_be_updated)
            await cur.execute(f'update {table} set {to_be_updated_string} where id = {row_id}')
            await self.conn.commit()
            log.debug(f'Updated {row_id} in {table}: {to_be_updated_string}')

    async def get_member_cols(self, member_id: int, *args: str) -> tuple:
        cols = ', '.join(args)
        async with self.conn.cursor() as cur:
            await cur.execute(f'select {cols} from users where id = "{member_id}"')
            return await cur.fetchone()

    async def get_user_by_id(self, member_id: int) -> tuple:
        async with self.conn.cursor() as cur:
            await cur.execute(f'select id, status, badges, badges_sorted, delayed_banned from users where id = "{member_id}"')
            return await cur.fetchone()

    async def register_member(self, member_id: int, status: str) -> None:
        async with self.conn.cursor() as cur:
            log.debug(f'Registering {member_id} as {status}...')
            await cur.execute(f'insert into users (id, status) values ({member_id}, "{status}")')
            await self.conn.commit()

    async def get_all_table(self, table: str):
        async with self.conn.cursor() as cur:
            await cur.execute(f'select * from {table}')
            return await cur.fetchall()

    # Useful Utils

    async def set_member_cols(self, member_id: int, **kwargs: str) -> None:
        await self.update_row('users', member_id, **kwargs)

    async def set_member_col(self, member_id: int, key, value) -> None:
        await self.set_member_cols(member_id, **{key: value})

    async def get_member_col(self, member_id: int, col: str):
        member_col = await self.get_member_cols(member_id, col)
        return member_col[0]

    async def set_member_list_col(self, member_id: int, col: str, seq: seq_) -> None:
        await self.update_row('users', member_id, **{col: ','.join(seq)})

    async def get_member_list_col(self, member_id: (int, str), col: str) -> list:
        member_col = await self.get_member_col(member_id, col)
        if member_col:
            return list(member_col.split(','))
        else:
            return []

    async def get_member_bool_col(self, member_id: int, col: str):
        member_col = await self.get_member_col(member_id, col)
        return 0 if not member_col else True

    async def set_member_bool_col(self, member_id: int, col: str, value: bool):
        if value:
            await self.set_member_col(member_id, col, 1)
        else:
            await self.set_member_col(member_id, col, 0)

    async def update_member(self, member_id: int, **kwargs):
        await self.update_row('users', member_id, **kwargs)

    async def get_member_status(self, member_id: int) -> str:
        return await self.get_member_col(member_id, 'status')

    # Register

    async def is_registered(self, member_id: int) -> bool:
        return True if await self.get_user_by_id(member_id) else False

    async def register_members(self, *args):
        for arg in args:
            await self.register_member(*arg)

    # Badges

    async def get_badges(self, member_id: int) -> list:
        badges = await self.get_member_list_col(member_id, 'badges')
        if not badges:
            badges = []

        return badges

    async def get_sorted_badges(self, member_id: int) -> list:
        badges = await self.get_member_list_col(member_id, 'badges_sorted')
        if not badges:
            badges = []

        return badges

    async def set_sorted_badges(self, member_id: int, badges: seq_) -> None:
        await self.set_member_list_col(member_id, 'badges_sorted', badges)

    async def set_badges(self, member_id: int, badges: seq_) -> None:
        await self.set_member_list_col(member_id, 'badges', badges)

    async def give_badge(self, member_id: int, badge: str) -> None:
        if badge not in emoji.UNICODE_EMOJI:
            raise AttributeError
        old_badges = await self.get_badges(member_id)
        old_badges.append(badge)
        await self.set_badges(member_id, old_badges)

    async def remove_badge(self, member_id: id, badge: str) -> None:
        if badge not in emoji.UNICODE_EMOJI:
            raise AttributeError
        badges = await self.get_badges(member_id)
        if badge in badges:
            badges.remove(badge)
            await self.set_badges(member_id, badges)

    async def remove_sorted_badge(self, member_id: int, badge: str) -> None:
        if badge not in emoji.UNICODE_EMOJI:
            raise AttributeError
        badges = await self.get_sorted_badges(member_id)
        if badge in badges:
            badges.remove(badge)
            await self.set_sorted_badges(member_id, badges)

    async def give_badges(self, member_id: int, *args: str) -> None:
        for badge in args:
            await self.give_badge(member_id, badge)

    async def remove_badges(self, member_id: int, *args: str) -> None:
        await self.remove_sorted_badges(member_id, *args)
        for badge in args:
            await self.remove_badge(member_id, badge)

    async def remove_sorted_badges(self, member_id: int, *args: str) -> None:
        for badge in args:
            await self.remove_sorted_badge(member_id, badge)

    # Nick History

    async def set_nick_history(self, member_id: int, history: seq_) -> seq_:
        await self.set_member_list_col(member_id, 'nick_history', history)
        return history

    async def get_nick_history(self, member_id: int) -> list:
        return await self.get_member_list_col(member_id, 'nick_history')

    async def add_nick_to_history(self, member_id: int, nick: str) -> seq_:
        old_nick_list = await self.get_nick_history(member_id)
        if len(old_nick_list) < self.GS.NICK_HISTORY_LIMIT:
            old_nick_list.append(nick)
        else:
            old_nick_list = old_nick_list[1:]
            old_nick_list.append(nick)
        return await self.set_nick_history(member_id, old_nick_list)

    # Delayed Ban

    async def set_delayed_ban_status(self, member_id: int, status: bool) -> None:
        await self.set_member_bool_col(member_id, 'delayed_banned', status)

    async def get_delayed_ban_status(self, member_id: int):
        await self.get_member_bool_col(member_id, 'delayed_banned')

    async def delayed_ban_member(self, member_id: int) -> None:
        await self.set_delayed_ban_status(member_id, True)

    async def delayed_unban_member(self, member_id: int) -> None:
        await self.set_delayed_ban_status(member_id, True)

    # Important

    async def prepare(self):
        self.conn = await aiosqlite.connect(self.path, loop=self.loop)

    async def close(self):
        await self.conn.close()

    async def start(self):
        log.info('Preparing DB...')
        await self.prepare()
        self.is_ready = True
        log.info(f'DB is connected! Current DB size is {os.path.getsize(self.path) / 1024} KBs!')
