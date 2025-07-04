import asyncio
import binascii
from functools import reduce
import hashlib
import struct
import os
from dcc_chat.config import PEER_REQUEST_INTERVAL
from dcc_chat.protocol import encode_archive_request, encode_archive_response, encode_peer_request


async def send_message( writer: asyncio.StreamWriter, message: bytes):
        try:
            writer.write(message)
            await writer.drain()
        except (ConnectionResetError, BrokenPipeError) as e:
            peer_ip = "desconhecido"
            try:
                peer_ip = writer.get_extra_info("peername")
            except:
                pass
            print(f"Não foi possível enviar mensagem para {peer_ip}: {e}")

async def send_peer_request(writer: asyncio.StreamWriter):
        print(f'===> SEND PEER_REQUEST to {writer.get_extra_info("peername")}')
        await send_message(writer, encode_peer_request())

async def send_archive_request(writer: asyncio.StreamWriter):
        print('===> SEND ARCIVE_REQUEST')
        await send_message(writer, encode_archive_request())

async def periodic_requests(p2PNode):
        while True:
            await asyncio.sleep(PEER_REQUEST_INTERVAL)
            async with p2PNode.lock:
                if not p2PNode.peers:
                    continue
                peer_writers = list(p2PNode.peers.values())

            for writer in peer_writers:
                await send_peer_request(writer)
                await send_archive_request(writer)
    
async def send_archive_response(chats, writer:asyncio.StreamWriter):
        #print(f'===> ARCHIVE RESPONSE to {writer.get_extra_info('peername')}')
        response = encode_archive_response(chats)
        await send_message(writer, response)
        
async def recive_archive_response(p2PNode, reader:asyncio.StreamReader):
        count_chats_bytes = await reader.readexactly(4)
        count_chats = struct.unpack("!I",count_chats_bytes)[0]
        chats = {}
        for i in range(0, count_chats):
            count_character_byte = await reader.readexactly(1)
            count_character = struct.unpack("!B",count_character_byte)[0]
            text_bytes =  await reader.readexactly(count_character)
            verification_code = await reader.readexactly(16)
            md5 = await reader.readexactly(16)
            chat = {"length":count_character_byte, "text": text_bytes, 
                    "verification_code": verification_code, "md5": md5}
            chats[i] = chat
        for idx, chat in enumerate(chats.values()):
            if idx == 0:
                continue
            index_before = idx - 19 if idx - 19 > 0 else 0
            if verification_check(chat, chats ,range(index_before,idx)) == False:
                return
        print_chats(chats, '')
        p2PNode.chats = chats
            
async def put_chat_in_queue(chats, text):
 
    if len(text) > 255:
        raise ValueError("Texto excede o limite de 255 caracteres.")

    bytes_s = b''
    recent_chats = list(chats.values())[-19:]
    for chat in recent_chats:
        bytes_s += chat["length"] + chat["text"] + chat["verification_code"] + chat["md5"]

   
    len_bytes = struct.pack("!B", len(text))
    text_bytes = text.encode("ascii")            


    while True:
        verification_code = os.urandom(16)      
        partial_chat = len_bytes + text_bytes + verification_code
        S = bytes_s + partial_chat
        md5 = hashlib.md5(S).digest()

        if md5.startswith(b'\x00\x00'):
            break 
    chat = {
        "length": len_bytes,
        "text": text_bytes,
        "verification_code": verification_code,
        "md5": md5
    }
    chats[len(chats)] = chat
    encode_archive_response(chats)
    
async def send_to_chats_to_all_peers(p2PNode):
    async with p2PNode.lock:
        if not p2PNode.peers:
            return
        peer_writers = list(p2PNode.peers.values())
    for writer in peer_writers:
        await send_archive_response(p2PNode.chats,writer)
        
def verification_check(chat, chats_before, range):
    
    bytes_s = b''
    for i in range:
        bytes_s += b''.join(chats_before[i].values())
    
    md5 = b'\x11' * 16
    message = chat["length"] + chat["text"] + chat["verification_code"]
    S = bytes_s + message
    md5 = hashlib.md5(S).digest()
    return True if chat["md5"] == md5 else False

  
def print_chats(chats: dict, st):
    print("="*60)
    print(f"{'Histórico de Chats':^60} {st}")
    print("="*60)

    if not chats:
        print("Nenhum chat disponível.")
        return

    for idx, chat in enumerate(chats.values(), start=1):
        # if(idx < len(chats)):
        #     continue
        # Garante que 'text' está como string
        text = chat["text"]
        if isinstance(text, bytes):
            text = text.decode("ascii", errors="ignore")

        verification_hex = binascii.hexlify(chat["verification_code"]).decode()
        md5_hex = binascii.hexlify(chat["md5"]).decode()

        print(f"📨 Chat #{idx} -- 📝 Texto ({int.from_bytes(chat['length'], byteorder='big')} chars): {text}")
        print(f"🔒 Código de verificação: {verification_hex}")
        print(f"🧬 Hash MD5: {md5_hex}")
        print("-"*60)