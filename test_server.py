import socket
import pytest
import threading
from multiprocessing import Process, Event
from server import run_server

def read_response(client, expected_response, buffer_size=1024):
    total_data = []
    data = b''
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
    server_process = Process(target=run_server, args=(ready_event,), daemon=True)
    server_process.start()
    ready_event.wait()
    yield
    server_process.terminate()
    server_process.join(timeout=1)
    if server_process.is_alive():
        print("Server thread did not terminate. There might be a resource leak!")

def test_ping_response(server):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6379))
    try:
        client.sendall(b"*1\r\n$4\r\nPING\r\n")
        response = read_response(client, b"+PONG\r\n")
        assert response == b"+PONG\r\n", f"Expected '+PONG\\r\\n', got '{response.decode()}'"
    finally:
        client.close()

def test_multiple_ping_response(server):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6379))
    try:
        client.sendall(b"*1\r\n$4\r\nPING\r\n*1\r\n$4\r\nPING\r\n")
        response = read_response(client, b"+PONG\r\n+PONG\r\n")
        assert response == b"+PONG\r\n+PONG\r\n", f"Expected '+PONG\\r\\n+PONG\\r\\n', got '{response.decode()}'"
    finally:
        client.close()

def test_concurrent_clients(server):
    def client_thread():
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 6379))
        try:
            client.sendall(b"*1\r\n$4\r\nPING\r\n")
            response = read_response(client, b"+PONG\r\n")
            assert response == b"+PONG\r\n", f"Expected '+PONG\\r\\n', got '{response.decode()}'"
        finally:
            client.close()

    threads = [threading.Thread(target=client_thread) for _ in range(10)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()