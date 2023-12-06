import socket
from .utils import read_response, server

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