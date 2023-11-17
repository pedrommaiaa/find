import asyncio
from .commands import CommandFactory
from .command_parser import CommandParser

class Jet:
    def __init__(self, host='localhost', port=6379):
        self.store = {}
        self.expiry = {}
        self.host = host
        self.port = port

    async def handle_client(self, reader, writer):
        parser = CommandParser()
        while True:
            data = await reader.read(1024)
            if not data:
                break

            parser.add_data(data)

            while parser.has_command():
                command_parts = parser.parse_command()
                if command_parts:
                    command_name = command_parts.pop(0)
                    command = CommandFactory.get_command(command_name, command_parts, self.store, self.expiry)
                    if command:
                        command.execute(writer)
                    else:
                        writer.write(b"-ERR unkown command\r\n")
                    await writer.drain()

        writer.close()
        await writer.wait_closed()

    async def run(self, ready_event):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)

        if ready_event:
            ready_event.set()

        async with server:
            await server.serve_forever()            


if __name__ == "__main__":
    jet = Jet()
    asyncio.run(jet.run())
