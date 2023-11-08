import asyncio
from multiprocessing import Event

class Jet:
    def __init__(self, host='localhost', port=6379):
        self.store = {}
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
                    if command[0].lower() == b"ping":
                        writer.write(b"+PONG\r\n")
                    elif command[0].lower() == b"echo" and len(command) == 2:
                        message = command[1]
                        writer.write(b"$" + str(len(message)).encode() + b"\r\n" + message + b"\r\n")
                    elif command[0].lower() == b"set" and len(command) == 3:
                        key, value = command[1], command[2]
                        self.store[key] = value
                        writer.write(b"+OK\r\n")
                    elif command[0].lower() == b"get" and len(command) == 2:
                        key = command[1]
                        value = self.store.get(key)
                        if value is not None:
                            writer.write(b"$" + str(len(value)).encode() + b"\r\n" + value + b"\r\n")
                        else:
                            writer.write(b"$-1\r\n")
                    else:
                        writer.write(b"-ERR unknown command\r\n")
                    await writer.drain()

        writer.close()
        await writer.wait_closed()


    def read_command(self):
        if not self.buffer:
            return None
        
        lines = self.buffer.split(b"\r\n")
        if lines[0].startswith(b"*"):
            num_args = int(lines[0][1:])
            command_parts = []
            idx = 1

            while num_args > 0:
                if idx < len(lines) and lines[idx].startswith(b"$"):
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


    async def run(self, ready_event):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)

        if ready_event:
            ready_event.set()

        async with server:
            await server.serve_forever()            


if __name__ == "__main__":
    jet = Jet()
    asyncio.run(jet.run())