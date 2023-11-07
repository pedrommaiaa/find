import socket

def main():
    server = socket.create_server(("localhost", 6379), reuse_port=True)
    
    conn, addr = server.accept()
    print(f"Accepted new connection from {addr}")

    buffer = b""
    while True:
        data = conn.recv(1024)
        if not data:
            break
        
        buffer += data

        if b"\r\n" in buffer:
            lines = buffer.split(b"\r\n")

            if lines[0] == b"*1" and lines[1] == b"$4" and lines[2].lower() == b"ping":
                conn.sendall(b"+PONG\r\n")
                break
            
            buffer = lines[-1]
    
    conn.close()
    server.close()

if __name__ == "__main__":
    main()
