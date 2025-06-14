import sys
import asyncio
from dcc_chat.connection import P2PNode

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python main.py MEU_IP [BOOTSTRAP_IP]")
        sys.exit(1)

    my_ip = sys.argv[1]
    bootstrap_ip = sys.argv[2] if len(sys.argv) > 2 else None

    node = P2PNode(my_ip, bootstrap_ip)
    try:
        asyncio.run(node.start())
    except KeyboardInterrupt:
        print("\nNó encerrado pelo usuário.")
