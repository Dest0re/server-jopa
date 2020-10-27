import typing
import json

import destlogger
import motor.motor_asyncio

import structures_jopa

log = destlogger.Logger(debug_mode=True)
seq_ = typing.TypeVar('seq_', typing.List, typing.Tuple)


def load_json_config(fp: str):
    with open(fp) as f:
        return json.load(f)


class DB:
    def __init__(self, db_data: structures_jopa.DBData, global_settings: structures_jopa.GlobalSettings, event_loop):
        self.loop = event_loop
        self.is_ready = False

        self.conn = None
        self.GS = global_settings
        self.DB_DATA = db_data

        self._db_client = None
        self._db = None
        self._members = []
        self.members_ = None

    # Low-Level

    async def get_raw_member(self, id_):
        return await self.members_.find_one({'_id': id_})

    async def update_member_cols(self, id_,  **kwargs):
        log.debug(f'Updating member {id_} with {kwargs}.')
        return await self.members_.find_one_and_update({'_id': id_}, kwargs)

    async def _get_raw_members(self):
        return await self.members_.find().to_list(await self.members_.estimated_document_count())

    async def register_member(self, id_, **kwargs):
        new_member = structures_jopa.Member(self)
        self._members.append(await new_member.register(id_, **kwargs))

    # Useful Utils

    def get_member(self, id_):
        try:
            return tuple(filter(lambda m: m.id == id_, self.members))[0]
        except IndexError:
            return None

    @property
    def members(self):
        return self._members

    # Register

    async def is_registered(self, id_: int) -> bool:
        return True if self.get_member(id_) else False

    async def register_members(self, *args):
        for arg in args:
            await self.register_member(*arg)

    # Important

    async def prepare_mongodb(self):
        self._db_client = motor.motor_asyncio.AsyncIOMotorClient()
        self._db = self._db_client.server_jopa
        self.members_ = self._db.members

    async def _load_members(self):
        for member in await self._get_raw_members():
            new_member = structures_jopa.Member(self)
            self._members.append(await new_member.create(member['_id']))

    async def close(self):
        await self.conn.close()

    async def start(self):
        log.info('Preparing DB...')
        await self.prepare_mongodb()
        log.info('MongoDB is prepared! Loading members...')
        await self._load_members()
        log.info(f'Members are loaded. There are {len(self.members)} members already!')
        self.is_ready = True
