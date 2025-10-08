from fastapi import APIRouter, Depends, HTTPException, Query
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session
from .. import auth, models
from ..sse import sse_manager, event_generator
from ..database import get_db

router = APIRouter(prefix="/events", tags=["sse"])


@router.get("/stream")
async def stream_events(
    token: str = Query(None),
    session_id: int = None,
    db: Session = Depends(get_db)
):
    """
    SSE endpoint for real-time updates.
    Token can be passed as query parameter for EventSource compatibility.
    If session_id is provided, only events for that session are streamed.
    Otherwise, all events are streamed (for web panel).
    """
    # Verify token if provided
    if token:
        try:
            from ..auth import verify_token
            payload = verify_token(token)
            # Token is valid
        except Exception as e:
            print(f"SSE Token validation error: {str(e)}")
            raise HTTPException(status_code=403, detail=f"Invalid or expired token: {str(e)}")
    
    # For web panel, use session_id = 0 to get all events
    if session_id is None:
        session_id = 0
    
    queue = await sse_manager.connect(session_id)
    
    # Don't use finally block - let the generator handle cleanup
    async def event_stream():
        try:
            async for event in event_generator(queue):
                yield event
        finally:
            print(f"🔌 SSE: Client disconnected from session {session_id}")
            sse_manager.disconnect(session_id, queue)
    
    return EventSourceResponse(event_stream())


@router.get("/ping")
async def ping():
    """Health check endpoint"""
    return {"status": "ok"}
