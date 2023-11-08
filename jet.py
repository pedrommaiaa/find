import asyncio
from multiprocessing import Event
from typing import Optional, Tuple, Union

class Jet:
    def __init__(self, host: str ='localhost', port: int =6379) -> None:
        self.host: str = host
        self.port: int = port
        self.buffer: bytes = b""

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            data: bytes = await reader.read(1024)
            if not data:
                break
            
            self.buffer += data

            while b"\r\n" in self.buffer:
                command: Optional[bytes] = self.read_command()
                if command is not None:
                    if command == b"ping":
                        writer.write(b"+PONG\r\n")
                    else:
                        writer.write(b"-ERR unknown command\r\n")
                        self.buffer = b""
                    await writer.drain()

        writer.close()
        await writer.wait_closed()


    def read_command(self) -> Optional[bytes]:
        if b"\r\n" in self.buffer:
            parts: Tuple[bytes, bytes] = self.buffer.split(b"\r\n", 1)
            if parts[0] == b"*1":
                length_command: Tuple[bytes, bytes] = parts[1].split(b"\r\n", 1)
                length: int = int(length_command[0].lstrip(b"$"))

                if len(length_command[1]) >= length + 2:
                    command_data: bytes = length_command[1][:length].lower()
                    self.buffer = length_command[1][length + 2:]
                    return command_data
                else:
                    return None
            else:
                self.buffer = b""
                return None
        else:
            return None
    
    async def run(self, ready_event: Optional[Union[asyncio.Event, Event]] = None) -> None:
        server: asyncio.AbstractServer = await asyncio.start_server(self.handle_client, self.host, self.port)
     
        if ready_event:
            ready_event.set()

        async with server:
            await server.serve_forever()            


if __name__ == "__main__":
    jet = Jet()
    asyncio.run(jet.run())