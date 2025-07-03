import asyncio
import struct
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
local_ip = s.getsockname()[0]

from dcc_chat.messages import print_chats, put_chat_in_queue, periodic_requests, recive_archive_response, send_archive_request, send_archive_response, send_message, send_peer_request, send_to_chats_to_all_peers, verification_check
from dcc_chat.protocol import (
    encode_archive_response,
    encode_identify,
    decode_identify,
    encode_peer_request,
    encode_peer_list,
    decode_peer_list,
    IDENTIFY,
    PEER_REQUEST,
    PEER_LIST,
    ARCHIVE_REQUEST,
    ARCHIVE_RESPONSE
)
from dcc_chat.config import PORT, PEER_REQUEST_INTERVAL

class P2PNode:
    def __init__(self, my_ip, bootstrap_ip=None):
        self.my_ip = my_ip
        self.bootstrap_ip = bootstrap_ip
        self.peers = {}
        self.lock = asyncio.Lock()
        self.server = None
        self.background_tasks = set()
        self.chats = {}
        self.a = 0

    def _create_task(self, coro):
        """Cria, rastreia e agenda a remoção de uma tarefa."""
        task = asyncio.create_task(coro)
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        return task

    async def start(self):
        """Inicia o servidor e as tarefas de background."""
        try:
            self.server = await asyncio.start_server(
                self.handle_connection, self.my_ip, PORT
            )
            print(f"Nó escutando em {self.my_ip}:{PORT}")
        except OSError as e:
            print(f"Erro ao iniciar o servidor: {e}")
            return

        self._create_task(periodic_requests(self))

        if self.bootstrap_ip:
            self._create_task(self.connect_to_peer(self.bootstrap_ip))

        async with self.server:
            await self.server.serve_forever()

    async def stop(self):
        print(f"Desligando o nó {self.my_ip}...")

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        for task in list(self.background_tasks):
            task.cancel()

        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)

        async with self.lock:
            for writer in self.peers.values():
                writer.close()
                try:
                    await writer.wait_closed()
                except (BrokenPipeError, ConnectionResetError):
                    pass 
            self.peers.clear()

        print(f"Nó {self.my_ip} desligado.")

    async def connect_to_peer(self, ip: str):
        """Conecta, se identifica e inicia a escuta a um par."""
        async with self.lock:
            if ip == self.my_ip or ip in self.peers:
                return

        print(f"Tentando conectar a {ip}...")
        try:
            reader, writer = await asyncio.open_connection(ip, PORT)

            async with self.lock:
                self.peers[ip] = writer

            await send_peer_request(writer)
            await send_archive_request(writer)
            self._create_task(self.listen_to_peer(ip, reader, writer))

        except Exception as e:
            print(f"Falha ao conectar a {ip}: {e}")

    async def handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Recebe uma conexão, aguarda identificação e inicia a escuta."""
        try:
            header = await reader.readexactly(1)
            if header[0] == IDENTIFY:
                ip_data = await reader.readexactly(4)
                peer_ip = decode_identify(ip_data)
                print(f"<- Conexão recebida e identificada de {peer_ip}")
            else:
                print("Conexão recebida sem identificação. Fechando.")
                writer.close()
                await writer.wait_closed()
                return
        except (asyncio.IncompleteReadError, ConnectionResetError) as e:
            print(f"Conexão perdida antes da identificação: {e}")
            return

        async with self.lock:
            if peer_ip in self.peers:
                writer.close()
                await writer.wait_closed()
                return
            self.peers[peer_ip] = writer

        await self.listen_to_peer(peer_ip, reader, writer)

    async def listen_to_peer(
        self, ip: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Loop para processar mensagens APÓS a identificação."""
        try:
            while True:
                msg_type_byte = await reader.readexactly(1)
                msg_type = struct.unpack("!B", msg_type_byte)[0]
                print(msg_type, 'vmsg_typemsg_typemsg_typemsg_typemsg_typemsg_typemsg_typemsg_typemsg_type')
                if msg_type == PEER_REQUEST:
                    print(f"===> Recebido PeerRequest de {ip}")
                    async with self.lock:
                        print(self.peers.keys(), 'self.peers.keys()')
                        response = encode_peer_list(list(self.peers.keys()))
                        print(f'enviado para {ip} ===> {response}')
                    await send_message(writer, response)
                    print(f"<==== Enviado PeerList para {ip}")

                elif msg_type == PEER_LIST:
                    print('===>recebido peerList msg')
                    count_data = await reader.readexactly(4)
                    count = struct.unpack("!I", count_data)[0]
                    if count > 0:
                        body = await reader.readexactly(count * 4)
                        new_peers = decode_peer_list(count_data + body)
                        print(
                            f"-> Recebido PeerList de {ip} com {count} pares: {new_peers}"
                        )
                        for new_ip in new_peers:
                            #self._create_task(self.connect_to_peer(new_ip))
                            print(f'NÂO CONECTADO COM O {new_ip} POR CAUSA DO NAT')
                    else:
                        print(f"-> Recebido PeerList de {ip} com 0 pares.")
                elif msg_type == ARCHIVE_REQUEST:
                    print('===> RECEBIDO ARCHIVE_REQUEST')
                    await send_archive_response(self.chats, writer)
                elif msg_type == ARCHIVE_RESPONSE:
                    print('===> RECEBIDO ARCHIVE_REPONSE')
                    await recive_archive_response(self,reader)
                    c = ['(^_^)', '(T_T)', '(O_O)', '(o_-)', '=^.^=']
                    if self.a < 1:
                        #await put_chat_in_queue(self.chats, f"Como se chama a pessoa que viu o Thor de perto? Vi-Thor.")
                        #await send_to_chats_to_all_peers(self)
                        self.a = self.a + 1

        except (
            asyncio.IncompleteReadError,
            ConnectionResetError,
            BrokenPipeError,
        ) as e:
            print(f"Conexão com {ip} perdida. Razão: {e}")
        finally:
            writer.close()
            async with self.lock:
                if ip in self.peers:
                    del self.peers[ip]
                    print(f"Par {ip} removido da lista.")

    