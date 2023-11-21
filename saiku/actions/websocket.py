import asyncio
import json
from aiohttp import web
import socketio

class WebsocketAction:
    def __init__(self, agent):
        self.agent = agent
        self.name = "websocket_server"
        self.description = "Starts a websocket server for real-time communication with the agent."
        self.parameters = [
            {
                "name": "htmlContent",
                "description": "HTML content to be served on the root path",
                "required": True,
                "type": "string",
                "default": "<html><body><h1>Default HTML Content</h1></body></html>"
            }
        ]
        self.app = web.Application()
        self.sio = socketio.AsyncServer(cors_allowed_origins='*')
        self.sio.attach(self.app)

    async def emit_response(self, sid, result):
        await self.sio.emit('agent_response', result, to=sid)

    async def async_agent_interact(self, data):
        data_dict = json.loads(data)
        self.agent.messages = data_dict  # Update the agent's state with the parsed data    
        return await self.agent.interact(True)

    async def index(self, request):
        html_content = self.parameters[0]["default"]  # Default HTML content
        return web.Response(text=html_content, content_type='text/html')

    async def run(self, args):
        # Update HTML content if provided in args
        if "htmlContent" in args:
            self.parameters[0]["default"] = args["htmlContent"]

        self.app.router.add_get('/', self.index)

        @self.sio.event
        async def connect(sid, environ):
            print("A user connected", sid)

        @self.sio.event
        async def disconnect(sid):
            print("A user disconnected", sid)

        @self.sio.event
        async def agent_request(sid, data):
            print("Agent request received", data)
            result = await self.async_agent_interact(data)
            await self.emit_response(sid, result)

        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 3000)
        await site.start()
        print("Websocket server started at http://localhost:3000")
        while True:
            await asyncio.sleep(3600)  # Keeps the server running
        server_url = "Websocket server started at http://localhost:3000"
        print(server_url)
        return server_url
