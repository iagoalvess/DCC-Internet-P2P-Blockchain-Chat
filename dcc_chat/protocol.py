import binascii
import hashlib
import socket
import struct

# --- Códigos de Mensagem ---
IDENTIFY = 0x00
PEER_REQUEST = 0x1
PEER_LIST = 0x2
ARCHIVE_REQUEST = 0x3
ARCHIVE_RESPONSE = 0x4


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

def encode_archive_request():
    return struct.pack("!B", ARCHIVE_REQUEST)


def decode_archive_response(data: bytes) -> list[str]:
    """
    Decodifica o corpo de uma mensagem de arquivo.
    Espera-se que `data` contenha [N (4 bytes), IP1, ...].
    """

def encode_archive_response(chats: dict) -> bytes:
    parts = [struct.pack("!B", ARCHIVE_RESPONSE)]
    parts.append(struct.pack("!I", len(chats)))

    for chat in chats.values():
        parts.extend([chat["length"], chat["text"], chat["verification_code"], chat["md5"]])
    c = b''.join(parts)
    #print_encoded_archive_response_with_verification(c)
    return c

def print_encoded_archive_response_with_verification(encoded: bytes):
    offset = 0

    msg_type = struct.unpack("!B", encoded[offset:offset+1])[0]
    offset += 1
    print(f"📦 Tipo da mensagem: {msg_type} (esperado: 4)")

    count = struct.unpack("!I", encoded[offset:offset+4])[0]
    offset += 4
    print(f"📚 Número de chats: {count}")
    print("=" * 60)

    chats = {}

    for i in range(count):
        length = struct.unpack("!B", encoded[offset:offset+1])[0]
        offset += 1

        text = encoded[offset:offset+length].decode("ascii", errors="ignore")
        text_bytes = encoded[offset:offset+length]
        offset += length

        verification_code = encoded[offset:offset+16]
        offset += 16

        md5 = encoded[offset:offset+16]
        offset += 16

        chat = {
            "length": struct.pack("!B", length),
            "text": text_bytes,
            "verification_code": verification_code,
            "md5": md5,
        }
        chats[i] = chat

        print(f"📨 Chat #{i+1}")
        print(f"📝 Texto ({length} chars): {text}")
        print(f"🔒 Código de verificação: {binascii.hexlify(verification_code).decode()}")
        print(f"🧬 Hash MD5: {binascii.hexlify(md5).decode()}")

        if i == 0:
            print("✅ Primeiro chat (válido por definição)")
        else:
            range_start = max(0, i - 19)
            valid = verification_check2(chat, chats, range(range_start, i))
            print(f"🛡️  Verificação de integridade: {'✔️ Válido' if valid else '❌ Inválido'}")
            print(f"📍 Usou os chats de {range_start + 1} até {i}")
        print("-" * 60)

def verification_check2(chat, chats_before, range):
    
    bytes_s = b''
    for i in range:
        bytes_s += b''.join(chats_before[i].values())
    
    md5 = b'\x11' * 16
    message = chat["length"] + chat["text"] + chat["verification_code"]
    S = bytes_s + message
    md5 = hashlib.md5(S).digest()
    return True if chat["md5"] == md5 else False