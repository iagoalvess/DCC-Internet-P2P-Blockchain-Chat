import struct

from dcc_chat.protocol import (
    encode_identify,
    decode_identify,
    encode_peer_request,
    encode_peer_list,
    decode_peer_list,
    IDENTIFY,
    PEER_REQUEST,
    PEER_LIST,
)


def test_encode_decode_identify():
    """Testa a codificação e decodificação da mensagem de identificação."""
    ip = "127.0.0.1"
    encoded_msg = encode_identify(ip)

    # Verifica o formato: [0x00, IP]
    assert encoded_msg[0] == IDENTIFY
    assert len(encoded_msg) == 5

    # Decodifica apenas o payload (após o byte de tipo)
    decoded_ip = decode_identify(encoded_msg[1:])
    assert decoded_ip == ip


def test_encode_peer_request():
    """Testa se a mensagem de requisição de pares é codificada corretamente."""
    assert encode_peer_request() == struct.pack("!B", PEER_REQUEST)


def test_encode_decode_peer_list():
    """Testa a codificação e decodificação da lista de pares (round-trip)."""
    peers = ["192.168.0.1", "10.0.0.5", "127.0.0.1"]
    encoded = encode_peer_list(peers)

    # Verifica o byte de tipo da mensagem
    assert encoded[0] == PEER_LIST

    # Verifica se o número de pares no cabeçalho está correto
    count = struct.unpack("!I", encoded[1:5])[0]
    assert count == len(peers)

    # Decodifica apenas o payload da mensagem
    decoded = decode_peer_list(encoded[1:])

    assert decoded == peers


def test_decode_empty_peer_list():
    """Testa o comportamento com uma lista de pares vazia."""
    peers = []
    encoded = encode_peer_list(peers)
    decoded = decode_peer_list(encoded[1:])
    assert decoded == []
