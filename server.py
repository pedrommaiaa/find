import asyncio

async def handle_client(reader, writer):
    buffer = b""
    while True:
        data = await reader.read(1024)
        if not data:
            break
        
        buffer += data

        while b"\r\n" in buffer:
            command, buffer = read_command(buffer)
            if command is not None:
                if command == b"ping":
                    writer.write(b"+PONG\r\n")
                else:
                    writer.write(b"-ERR unknown command\r\n")
                    buffer = b""
                await writer.drain()

    writer.close()
    await writer.wait_closed()


def read_command(buffer):
    if b"\r\n" in buffer:
        parts = buffer.split(b"\r\n", 1)
        if parts[0] == b"*1":
            length_command = parts[1].split(b"\r\n", 1)
            length = int(length_command[0].lstrip(b"$"))

            if len(length_command[1]) >= length + 2:
                command_data = length_command[1][:length].lower()
                remaining_buffer = length_command[1][length + 2:]
                return command_data, remaining_buffer
            else:
                return None, buffer
        else:
            return None, b""
    else:
        return None, buffer

async def main(ready_event=None):
    server = await asyncio.start_server(handle_client, 'localhost', 6379)

    if ready_event:
        ready_event.set()
    
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
else:
    def run_server(ready_event):
        asyncio.run(main(ready_event))