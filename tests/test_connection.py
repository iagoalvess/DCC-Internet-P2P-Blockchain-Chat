import asyncio
import pytest

from dcc_chat.connection import P2PNode


@pytest.mark.asyncio
async def test_node_bootstrap_connection():
    """
    Testa se um nó (node2) consegue se conectar a um nó bootstrap (node1)
    e se o node1 o reconhece corretamente.
    """
    node1 = P2PNode("127.0.0.1")
    node2 = P2PNode("127.0.0.2", bootstrap_ip="127.0.0.1")

    task1 = asyncio.create_task(node1.start())
    task2 = asyncio.create_task(node2.start())

    try:
        await asyncio.sleep(2)  # Tempo para conexão e identificação

        # Verificações
        async with node1.lock:
            assert "127.0.0.2" in node1.peers
        async with node2.lock:
            assert "127.0.0.1" in node2.peers

    finally:
        await node1.stop()
        await node2.stop()
        
        task1.cancel()
        task2.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task1
        with pytest.raises(asyncio.CancelledError):
            await task2


@pytest.mark.asyncio
async def test_three_node_discovery():
    """
    Testa um cenário com 3 nós para garantir a descoberta transitiva.
    """
    node1 = P2PNode("127.0.0.1")
    node2 = P2PNode("127.0.0.2", bootstrap_ip="127.0.0.1")
    node3 = P2PNode("127.0.0.3", bootstrap_ip="127.0.0.1")

    task1 = asyncio.create_task(node1.start())
    task2 = asyncio.create_task(node2.start())
    await asyncio.sleep(1)

    task3 = asyncio.create_task(node3.start())

    try:
        await asyncio.sleep(3)

        async with node3.lock:
            assert "127.0.0.1" in node3.peers
            assert "127.0.0.2" in node3.peers

        async with node2.lock:
            assert "127.0.0.3" in node2.peers

    finally:
        await node1.stop()
        await node2.stop()
        await node3.stop()

        task1.cancel()
        task2.cancel()
        task3.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task1
        with pytest.raises(asyncio.CancelledError):
            await task2
        with pytest.raises(asyncio.CancelledError):
            await task3
