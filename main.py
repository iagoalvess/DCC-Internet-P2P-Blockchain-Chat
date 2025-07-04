import sys
import asyncio
import socket
from dcc_chat.config import PORT
from dcc_chat.connection import P2PNode


async def resolve_hostname(hostname):
    """Resolve hostname to an IP address asynchronously."""
    loop = asyncio.get_running_loop()
    try:
        info = await loop.getaddrinfo(hostname, PORT)
        return info[0][4][0]
    except socket.gaierror as e:
        print(f"Erro ao resolver o hostname '{hostname}': {e}")
        return None


async def start_node(my_ip, bootstrap_ip):
    if bootstrap_ip and not bootstrap_ip[0].isdigit():
        resolved_ip = await resolve_hostname(bootstrap_ip)
        if resolved_ip is None:
            print("Encerrando o programa.")
            return 1
        bootstrap_ip = resolved_ip

    node = P2PNode(my_ip, bootstrap_ip)
    try:
        await node.start()
    except KeyboardInterrupt:
        print("\nNó encerrado pelo usuário.")
    return 0


def parse_args(argv):
    if len(argv) < 2:
        print("Uso: python main.py MEU_IP [BOOTSTRAP_IP]")
        return None
    my_ip = argv[1]
    bootstrap_ip = argv[2] if len(argv) > 2 else None
    return my_ip, bootstrap_ip


async def main(argv):
    args = parse_args(argv)
    if args is None:
        return 1
    my_ip, bootstrap_ip = args
    return await start_node(my_ip, bootstrap_ip)


if __name__ == "__main__":
    exit_code = asyncio.run(main(sys.argv))
    sys.exit(exit_code)
