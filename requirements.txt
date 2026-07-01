import difflib
import re


def normalize_text(text: str) -> str:
    """標準化答案：忽略大小寫、標點、多餘空白。"""
    if text is None:
        return ""
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9\s']", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def check_answer(user_answer: str, correct_answer: str, threshold: float = 0.9) -> dict:
    user = normalize_text(user_answer)
    correct = normalize_text(correct_answer)

    similarity = difflib.SequenceMatcher(None, user, correct).ratio()
    similarity_percent = round(similarity * 100, 1)

    return {
        "is_correct": similarity >= threshold,
        "similarity": similarity_percent,
        "normalized_user": user,
        "normalized_correct": correct,
    }
