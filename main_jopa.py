import asyncio
import os
import dotenv

import destlogger

import server_jopa
import discord_jopa
import structures_jopa
import database_jopa

dotenv.load_dotenv()
config = database_jopa.load_json_config('./config.json')

DISCORD_BOT_TOKEN = os.getenv('DISCORD_TOKEN')
DB_PATH = config['db']['db_path']

NICK_HISTORY_LIMIT = config['discord_bot']['nick_history_limit']

guild_data = structures_jopa.GuildData(**config['guild'])
server_data = structures_jopa.ServerData(**config['server'])
global_settings = structures_jopa.GlobalSettings(NICK_HISTORY_LIMIT)

log = destlogger.Logger(debug_mode=config['debug_mode'], title=config['window_title'])


async def main():
    loop = asyncio.get_event_loop()

    db = database_jopa.DB(DB_PATH, global_settings, loop)
    await db.start()

    client = discord_jopa.Client(guild_data, db, loop=loop)
    server = server_jopa.ServerSide(server_data, loop, client)

    try:
        run_client = client.start(DISCORD_BOT_TOKEN)
        run_server = server.run()

        await asyncio.gather(run_client, run_server)
    finally:
        await client.logout()
        await db.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        exit()