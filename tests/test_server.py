import socket
import threading
from .utils import read_response, server

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