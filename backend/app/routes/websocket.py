from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and register a WebSocket connection for a user."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected for user {user_id}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending WebSocket message to {user_id}: {e}")
                self.disconnect(user_id)

    async def broadcast(self, message: dict):
        """Send message to all connected users."""
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {user_id}: {e}")


manager = ConnectionManager()


@router.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time updates.

    ## Authentication (two supported methods during migration)

    ### Method 1 — Query string (legacy, still supported)
    Connect with the token as a query parameter:
        ws://host/ws/updates?token=<your_access_token>

    ### Method 2 — First message auth (preferred)
    Connect without a token, then send a JSON auth message as the
    first message after the connection is established:
        {"type": "auth", "token": "<your_access_token>"}

    The server will respond with:
        {"type": "auth_success", "user_id": "<user_id>"}

    If authentication fails the connection is closed with code 4001.

    ## Ping / Pong
    Send {"type": "ping"} to receive {"type": "pong"} for keep-alive.
    """
    from app.services.auth import verify_access_token

    user_id = None

    # ── Method 1: query-string token (backward compat) ────────────────────────
    if token:
        try:
            user_id = await verify_access_token(token)
        except Exception as e:
            logger.error(f"WebSocket query-string auth failed: {e}")

        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return

        await manager.connect(websocket, user_id)

    else:
        # ── Method 2: first-message auth (preferred) ──────────────────────────
        await websocket.accept()
        try:
            raw = await websocket.receive_text()
            message = json.loads(raw)
        except Exception:
            await websocket.close(code=4001, reason="Expected JSON auth message")
            return

        if message.get("type") != "auth" or not message.get("token"):
            await websocket.close(code=4001, reason="First message must be an auth message")
            return

        try:
            user_id = await verify_access_token(message["token"])
        except Exception as e:
            logger.error(f"WebSocket first-message auth failed: {e}")

        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return

        # Register via manager (not direct mutation)
        manager.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected (first-message auth) for user {user_id}")
        await websocket.send_json({"type": "auth_success", "user_id": user_id})

    # ── Main message loop ─────────────────────────────────────────────────────
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)
