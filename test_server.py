import socket
import pytest
from multiprocessing import Process, Event
from server import main as start_server

@pytest.fixture(scope="function")
def server():
    ready_event = Event()
    server_process = Process(target=start_server, args=(ready_event,), daemon=True)
    server_process.start()    
    ready_event.wait()
    yield
    server_process.terminate()
    # Give the server thread time to exit cleanly
    server_process.join(timeout=1)
    if server_process.is_alive():
        print("Server thread did not terminate. There might be a resource leak!")

def test_ping_response(server):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6379))
    try:
        client.sendall(b"*1\r\n$4\r\nPING\r\n")
        response = client.recv(1024)
        assert response == b"+PONG\r\n", f"Expected '+PONG\\r\\n', got '{response.decode()}'"
    finally:
        client.close()

def test_multiple_ping_response(server):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6379))
    try:
        client.sendall(b"*1\r\n$4\r\nPING\r\n*1\r\n$4\r\nPING\r\n")
        response = client.recv(1024)
        assert response == b"+PONG\r\n+PONG\r\n", f"Expected '+PONG\\r\\n+PONG\\r\\n', got '{response.decode()}'"
    finally:
        client.close()