import asyncio
import logging
from io import BytesIO
from collections import namedtuple

logger = logging.getLogger(__name__)

class CommandError(Exception): pass
class Disconnect(Exception): pass

Error = namedtuple('Error', ('message',))

class ProtocolHandler(object):
    def __init__(self):
        self.handlers = {
            '+': self.handle_simple_string,
            '$': self.handle_string,
            '*': self.handle_array
        }

    async def handle_request(self, reader, writer):
        first_byte = await reader.read(1)
        if not first_byte:
            raise Disconnect()

        try:
            return await self.handlers[first_byte.decode()](reader, writer)
        except KeyError:
            raise CommandError('bad request')

    async def handle_simple_string(self, reader, writer):
        return (await reader.readline()).decode().rstrip('\r\n')

    async def handle_string(self, reader, writer):
        length_line = await reader.readline()
        length = int(length_line.decode().rstrip('\r\n'))
        if length == -1:
            return None
        string_data = await reader.read(length + 2)
        return string_data.decode()[:-2]

    async def handle_array(self, reader, writer):
        num_elements_line = await reader.readline()
        num_elements = int(num_elements_line.decode().rstrip('\r\n'))
        return [await self.handle_request(reader, writer) for _ in range(num_elements)]
    
    async def write_response(self, writer, data):
        buf = BytesIO()
        self._write(buf, data)
        writer.write(buf.getvalue())
        await writer.drain()

    def _write(self, buf, data):
        if isinstance(data, str):
            buf.write(('+' + data + '\r\n').encode('utf-8'))
        elif isinstance(data, bytes):
            buf.write('$%d\r\n%s\r\n' % (len(data), data))
        elif isinstance(data, (list, tuple)):
            buf.write(('*%d\r\n' % len(data)).encode('utf-8'))
            for item in data:
                self._write(buf, item)
        elif data is None:
            buf.write(b'$-1\r\n')
        else:
            raise CommandError('unrecognized type: %s' % type(data))

class Server(object):
    def __init__(self, host='127.0.0.1', port=6379):
        self._protocol = ProtocolHandler()
        self._kv = {}
        self._commands = self.get_commands()
        self.host = host
        self.port = port

    def get_commands(self):
        return {
            'PING': lambda: 'PONG'
        }

    async def connection_handler(self, reader, writer):
        address = writer.get_extra_info('peername')
        logger.info('Connection received: %s:%s' % address)

        while True:
            try:
                data = await self._protocol.handle_request(reader, writer)
            except Disconnect:
                logger.info('Client went away: %s:%s' % address)
                break

            try:
                resp = await self.get_response(data)
            except CommandError as exc:
                logger.exception('Command error')
                resp = Error(exc.args[0])

            await self._protocol.write_response(writer, resp)

        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def run(self, ready_event=None):
        server = await asyncio.start_server(self.connection_handler, self.host, self.port)

        if ready_event:
            ready_event.set()

        async with server:
            await server.serve_forever()

    async def get_response(self, data):
        if not isinstance(data, list):
            try:
                data = data.split()
            except:
                raise CommandError('Request must be list or simple string.')

        if not data:
            raise CommandError('Missing command')

        command = data[0].upper()
        if command not in self._commands:
            raise CommandError('Unrecognized command: %s' % command)
        else:
            logger.debug('Received %s', command)

        return self._commands[command](*data[1:])

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(Server().run())