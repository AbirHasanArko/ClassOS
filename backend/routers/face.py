"""
ClassOS — Face Registration Router
Handles uploading face images, generating embeddings, and managing
the face data that powers live recognition during attendance sessions.
"""

import os
import shutil
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user, require_role
from backend.schemas.face import FaceRegistrationStatus, FaceUploadResult, FaceEmbeddingOut
from models.user import User, UserRole
from models.student import Student
from models.face_embedding import FaceEmbedding
from ai_engine.embedding_generator import EmbeddingGenerator
from ai_engine.face_recognizer import recognizer
from ai_engine.config import ai_config

router = APIRouter()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@router.get("/{student_id}/face", response_model=FaceRegistrationStatus)
async def get_face_status(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a student's face registration status and sample count."""
    student = await _get_student_or_404(db, student_id)

    stmt = (
        select(FaceEmbedding)
        .where(FaceEmbedding.student_id == student_id)
        .order_by(FaceEmbedding.sample_number)
    )
    result = await db.execute(stmt)
    embeddings = result.scalars().all()

    return {
        "student_id": student.id,
        "face_registered": student.face_registered,
        "total_samples": len(embeddings),
        "max_samples": ai_config.FACE_SAMPLES_PER_STUDENT,
        "samples": embeddings,
    }


@router.post(
    "/{student_id}/face",
    response_model=FaceUploadResult,
    status_code=status.HTTP_201_CREATED,
)
async def upload_face_images(
    student_id: UUID,
    files: list[UploadFile] = File(..., description="One or more face images (jpg/png)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER])),
):
    """
    Upload face images for a student.

    Each image must contain **exactly one face**. The system generates a
    128-dimensional embedding from each and stores it in the database.
    Once at least one sample exists the student is marked as face-registered.
    Up to ``FACE_SAMPLES_PER_STUDENT`` (default 20) samples are allowed.
    """
    student = await _get_student_or_404(db, student_id)

    # How many samples already exist?
    count_result = await db.execute(
        select(func.count())
        .select_from(FaceEmbedding)
        .where(FaceEmbedding.student_id == student_id)
    )
    existing_count = count_result.scalar_one()
    remaining_slots = ai_config.FACE_SAMPLES_PER_STUDENT - existing_count

    if remaining_slots <= 0:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Student already has {existing_count} face samples "
                f"(max {ai_config.FACE_SAMPLES_PER_STUDENT}). "
                "Delete existing samples first to re-register."
            ),
        )

    # Cap to available slots
    files_to_process = files[: remaining_slots]

    # Prepare storage directory
    student_faces_dir = os.path.join(ai_config.FACE_IMAGES_DIR, str(student_id))
    os.makedirs(student_faces_dir, exist_ok=True)

    samples_added = 0
    errors: list[str] = []

    for idx, upload_file in enumerate(files_to_process):
        # Validate extension
        ext = os.path.splitext(upload_file.filename or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            errors.append(f"{upload_file.filename}: unsupported format ({ext})")
            continue

        # Save file to disk
        sample_number = existing_count + samples_added + 1
        filename = f"sample_{sample_number:02d}{ext}"
        file_path = os.path.join(student_faces_dir, filename)

        try:
            with open(file_path, "wb") as f:
                content = await upload_file.read()
                f.write(content)
        except Exception as e:
            errors.append(f"{upload_file.filename}: failed to save ({e})")
            continue

        # Generate embedding
        embedding = EmbeddingGenerator.generate_embedding_from_image(file_path)

        if embedding is None:
            # Clean up saved file
            os.remove(file_path)
            errors.append(
                f"{upload_file.filename}: could not extract a face "
                "(image must contain exactly one clearly visible face)"
            )
            continue

        # Store embedding in DB
        face_emb = FaceEmbedding(
            student_id=student_id,
            embedding=embedding.tobytes(),
            image_path=file_path,
            sample_number=sample_number,
        )
        db.add(face_emb)
        samples_added += 1

    if samples_added == 0 and errors:
        raise HTTPException(
            status_code=400,
            detail=f"No valid face images could be processed. Errors: {'; '.join(errors)}",
        )

    # Mark student as face-registered once they have at least one sample
    total_samples = existing_count + samples_added
    if total_samples > 0 and not student.face_registered:
        student.face_registered = True

    await db.commit()

    # Refresh the in-memory recognizer cache so new faces are immediately usable
    await recognizer.load_embeddings_from_db()

    message = f"Added {samples_added} face sample(s) for {student.full_name}."
    if errors:
        message += f" Skipped {len(errors)} file(s): {'; '.join(errors)}"

    return {
        "message": message,
        "samples_added": samples_added,
        "total_samples": total_samples,
        "face_registered": student.face_registered,
    }


@router.delete("/{student_id}/face", status_code=status.HTTP_200_OK)
async def delete_face_data(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER])),
):
    """
    Delete all face embeddings and images for a student.

    This resets the student's face registration so new samples can be
    uploaded. Useful when a student's appearance has changed significantly.
    """
    student = await _get_student_or_404(db, student_id)

    # Fetch and delete embeddings from DB
    stmt = select(FaceEmbedding).where(FaceEmbedding.student_id == student_id)
    result = await db.execute(stmt)
    embeddings = result.scalars().all()
    deleted_count = len(embeddings)

    for emb in embeddings:
        await db.delete(emb)

    # Reset student flag
    student.face_registered = False
    await db.commit()

    # Delete face images from disk
    student_faces_dir = os.path.join(ai_config.FACE_IMAGES_DIR, str(student_id))
    if os.path.isdir(student_faces_dir):
        shutil.rmtree(student_faces_dir)

    # Refresh in-memory recognizer
    await recognizer.load_embeddings_from_db()

    return {
        "message": f"Deleted {deleted_count} face sample(s) for {student.full_name}. "
        "Face registration has been reset.",
        "deleted_count": deleted_count,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_student_or_404(db: AsyncSession, student_id: UUID) -> Student:
    """Fetch a Student by PK or raise 404."""
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student
