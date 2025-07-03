import sys
import asyncio
from dcc_chat.config import PORT
from dcc_chat.connection import P2PNode

async def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py MEU_IP [BOOTSTRAP_IP]")
        sys.exit(1)

    my_ip = sys.argv[1]
    bootstrap_ip = sys.argv[2] if len(sys.argv) > 2 else None
    if str.isdigit(bootstrap_ip[0]) == False: 
        loop = asyncio.get_running_loop()
        bootstrap_ip = await loop.getaddrinfo(bootstrap_ip, PORT)
        bootstrap_ip = bootstrap_ip[0][4][0]
    
    node = P2PNode(my_ip, bootstrap_ip)
    try:
        await node.start()
    except KeyboardInterrupt:
        print("\nNó encerrado pelo usuário.")

if __name__ == "__main__":
     asyncio.run(main())