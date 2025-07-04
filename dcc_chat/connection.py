import asyncio
import struct

from dcc_chat.messages import (
    periodic_requests,
    recive_archive_response,
    send_archive_request,
    send_archive_response,
    send_message,
    send_peer_request,
)
from dcc_chat.protocol import (
    decode_identify,
    encode_peer_list,
    decode_peer_list,
    IDENTIFY,
    PEER_REQUEST,
    PEER_LIST,
    ARCHIVE_REQUEST,
    ARCHIVE_RESPONSE,
)
from dcc_chat.config import PORT, PEER_COUNT_SIZE, IP_SIZE, HEADER_SIZE


class P2PNode:
    def __init__(self, my_ip, bootstrap_ip=None):
        self.my_ip = my_ip
        self.bootstrap_ip = bootstrap_ip
        self.peers = {}
        self.lock = asyncio.Lock()
        self.server = None
        self.background_tasks = set()
        self.chats = {}

        self._message_handlers = {
            PEER_REQUEST: self._handle_peer_request,
            PEER_LIST: self._handle_peer_list,
            ARCHIVE_REQUEST: self._handle_archive_request,
            ARCHIVE_RESPONSE: self._handle_archive_response,
        }

    async def _handle_peer_request(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Manipula uma requisição de lista de pares."""
        async with self.lock:
            response = encode_peer_list(list(self.peers.keys()))
        await send_message(writer, response)

    async def _handle_peer_list(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Manipula o recebimento de uma lista de pares."""
        count_data = await reader.readexactly(PEER_COUNT_SIZE)
        count = struct.unpack("!I", count_data)[0]
        if count > 0:
            body = await reader.readexactly(count * IP_SIZE)
            new_peers = decode_peer_list(count_data + body)
            for new_ip in new_peers:
                """
                Em geral, não dá para conectar diretamente aos peers do TP
                porque todos estão atrás do NAT, bloqueando conexões
                externas. Por isso, o código está comentado.
                """
                # self._create_task(self.connect_to_peer(new_ip))
                print(f"NÃO CONECTADO COM O {new_ip} POR CAUSA DO NAT")

    async def _handle_archive_request(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Manipula uma requisição de histórico de chat."""
        await send_archive_response(self.chats, writer)

    async def _handle_archive_response(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Manipula o recebimento de um histórico de chat."""
        await recive_archive_response(self, reader)

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
            print(f"Servidor iniciado em {self.my_ip}:{PORT}")
        except OSError as e:
            print(f"Erro ao iniciar o servidor: {e}")
            return

        self._create_task(periodic_requests(self))

        if self.bootstrap_ip:
            self._create_task(self.connect_to_peer(self.bootstrap_ip))

        async with self.server:
            await self.server.serve_forever()

    async def connect_to_peer(self, ip: str):
        """Conecta, se identifica e inicia a escuta a um par."""
        async with self.lock:
            if ip == self.my_ip or ip in self.peers:
                return

        try:
            reader, writer = await asyncio.open_connection(ip, PORT)

            async with self.lock:
                self.peers[ip] = writer

            await send_peer_request(writer)
            await send_archive_request(writer)
            self._create_task(self.listen_to_peer(ip, reader, writer))

        except Exception as e:
            print(f"Falha ao conectar a {ip}: {e}")

            async with self.lock:
                if ip in self.peers:
                    del self.peers[ip]

    async def handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Recebe uma conexão, aguarda identificação e inicia a escuta."""
        peer_ip = None
        try:
            header = await reader.readexactly(HEADER_SIZE)
            if header[0] == IDENTIFY:
                ip_data = await reader.readexactly(IP_SIZE)
                peer_ip = decode_identify(ip_data)
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
                print(f"Conexão duplicada de {peer_ip}. Rejeitando.")
                writer.close()
                await writer.wait_closed()
                return
            self.peers[peer_ip] = writer

        await self.listen_to_peer(peer_ip, reader, writer)

    async def listen_to_peer(
        self, ip: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Loop para processar mensagens usando o dispatcher."""
        try:
            while True:
                msg_type_byte = await reader.readexactly(HEADER_SIZE)
                msg_type = struct.unpack("!B", msg_type_byte)[0]

                handler = self._message_handlers.get(msg_type)

                if handler:
                    await handler(reader, writer)

        except (
            asyncio.IncompleteReadError,
            ConnectionResetError,
            BrokenPipeError,
        ) as e:
            print(f"Conexão com {ip} perdida. Razão: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            async with self.lock:
                if ip in self.peers:
                    del self.peers[ip]
                    print(f"Par {ip} removido da lista.")
