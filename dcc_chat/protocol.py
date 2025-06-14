import socket
import struct

# --- Códigos de Mensagem ---
IDENTIFY = 0x00
PEER_REQUEST = 0x1
PEER_LIST = 0x2


def encode_identify(ip: str):
    """Codifica uma mensagem de identificação. Formato: [0x00, IP (4 bytes)]"""
    encoded = struct.pack("!B", IDENTIFY)
    encoded += socket.inet_aton(ip)
    return encoded


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
