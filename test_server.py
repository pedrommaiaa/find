import socket
import pytest
import threading
from server import main as start_server

@pytest.fixture(scope="module")
def server():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    yield

def test_ping_response(server):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6379))
    try:
        client.sendall(b"*1\r\n$4\r\nPING\r\n")
        response = client.recv(1024)
        assert response == b"+PONG\r\n", f"Expected '+PONG\\r\\n', got '{response.decode()}'"
    finally:
        client.close()
