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
