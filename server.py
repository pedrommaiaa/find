import socket

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

        while b"\r\n" in buffer:
            command, buffer = read_command(buffer)
            if command is not None:
                if command == b"ping":
                    conn.sendall(b"+PONG\r\n")
                else:
                    conn.sendall(b"-ERR unkown command\r\n")
                    buffer = b""

    conn.close()
    server.close()

if __name__ == "__main__":
    main()
