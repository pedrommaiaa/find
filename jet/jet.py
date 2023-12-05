import asyncio
from abc import ABC, abstractmethod

class Command(ABC):
    def __init__(self, args):
        self.args = args

    @abstractmethod
    def execute(self, writer):
        pass

class PingCommand(Command):
    def execute(self, writer):
        writer.write(b"+PONG\r\n")

class CommandFactory:
    @staticmethod
    def get_command(command_name, args):
        if command_name.lower() == b"ping":
            return PingCommand(args)
        return None

class CommandParser:
    def __init__(self):
        self.buffer = b""

    def add_data(self, data):
        self.buffer += data

    def has_command(self):
        return b"\r\n" in self.buffer

    def parse_command(self):
        if not self.buffer:
            return None
        
        lines = self.buffer.split(b"\r\n")
        if lines[0].startswith(b"*"):
            num_args = int(lines[0][1:])
            command_parts = []
            idx = 1

            while num_args > 0 and idx < len(lines):
                if lines[idx].startswith(b"$"):
                    length = int(lines[idx][1:])
                    idx += 1
                    if idx < len(lines):
                        bulk_string = lines[idx]
                        if len(bulk_string) != length:
                            return None
                        command_parts.append(bulk_string)
                        idx += 1
                    else:
                        return None
                else:
                    return None
                num_args -= 1
            
            self.buffer = b"\r\n".join(lines[idx:])
            return command_parts
        return None

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
                    command = CommandFactory.get_command(command_name, command_parts)
                    if command:
                        command.execute(writer)
                    else:
                        writer.write(b"-ERR unkown command\r\n")
                    await writer.drain()

        writer.close()
        await writer.wait_closed()

    async def run(self, ready_event=None):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)

        if ready_event:
            ready_event.set()

        async with server:
            await server.serve_forever()
