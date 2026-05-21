from typing import Dict, List

import torch

from app.core.logging_config import logger

try:
    from pyannote.audio import Pipeline  # type: ignore
except Exception:
    Pipeline = None


_pipeline = None


def _get_pipeline():
    global _pipeline
    if Pipeline is None:
        return None
    if _pipeline is None:
        try:
            _pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")
            if torch.cuda.is_available():
                _pipeline.to(torch.device("cuda"))
        except Exception as e:
            print(f"Warning: Could not load speaker diarization pipeline: {e}")
            _pipeline = None
    return _pipeline


def identify_speakers(audio_file: str) -> List[Dict]:
    """Identify speakers in audio file using diarization."""
    pipeline = _get_pipeline()
    if pipeline is None:
        logger.warning("Speaker diarization pipeline not available, using default speaker")
        return [{"speaker": "You", "start": 0.0, "end": 10.0}]

    try:
        diarization = pipeline(audio_file)
        speakers = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            # Map generic speaker labels to more user-friendly names
            # Fix: use the full ID if it's SPEAKER_XX
            if speaker.startswith("SPEAKER_"):
                speaker_id = speaker.split('_')[-1]
                speaker_name = f"Speaker {speaker_id}"
            else:
                speaker_name = speaker

            speakers.append({"speaker": speaker_name, "start": turn.start, "end": turn.end})
        return speakers or [{"speaker": "You", "start": 0.0, "end": 10.0}]
    except Exception as e:
        logger.warning(f"Error in speaker identification: {e}, using default speaker")
        return [{"speaker": "You", "start": 0.0, "end": 10.0}]

def get_primary_speaker(speakers: List[Dict]) -> str:
    """Get the speaker who spoke the most."""
    if not speakers:
        return "You"

    # Calculate total speaking time for each speaker
    speaker_times = {}
    for spk in speakers:
        speaker = spk["speaker"]
        duration = spk["end"] - spk["start"]
        speaker_times[speaker] = speaker_times.get(speaker, 0) + duration

    # Return speaker with most speaking time
    if speaker_times:
        return max(speaker_times.items(), key=lambda x: x[1])[0]
    return "You"
