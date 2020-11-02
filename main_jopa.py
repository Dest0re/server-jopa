import asyncio
import os
import dotenv

import destlogger
import discord

import server_jopa
import discord_jopa
import structures_jopa
import database_jopa

dotenv.load_dotenv()
config = database_jopa.load_json_config('./config.json')

DISCORD_BOT_TOKEN = os.getenv('DISCORD_TOKEN')

NICK_HISTORY_LIMIT = config['discord_bot']['nick_history_limit']

guild_data = structures_jopa.GuildData(**config['guild'])
db_data = structures_jopa.DBData(**config['db'])
server_data = structures_jopa.ServerData(**config['server'])
global_settings = structures_jopa.GlobalSettings(**config['global_settings'])

log = destlogger.Logger(debug_mode=config['debug_mode'], title=global_settings.WINDOW_TITLE)


async def main():
    loop = asyncio.get_event_loop()

    intents = discord.Intents.default()
    intents.members = True

    db = database_jopa.DB(db_data, global_settings, loop)
    await db.start()

    client = discord_jopa.Client(guild_data, db, intents=intents, loop=loop)
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
