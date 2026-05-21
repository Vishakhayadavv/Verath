import os
from typing import Any, Dict

from app.core.logging_config import logger
from app.models.memory import RecordingSession
from app.services.audio import record_audio
from app.services.transcription import transcribe


class AudioProcessor:
    """Handles audio recording with session types and metadata."""

    def __init__(self):
        self.recording_sessions: Dict[str, RecordingSession] = {}

    async def record_session(self, session: RecordingSession, user_id: str) -> Dict[str, Any]:
        """
        Record audio with session metadata.

        Session types:
        - manual: User-initiated recording
        - lecture: Long-form lecture recording
        - meeting: Meeting/conversation recording
        - general: General purpose recording
        - short: Quick capture (5-10 seconds)
        """
        try:
            logger.info(f"Starting {session.session_type} recording for user {user_id}")

            # Set end time based on duration
            session.end_time = session.start_time

            # Generate filename if not provided
            if not session.filename:
                session.filename = f"{session.session_type}_{user_id}_{session.start_time.strftime('%Y%m%d_%H%M%S')}.wav"

            # Record audio
            file_path = record_audio(
                filename=session.filename,
                duration=session.duration
            )

            logger.info(f"Recording completed: {file_path}")

            return {
                "success": True,
                "file_path": file_path,
                "session_type": session.session_type,
                "duration": session.duration,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat()
            }

        except Exception as e:
            logger.error(f"Error in recording session: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "session_type": session.session_type
            }

    async def transcribe_audio(self, file_path: str) -> str:
        """Transcribe audio file to text."""
        try:
            logger.info(f"Transcribing audio: {file_path}")
            text = transcribe(file_path)
            logger.info(f"Transcription completed: {len(text)} characters")
            return text
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}", exc_info=True)
            raise

    def cleanup_temp_file(self, file_path: str):
        """Clean up temporary audio file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temp file: {e}")

audio_processor = AudioProcessor()
