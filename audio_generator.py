from pathlib import Path
import hashlib
import tempfile


def _safe_cache_dir() -> Path:
    """Return a writable temp folder for Streamlit Cloud/local use."""
    base = Path(tempfile.gettempdir()) / "english_listening_audio_cache"
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_audio_path(level_key: str, topic_key: str, question_id, english_text: str, repeat_count: int = 2) -> Path:
    """Generate an MP3 file in /tmp. The sentence is repeated in the audio.

    This function intentionally avoids the project audio/ folder, because on GitHub
    an accidental file named audio can break folder creation.
    """
    from gtts import gTTS

    text = str(english_text).strip()
    repeated_text = (text + ". ") * max(1, int(repeat_count))
    digest = hashlib.md5(repeated_text.encode("utf-8")).hexdigest()[:12]

    folder = _safe_cache_dir() / str(level_key) / str(topic_key)
    folder.mkdir(parents=True, exist_ok=True)
    audio_path = folder / f"{question_id}_{digest}.mp3"

    if not audio_path.exists():
        tts = gTTS(text=repeated_text, lang="en", slow=False)
        tts.save(str(audio_path))

    return audio_path
