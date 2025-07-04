import socket
import struct

# --- Códigos de Mensagem ---
IDENTIFY = 0x00
PEER_REQUEST = 0x1
PEER_LIST = 0x2
ARCHIVE_REQUEST = 0x3
ARCHIVE_RESPONSE = 0x4


def decode_identify(data: bytes) -> str:
    """Decodifica o IP de uma mensagem de identificação."""
    return socket.inet_ntoa(data)


def encode_peer_request():
    """Codifica uma mensagem PeerRequest. Formato: [0x1]"""
    return struct.pack("!B", PEER_REQUEST)


def encode_peer_list(peers: list[str]):
    """
    Codifica uma lista de pares.
    Formato: [0x2, N (4 bytes), IP1 (4 bytes), ..., IPN (4 bytes)]
    """
    encoded = struct.pack("!B", PEER_LIST)
    encoded += struct.pack("!I", len(peers))
    for ip in peers:
        encoded += socket.inet_aton(ip)
    return encoded


def decode_peer_list(data: bytes) -> list[str]:
    """
    Decodifica o corpo de uma mensagem PeerList.
    Espera-se que `data` contenha [N (4 bytes), IP1, ...].
    """
    count = struct.unpack("!I", data[0:4])[0]
    peers = []
    offset = 4
    for _ in range(count):
        ip_bytes = data[offset : offset + 4]
        peers.append(socket.inet_ntoa(ip_bytes))
        offset += 4
    return peers

def encode_archive_request():
    return struct.pack("!B", ARCHIVE_REQUEST)


def encode_archive_response(chats: dict) -> bytes:
    parts = [struct.pack("!B", ARCHIVE_RESPONSE)]
    parts.append(struct.pack("!I", len(chats)))

    for chat in chats.values():
        parts.extend([chat["length"], chat["text"], chat["verification_code"], chat["md5"]])
    c = b''.join(parts)
    
    return c