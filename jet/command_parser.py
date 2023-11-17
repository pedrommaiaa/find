class CommandParser:
    def __init__(self):
        self.buffer = b""

    def add_data(self, data):
        self.buffer += data

    def has_command(self):
        return b"\r\n" in self.buffer

    def parse_command(self):
        if not self.buffer:
            return None
        
        lines = self.buffer.split(b"\r\n")
        if lines[0].startswith(b"*"):
            num_args = int(lines[0][1:])
            command_parts = []
            idx = 1

            while num_args > 0 and idx < len(lines):
                if lines[idx].startswith(b"$"):
                    length = int(lines[idx][1:])
                    idx += 1
                    if idx < len(lines):
                        bulk_string = lines[idx]
                        if len(bulk_string) != length:
                            return None
                        command_parts.append(bulk_string)
                        idx += 1
                    else:
                        return None
                else:
                    return None
                num_args -= 1
            
            self.buffer = b"\r\n".join(lines[idx:])
            return command_parts
        return None
