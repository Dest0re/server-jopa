from aiohttp import web
import destlogger

log = destlogger.Logger(debug_mode=True)


class ServerSide:
    def __init__(self, server_data, loop, client):
        self.sd = server_data
        self.loop = loop
        self.client = client
        self.utils = self.client.utils

        self.app = web.Application()
        self.app.add_routes([web.get('/chnick', self.chnick)])
        self.app.add_routes([web.get('/getMemberProfile', self.get_member_profile)])

    async def get_member_profile(self, request):
        query = request.query
        if query:
            if 'member_id' in query:
                member_id = int(query['id'])
                if member_id in self.client.db:
                    db_member = self.client.db.get_member(member_id)
                    return web.json_response(await db_member.json())
                else:
                    return web.Response(status=400)
            else:
                return web.Response(status=400)
        else:
            return web.Response(status=400)

    async def chnick(self, request):
        query = request.query
        member = self.client.GUILD.get_member(int(query['member_id']))
        await self.utils.set_nick(member)
        return web.Response(text=member.nick)

    async def run(self, *args, **kwargs):
        log.info("Server started")

        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.sd.URL, self.sd.PORT)
        await site.start()
