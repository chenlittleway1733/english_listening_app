from pathlib import Path
import tempfile
from gtts import gTTS


def _make_repeat_text(english_text: str, repeat_count: int = 2) -> str:
    """
    把同一句英文重複指定次數，讓按一次播放鍵時可以連續聽到多次。
    gTTS 會依照標點符號自然停頓，所以這裡用句點隔開每一次播放。
    """
    text = str(english_text).strip()
    if not text:
        return text

    # 避免原句沒有標點時兩句黏在一起。
    if text[-1] not in ".?!":
        text = text + "."

    return " ".join([text] * repeat_count)


def get_audio_path(level_key: str, topic_key: str, question_id, english_text: str, repeat_count: int = 2) -> Path:
    """
    產生並回傳 mp3 音檔路徑。

    這版預設把同一句英文重複播放 2 次。
    因為 Streamlit 內建 st.audio 的播放鍵無法直接控制「按一次自動播放兩次」，
    所以做法是：產生音檔時就把句子重複錄成兩遍。

    注意：不要寫入專案內的 audio/ 資料夾。
    在 GitHub / Streamlit Cloud 上，如果曾把 audio 當成「檔案」上傳，
    再執行 mkdir audio/... 就會出現 NotADirectoryError。
    因此這裡統一把音檔產生到系統暫存資料夾 /tmp 底下。
    """
    safe_level = str(level_key).strip().replace("/", "_").replace("\\", "_")
    safe_topic = str(topic_key).strip().replace("/", "_").replace("\\", "_")
    safe_id = str(question_id).strip().replace("/", "_").replace("\\", "_")
    safe_repeat = max(1, int(repeat_count))

    folder = Path(tempfile.gettempdir()) / "english_listening_audio" / safe_level / safe_topic
    folder.mkdir(parents=True, exist_ok=True)

    # 檔名加入 x2，避免沿用舊版只播放一次的快取音檔。
    audio_path = folder / f"{safe_id}_x{safe_repeat}.mp3"

    if not audio_path.exists():
        repeat_text = _make_repeat_text(english_text, repeat_count=safe_repeat)
        tts = gTTS(text=repeat_text, lang="en")
        tts.save(str(audio_path))

    return audio_path
