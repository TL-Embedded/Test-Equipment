import socket


class SCPI():
    def __init__(self):
        self.is_binary_safe = False

    def write(self, command: str):
        self.write_bytes((command + "\n").encode())

    def read(self) -> str:
        return self.read_bytes().decode().strip()
    
    def query(self, command: str) -> str:
        self.write(command)
        return self.read()
    
    def get_idn(self) -> str:
        return self.query("*IDN?")

    def write_bytes(self, command: bytes):
        raise NotImplementedError()
    
    def read_bytes(self) -> bytes:
        raise NotImplementedError()
    
    def close(self):
        raise NotImplementedError()


class SerialSCPI(SCPI):
    def __init__(self, path: str, baud: int):
        import serial # pip install pyserial
        self._port = serial.Serial(path, baud)
        self._port.timeout = 1.0

    def write_bytes(self, command: bytes):
        self._port.write(command)

    def read_bytes(self) -> bytes:
        return self._port.read_until(b"\n")

    def close(self):
        self._port.close()


class SocketSCPI(SCPI):
    def __init__(self, address, port, is_tcp = True):
        socket_type = socket.SOCK_STREAM if is_tcp else socket.SOCK_DGRAM
        self.is_tcp = is_tcp
        self._socket = socket.socket(socket.AF_INET, socket_type)
        if is_tcp:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        else:
            self._socket.bind(("0.0.0.0", port))
        self._socket.settimeout(1.0)
        self._socket.connect((address, port))

    def read_bytes(self) -> bytes:
        payload = self._socket.recv(1024)
        while not payload.endswith(b"\n"):
            payload += self._socket.recv(1024)
        return payload[:-1]
    
    def write_bytes(self, command: bytes):
        self._socket.send(command)

    def close(self):
        if self.is_tcp:
            self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()


class VXISCPI(SCPI):
    def __init__(self, address: str):
        import vxi11 # pip install python-vxi11
        self._inst = vxi11.Instrument(address)
        self.is_binary_safe = True

    def write_bytes(self, command: bytes):
        self._inst.write_raw(command)

    def read_bytes(self) -> bytes:
        return self._inst.read_raw()

    def close(self):
        self._inst.close()


def from_uri(uri: str, baud: int = 9600, port: int = 5025, is_tcp: bool = True) -> SCPI:
    
    if type(uri) != str:
        # assume the given object was already a scpi object
        return uri

    components = uri.split(":")
    scheme = components[0]
    address = components[1]
    args = components[2] if len(components) > 2 else None

    if scheme == "tty":
        if args:
            baud = int(args)
        return SerialSCPI(address, baud)
    
    if scheme == "vxi":
        # Args are discarded
        address = address.removeprefix("//")
        return VXISCPI(address)

    if scheme in ["udp", "tcp", "ip"]:
        address = address.removeprefix("//")
        if args:
            port = int(args)
        if scheme != "ip":
            # scheme == ip autoselects 
            is_tcp = scheme == "tcp"
        return SocketSCPI(address, port, is_tcp)
    
    else:
        raise Exception("uri scheme not recognised")

