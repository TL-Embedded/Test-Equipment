import socket
import struct
import time
from typing import Callable


RECORD_A   = 0x0001
RECORD_TXT = 0x0010
RECORD_PTR = 0x000C
RECORD_SRV = 0x0021

FLAG_RESPONSE = 0x8000
FLAG_AUTHORITIVE = 0x0400

CLASS_IN = 0x0001
CLASS_UNICAST_REQ = 0x8000

MDNS_PORT  = 5353
MDNS_IP = "224.0.0.251"


def encode_name(name: str):
    buffer = b''
    for label in name.split('.'):
        buffer += struct.pack('B', len(label)) + label.encode()
    buffer += b'\x00'
    return buffer


def decode_name(buffer: bytes, offset: int = 0) -> tuple[str, int]:
    labels = []
    jumped = False

    while True:
        length = buffer[offset]
        offset += 1
        if length == 0:
            # End marker
            break
        if (length & 0xC0) == 0xC0:
            # Pointer compression
            if not jumped:
                end_offset = offset + 1
                jumped = True
            offset = ((length & 0x3F) << 8) | buffer[offset]
        else:
            # Regular label
            labels.append(buffer[offset:offset + length].decode())
            offset += length  # Move past the label
    
    if jumped:
        # Make sure we return the last decoded byte
        offset = end_offset
    return '.'.join(labels), offset


def encode_question(name: str, record_type: int):
    return encode_name(name) + struct.pack("!2H",
        record_type, # Type
        CLASS_IN | CLASS_UNICAST_REQ, # Class
    )


def decode_answer(packet: bytes, offset: int = 0) -> tuple[tuple[str, int, Callable[[], bytes]], int]:
    name, offset = decode_name(packet, offset)
    type, _, _, len = struct.unpack_from("!HHIH", packet, offset=offset)
    offset += 10
    decoder = lambda offset=offset: decode_answer_data(packet, offset, len, type)
    offset += len
    return (name, type, decoder), offset


def decode_answer_data(packet: bytes, offset: int, len: int, type: int) -> str:
    if type == RECORD_A:
        return ".".join(str(b) for b in packet[offset:offset+len])
    if type == RECORD_PTR:
        return decode_name(packet, offset)[0]
    if type == RECORD_SRV:
        return str(packet[offset:offset+len])
    return packet[offset:offset+len].decode()


def encode_mdns(questions: list[tuple[str, int]]):
    packet = struct.pack( "!6H",
        0, # Transaction ID
        0, # Flags
        len(questions), # Questions
        0, # Answers
        0, # Authorities
        0, # Additional question
    )
    for (name, type) in questions:
        packet += encode_question(name, type)
    return packet


def extract_mdns_answer(packet: bytes, name: str, type: int) -> str | None:
    try:
        _, flags, questions, answers, _, _ = struct.unpack_from("!6H", packet)
        # We are looking for answers only
        if questions or not (flags & FLAG_RESPONSE):
            return None
        
        offset = 12
        for _ in range(answers):
            (aname, atype, decoder), offset = decode_answer(packet, offset)
            if atype == type and (name == "*" or aname == name):
                return decoder()
        
    except struct.error:
        return None

class MDNS():
    def __init__(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        mreq = struct.pack('=4s4s', socket.inet_aton(MDNS_IP), socket.inet_aton('0.0.0.0'))
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        s.bind(('0.0.0.0', MDNS_PORT))
        self.socket = s

    def __del__(self):
        self.socket.close()

    def query(self, name: str, type: int, timeout: float = 1.0, limit: int = 100) -> list[str]:
        queries = [(name, type)]
        self.socket.sendto(encode_mdns(queries), (MDNS_IP, MDNS_PORT))
        return self._listen_for(name, type, timeout=timeout, limit=limit)

    def _listen_for(self, name: str, type: int, timeout: float = 1.0, limit: int = 100) -> list[str]:
        start = time.time()
        remaining = timeout
        results = []
        try:
            while remaining > 0 and len(results) < limit:
                self.socket.settimeout(remaining)
                data, addr = self.socket.recvfrom(4096)
                result = extract_mdns_answer(data, name, type)
                if result:
                    results.append(result)
                remaining = timeout - (time.time() - start)
        except TimeoutError:
            pass
        return results
        
    def resolve_hostname(self, hostname: str, timeout: float = 1.0) -> str:
        # Takes a hostname, ie, "name.local"
        return self.query(hostname, RECORD_A, timeout=timeout, limit=1)[0]
    
    def resolve_text(self, service_instance: str, timeout: float = 1.0) -> str:
        # Takes a service_instance, ie, "name._scpi-raw._tcp.local"
        return self.query(service_instance, RECORD_TXT, timeout=timeout, limit=1)[0]

    def list_all_service_types(self, timeout: float = 1.0, limit: int = 100) -> list[str]:
        return self.query("_services._dns-sd._udp.local", RECORD_PTR, timeout=timeout, limit=limit )
    
    def list_services_instances(self, service_type: str, timeout: float = 1.0, limit: int = 100) -> list[str]:
        # Takes a service_type, ie, "_scpi-raw._tcp.local"
        return self.query(service_type, RECORD_PTR, timeout=timeout, limit=limit)

if __name__ == "__main__":
    mdns = MDNS()
    for service_instance in mdns.list_services_instances("_scpi-raw._tcp.local"):
        print(service_instance)