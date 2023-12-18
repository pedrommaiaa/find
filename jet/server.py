import asyncio
import logging
from io import BytesIO
from collections import namedtuple

logger = logging.getLogger(__name__)

class CommandError(Exception): 
    """Exception raised for errors in command execution."""
    pass

class Disconnect(Exception): 
    """Execption raised for client disconnection."""
    pass

class ProtocolError(Exception):
    """Exception raised for protocol-related errors."""
    pass

class CommandSyntaxError(CommandError):
    """Exception raised for command syntax errors."""
    pass  

Error = namedtuple('Error', ('message',))

class ProtocolHandler(object):
    def __init__(self):
        self.handlers = {
            '+': self.handle_simple_string,
            '$': self.handle_string,
            '*': self.handle_array
        }

    async def handle_request(self, reader, writer):
        try:
            first_byte = await reader.read(1)
            if not first_byte:
                raise Disconnect()
            
            decoded_byte = first_byte.decode()
            if decoded_byte not in self.handlers:
                raise ProtocolError('Invalid protocol message')
            return await self.handlers[first_byte.decode()](reader, writer)
        except Disconnect:
            raise
        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Unexpected error: {e}")
            raise ProtocolError('Unexpected server error')

    async def handle_simple_string(self, reader, writer):
        return (await self._read_and_decode(reader))

    async def handle_string(self, reader, writer):
        length = int(await self._read_and_decode(reader))
        if length == -1:
            return None
        string_data = await reader.read(length + 2)
        return string_data.decode()[:-2]

    async def handle_array(self, reader, writer):
        num_elements = int(await self._read_and_decode(reader))
        return [await self.handle_request(reader, writer) for _ in range(num_elements)]
    
    async def write_response(self, writer, data):
        buf = BytesIO()
        self._write(buf, data)
        writer.write(buf.getvalue())
        await writer.drain()

    async def _read_and_decode(self, reader):
        data = await reader.readline()
        return data.decode().rstrip('\r\n')

    def _write(self, buf, data):
        if isinstance(data, str):
            buf.write(f"+{data}\r\n".encode('utf-8'))
        elif isinstance(data, bytes):
            buf.write(f'${len(data)}\r\n{data}\r\n')
        elif isinstance(data, (list, tuple)):
            buf.write((f'*{len(data)}\r\n').encode('utf-8'))
            for item in data:
                self._write(buf, item)
        elif data is None:
            buf.write(b'$-1\r\n')
        else:
            raise CommandError(f'unrecognized type: {type(data)}')


class Server(object):
    def __init__(self, host='127.0.0.1', port=6379):
        self._kv = {}
        self.host = host
        self.port = port
        self._protocol = ProtocolHandler()
        self._commands = self.get_commands()

    def get_commands(self):
        return {
            'PING': lambda: 'PONG',
            'ECHO': lambda message: message
        }

    async def run(self, ready_event=None):
        server = await asyncio.start_server(self.connection_handler, self.host, self.port)

        if ready_event:
            ready_event.set()

        async with server:
            await server.serve_forever()

    async def get_response(self, data):
        try:
            if not isinstance(data, list):
                try:
                    data = data.split()
                except Exception as e:
                    raise CommandSyntaxError('Request must be list or simple string.')
            if not data:
                raise CommandSyntaxError('Missing command')

            command = data[0].upper()
            if command not in self._commands:
                raise CommandError(f'Unrecognized command: {command}')
            else:
                logger.debug(f'Received {command}')

            return self._commands[command](*data[1:])
        except CommandError as e:
            # Log and re-raise coommand-specific errors
            logger.error(f'Command error: {e}')
            raise

    async def connection_handler(self, reader, writer):
        address = writer.get_extra_info('peername')
        logger.info(f'Connection received: {address[0]}:{address[1]}')

        while True:
            try:
                data = await self._protocol.handle_request(reader, writer)
            except Disconnect:
                logger.info(f'Client went away: {address[0]}:{address[1]}')
                break
            except ProtocolError as e:
                logger.error(f'Protocol error: {e}')
                resp = Error(e.args[0])
                await self._protocol.write_response(writer, resp)
                continue

            try:
                resp = await self.get_response(data)
            except CommandError as exc:
                logger.exception('Command error')
                resp = Error(exc.args[0])

            await self._protocol.write_response(writer, resp)

        await writer.drain()
        writer.close()
        await writer.wait_closed()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(Server().run())