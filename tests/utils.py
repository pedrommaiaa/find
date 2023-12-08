import pytest
import asyncio
from jet.server import Server
from multiprocessing import Process, Event

def start_server(ready_event):
    server = Server()
    asyncio.run(server.run(ready_event))

def read_response(client, expected_response, buffer_size=1024):
    total_data = []
    while True:
        data = client.recv(buffer_size)
        if not data:
            break
        total_data.append(data)
        if b''.join(total_data).endswith(expected_response):
            break
    return b''.join(total_data)

@pytest.fixture(scope="function")
def server():
    ready_event = Event()
    server_process = Process(target=start_server, args=(ready_event,), daemon=True)
    server_process.start()
    ready_event.wait()
    yield
    server_process.terminate()
    server_process.join(timeout=1)
    if server_process.is_alive():
        print("Server thread did not terminate. There might be a resource leak!")