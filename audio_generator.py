from pathlib import Path
from gtts import gTTS


def get_audio_path(level_key: str, topic_key: str, question_id, english_text: str) -> Path:
    """若音檔不存在，就自動用 gTTS 產生 mp3。"""
    folder = Path("audio") / level_key / topic_key
    folder.mkdir(parents=True, exist_ok=True)

    audio_path = folder / f"{question_id}.mp3"

    if not audio_path.exists():
        tts = gTTS(text=str(english_text), lang="en")
        tts.save(str(audio_path))

    return audio_path
