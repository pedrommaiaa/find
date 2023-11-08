import asyncio
from multiprocessing import Event

class Jet:
    def __init__(self, host='localhost', port=6379):
        self.host = host
        self.port = port
        self.buffer = b""

    async def handle_client(self, reader, writer):
        while True:
            data = await reader.read(1024)
            if not data:
                break
            
            self.buffer += data

            while b"\r\n" in self.buffer:
                command = self.read_command()
                if command is not None:
                    if command == b"ping":
                        writer.write(b"+PONG\r\n")
                    else:
                        writer.write(b"-ERR unknown command\r\n")
                        self.buffer = b""
                    await writer.drain()

        writer.close()
        await writer.wait_closed()


    def read_command(self):
        if b"\r\n" in self.buffer:
            parts = self.buffer.split(b"\r\n", 1)
            if parts[0] == b"*1":
                length_command = parts[1].split(b"\r\n", 1)
                length = int(length_command[0].lstrip(b"$"))

                if len(length_command[1]) >= length + 2:
                    command_data = length_command[1][:length].lower()
                    self.buffer = length_command[1][length + 2:]
                    return command_data
                else:
                    return None
            else:
                self.buffer = b""
                return None
        else:
            return None

    async def run(self, ready_event):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)

        if ready_event:
            ready_event.set()

        async with server:
            await server.serve_forever()            


if __name__ == "__main__":
    jet = Jet()
    asyncio.run(jet.run())