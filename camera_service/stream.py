import cv2
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ai_engine.pipeline import face_pipeline, head_count_pipeline
from camera_service.camera import camera_0, camera_1

router = APIRouter()


async def _generate_mjpeg(camera_instance, pipeline_instance, pipeline_flag_attr: str):
    """
    Generic MJPEG generator.

    Args:
        camera_instance: CameraManager to pull frames from.
        pipeline_instance: AI pipeline to check for annotated frames.
        pipeline_flag_attr: Attribute name on pipeline_instance to check (e.g. 'is_running').
    """
    try:
        # Wait up to 5 seconds for the session to start (handles frontend race condition)
        for _ in range(50):
            if getattr(pipeline_instance, pipeline_flag_attr, False):
                break
            await asyncio.sleep(0.1)

        while True:
            is_running = getattr(pipeline_instance, pipeline_flag_attr, False)
            if not is_running:
                # Privacy constraint: Do not stream if no active session is running
                break

            # 1. Get raw frame (may be None if camera is unavailable)
            raw_frame = camera_instance.get_latest_frame()

            # 2. Stream annotated frame if available, otherwise raw frame
            if raw_frame is not None:
                frame_to_stream = pipeline_instance.draw_annotations(raw_frame)
            else:
                frame_to_stream = None

            if frame_to_stream is not None:
                # Compress to JPEG — quality 70 is a good balance for WiFi streaming
                ret, buffer = cv2.imencode('.jpg', frame_to_stream, [cv2.IMWRITE_JPEG_QUALITY, 70])

                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # Limit streaming framerate to save bandwidth (~30 FPS)
            await asyncio.sleep(1.0 / 30.0)

    except asyncio.CancelledError:
        # Client disconnected — clean exit
        pass
    except Exception as e:
        print(f"Stream error: {e}")


async def generate_mjpeg_stream():
    """
    Camera 0 MJPEG stream — face recognition feed.
    Shows annotated frames from FaceRecognitionPipeline during active sessions.
    Falls back to raw Camera 0 frames when no session is active.
    """
    async for chunk in _generate_mjpeg(camera_0, face_pipeline, "is_running"):
        yield chunk


async def generate_headcount_stream():
    """
    Camera 1 MJPEG stream — head counting feed.
    Shows annotated frames from HeadCountPipeline during head count mode.
    Falls back to raw Camera 1 frames when not in head count mode.
    """
    async for chunk in _generate_mjpeg(camera_1, head_count_pipeline, "is_running"):
        yield chunk

@router.get("/enroll")
async def enroll_stream():
    """
    MJPEG endpoint specifically for face enrollment. 
    Dynamically starts Camera 0 and streams raw frames.
    Stops the camera when the client disconnects.
    """
    async def _enroll_generator():
        try:
            camera_0.start()
            while True:
                frame = camera_0.get_latest_frame()
                if frame is not None:
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if ret:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                await asyncio.sleep(1.0 / 30.0)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Enroll stream error: {e}")
        finally:
            # Safely release the hardware
            camera_0.stop()

    return StreamingResponse(_enroll_generator(), media_type="multipart/x-mixed-replace; boundary=frame")


@router.get("/live")
async def live_video_feed():
    """
    Camera 0 MJPEG streaming endpoint (face recognition feed).
    Returns a multipart/x-mixed-replace continuous stream.
    Used during Take Attendance mode.
    """
    return StreamingResponse(
        generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/headcount")
async def headcount_video_feed():
    """
    Camera 1 MJPEG streaming endpoint (head count feed).
    Returns a multipart/x-mixed-replace continuous stream.
    Used during Verify Head Count mode.
    If Camera 1 is unavailable, the stream will be empty frames.
    """
    return StreamingResponse(
        generate_headcount_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
