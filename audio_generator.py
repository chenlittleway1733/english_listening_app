from pathlib import Path
import hashlib
import tempfile
import asyncio
import threading
from typing import Callable


FEMALE_VOICE = "en-US-JennyNeural"
MALE_VOICE = "en-US-GuyNeural"

RATE_BY_SPEED = {
    "normal": "+0%",
}


def _safe_cache_dir() -> Path:
    """Return a writable temp folder for Streamlit Cloud/local use."""
    base = Path(tempfile.gettempdir()) / "english_listening_audio_cache"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _run_async_in_thread(coro_factory: Callable[[], object]) -> None:
    """Run an async TTS task safely from Streamlit.

    Streamlit can sometimes already have an event loop active, so we run the
    coroutine in a short-lived thread with its own event loop.
    """
    result = {"error": None}

    def target() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro_factory())
        except Exception as exc:  # re-raised in caller thread
            result["error"] = exc
        finally:
            loop.close()

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join()

    if result["error"] is not None:
        raise result["error"]


def _save_edge_tts(path: Path, text: str, voice: str, rate: str) -> None:
    async def runner():
        import edge_tts
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
        await communicate.save(str(path))

    _run_async_in_thread(runner)


def _make_female_then_male_audio(final_path: Path, text: str, rate: str) -> None:
    """Generate one MP3 that contains female voice once, then male voice once."""
    stem = final_path.with_suffix("")
    female_path = Path(str(stem) + "_female.mp3")
    male_path = Path(str(stem) + "_male.mp3")

    if not female_path.exists():
        _save_edge_tts(female_path, text, FEMALE_VOICE, rate)
    if not male_path.exists():
        _save_edge_tts(male_path, text, MALE_VOICE, rate)

    # MP3 frames can be concatenated directly for browser playback in most cases.
    # This avoids requiring ffmpeg on Streamlit Cloud.
    with final_path.open("wb") as out:
        out.write(female_path.read_bytes())
        out.write(male_path.read_bytes())


def _fallback_gtts(final_path: Path, text: str, repeat_count: int, playback_speed_key: str) -> None:
    """Fallback when Edge TTS is unavailable. Gender selection is not supported."""
    from gtts import gTTS

    repeated_text = (text + ". ") * max(1, int(repeat_count))
    # gTTS fallback uses normal speed by default.
    slow = playback_speed_key == "slow_075"
    tts = gTTS(text=repeated_text, lang="en", slow=slow)
    tts.save(str(final_path))


def get_audio_path(
    level_key: str,
    topic_key: str,
    question_id,
    english_text: str,
    repeat_count: int = 2,
    playback_speed_key: str = "normal",
) -> Path:
    """Generate an MP3 file in /tmp.

    Primary mode:
    - play the sentence once in a female voice
    - then play the same sentence once in a male voice
    - use normal TTS speed; users can adjust speed in the browser audio player when supported.

    The project audio/ folder is intentionally avoided because an accidental
    GitHub file named audio can break folder creation on Streamlit Cloud.
    """
    text = str(english_text).strip()
    if not text:
        raise ValueError("英文句子是空的，無法產生語音。")

    rate = RATE_BY_SPEED.get(playback_speed_key, "+0%")
    digest_source = f"{text}|{playback_speed_key}|{FEMALE_VOICE}|{MALE_VOICE}|v16"
    digest = hashlib.md5(digest_source.encode("utf-8")).hexdigest()[:12]

    folder = _safe_cache_dir() / str(level_key) / str(topic_key)
    folder.mkdir(parents=True, exist_ok=True)
    audio_path = folder / f"{question_id}_{playback_speed_key}_{digest}.mp3"

    if audio_path.exists():
        return audio_path

    try:
        _make_female_then_male_audio(audio_path, text, rate)
    except Exception:
        # Keep the app usable even if Edge TTS is temporarily unavailable.
        _fallback_gtts(audio_path, text, repeat_count, playback_speed_key)

    return audio_path
