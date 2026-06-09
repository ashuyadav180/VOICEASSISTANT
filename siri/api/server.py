"""FastAPI Web Server for SIRI UI."""

import asyncio
import json
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

app = FastAPI(title="SIRI UI")

WEB_DIR = Path(__file__).parent.parent / "web"
WEB_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.get("/")
async def get_index():
    index_file = WEB_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>UI not built yet</h1>")
    return HTMLResponse(index_file.read_text(encoding="utf-8"))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        loop = getattr(app.state, "agent_loop", None)
        if loop:
            await websocket.send_json({"type": "state", "state": loop.state.value})
            
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                if payload.get("action") == "process_text":
                    text = payload.get("text")
                    if text and loop:
                        asyncio.create_task(loop.process_text(text))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def event_broadcaster():
    """Reads events from the loop's queue and broadcasts them."""
    loop = getattr(app.state, "agent_loop", None)
    if not loop:
        return
        
    loop.event_queue = asyncio.Queue()
    while True:
        try:
            event = await loop.event_queue.get()
            await manager.broadcast(event)
        except Exception as e:
            logger.error(f"Broadcaster error: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(event_broadcaster())
