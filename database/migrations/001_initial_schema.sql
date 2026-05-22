-- ClassOS Initial Database Schema Migration
-- Designed for PostgreSQL 16
-- Run this via psql or SQLAlchemy metadata generation

-- 1. Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- (Note: SQLAlchemy's Base.metadata.create_all will generate the tables
-- dynamically based on the models. This file serves as a manual reference
-- or baseline if using pure SQL migrations instead of Alembic.)

-- 2. Performance Indexes (to be applied after tables are created)
-- These are critical for the Raspberry Pi 5 to maintain speed during queries

-- Fast lookup for attendance by session
CREATE INDEX IF NOT EXISTS idx_attendance_session_id ON attendance(session_id);

-- Fast lookup for attendance by student
CREATE INDEX IF NOT EXISTS idx_attendance_student_id ON attendance(student_id);

-- Find active sessions quickly
CREATE INDEX IF NOT EXISTS idx_sessions_status ON attendance_sessions(status) WHERE status = 'active';

-- NOTE: The models define UniqueConstraints and foreign keys, which SQLAlchemy will enforce.
