from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from backend.websocket.manager import manager
from backend.auth.jwt_handler import verify_access_token

router = APIRouter()

@router.websocket("/attendance/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    session_id: str,
    token: str = Query(None)
):
    # Basic token validation for websocket
    if not token:
        await websocket.close(code=1008)
        return
        
    payload = verify_access_token(token)
    if not payload:
        await websocket.close(code=1008)
        return
        
    await manager.connect(websocket, session_id)
    try:
        while True:
            # We don't expect messages from client, just keep connection open
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
