import time
from abc import ABC, abstractmethod

class Command(ABC):
    def __init__(self, args):
        self.args = args

    @abstractmethod
    def execute(self, writer):
        pass

class PingCommand(Command):
    def execute(self, writer):
        writer.write(b"+PONG\r\n")

class EchoCommand(Command):
    def execute(self, writer):
        message = self.args[0]
        writer.write(b"$" + str(len(message)).encode() + b"\r\n" + message + b"\r\n")

class SetCommand(Command):
    def __init__(self, args, store, expiry):
        super().__init__(args)
        self.store = store
        self.expiry = expiry
    
    def execute(self, writer):
        key, value = self.args[0], self.args[1]
        expiry = None
        if len(self.args) > 2:
            for i in range(2, len(self.args), 2):
                if self.args[i].lower() == b"px":
                    expiry = int(self.args[i + 1])
                    break
        self.store[key] = value
        if expiry:
            self.expiry[key] = time.time() * 1000 + expiry
        writer.write(b"+OK\r\n")

class GetCommand(Command):
    def __init__(self, args, store, expiry):
        super().__init__(args)
        self.store = store
        self.expiry = expiry
    
    def execute(self, writer):
        key = self.args[0]
        value = self.store.get(key)
        if value is not None and key not in self.expiry:
            writer.write(b"$" + str(len(value)).encode() + b"\r\n" + value + b"\r\n")
        elif key in self.expiry and self.expiry[key] > time.time() * 1000:
            writer.write(b"$" + str(len(value)).encode() + b"\r\n" + value + b"\r\n")
        else:
            if key in self.expiry:
                del self.store[key]
                del self.expiry[key]
            writer.write(b"$-1\r\n")

class CommandFactory:
    @staticmethod
    def get_command(command_name, args, store=None, expiry=None):
        if command_name.lower() == b"ping":
            return PingCommand(args)
        elif command_name.lower() == b"echo":
            return EchoCommand(args)
        elif command_name.lower() == b"set":
            return SetCommand(args, store, expiry)
        elif command_name.lower() == b"get":
            return GetCommand(args, store, expiry)
        return None