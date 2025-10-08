import asyncio
import json
from typing import AsyncGenerator
from sse_starlette.sse import EventSourceResponse


class SSEManager:
    def __init__(self):
        self.connections: dict[int, list[asyncio.Queue]] = {}
    
    async def connect(self, session_id: int) -> asyncio.Queue:
        """Create a new SSE connection for a session"""
        queue = asyncio.Queue()
        if session_id not in self.connections:
            self.connections[session_id] = []
        self.connections[session_id].append(queue)
        print(f"✅ SSE: Client connected to session {session_id}. Total connections: {sum(len(v) for v in self.connections.values())}")
        print(f"   Connections by session: {[(k, len(v)) for k, v in self.connections.items()]}")
        return queue
    
    def disconnect(self, session_id: int, queue: asyncio.Queue):
        """Remove an SSE connection"""
        if session_id in self.connections:
            if queue in self.connections[session_id]:
                self.connections[session_id].remove(queue)
            if not self.connections[session_id]:
                del self.connections[session_id]
    
    async def broadcast(self, session_id: int, data: dict):
        """Broadcast data to all connections for a session"""
        if session_id in self.connections:
            dead_queues = []
            for queue in self.connections[session_id]:
                try:
                    await queue.put(data)
                except:
                    dead_queues.append(queue)
            
            # Clean up dead queues
            for queue in dead_queues:
                self.disconnect(session_id, queue)
    
    async def broadcast_all(self, data: dict):
        """Broadcast to all sessions"""
        print(f"📡 SSE: Broadcasting to all sessions. Event: {data.get('event', 'unknown')}")
        print(f"   Active sessions: {list(self.connections.keys())}")
        print(f"   Total clients: {sum(len(v) for v in self.connections.values())}")
        
        if not self.connections:
            print("⚠️  WARNING: No SSE clients connected!")
            return
            
        for session_id in list(self.connections.keys()):
            await self.broadcast(session_id, data)
            print(f"   ✓ Broadcasted to session {session_id}")


# Global SSE manager instance
sse_manager = SSEManager()


async def event_generator(queue: asyncio.Queue) -> AsyncGenerator[dict, None]:
    """Generate SSE events from queue"""
    try:
        while True:
            # Send heartbeat every 15 seconds to keep connection alive
            try:
                data = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield data
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                yield {
                    "event": "ping",
                    "data": json.dumps({"type": "ping"})
                }
    except asyncio.CancelledError:
        pass
