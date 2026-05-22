import cv2
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ai_engine.pipeline import pipeline
from camera_service.camera import camera

router = APIRouter()

async def generate_mjpeg_stream():
    """Generator yielding JPEG frames formatted for multipart/x-mixed-replace."""
    # Ensure camera is running
    camera.start()
    
    try:
        while True:
            frame = camera.get_latest_frame()
            
            if frame is not None:
                # If AI pipeline is running (e.g. during an active session),
                # we process the frame to draw bounding boxes.
                if pipeline.is_running:
                    # In stream mode, we use a dummy callback that does nothing
                    # because the Attendance Engine handles the actual logic callback
                    frame = pipeline.process_frame(frame, lambda x: None)
                    
                # Compress to JPEG
                # Quality 70 is a good balance for streaming over WiFi
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                           
            # Limit streaming framerate to save bandwidth (~15 FPS)
            await asyncio.sleep(1.0 / 15.0)
            
    except asyncio.CancelledError:
        # Client disconnected
        pass
    except Exception as e:
        print(f"Stream error: {e}")

@router.get("/live")
async def live_video_feed():
    """
    MJPEG streaming endpoint for the React frontend dashboard.
    Returns a multipart/x-mixed-replace continuous stream.
    """
    return StreamingResponse(
        generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
