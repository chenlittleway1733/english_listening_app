from pathlib import Path
import traceback

import pandas as pd
import streamlit as st

from answer_checker import check_answer


LEVELS = {
    "初級 Level 1 / Beginner": "beginner",
    "中級 Level 2 / Intermediate": "intermediate",
    "高級 Level 3 / Advanced": "advanced",
}

TOPICS_BY_LEVEL = {
    "beginner": {},
    "intermediate": {
        "購物 Shopping-常用3000單": "shopping",
        "餐廳 Restaurant-常用3000單": "restaurant",
        "學校 School-常用3000單": "school",
        "旅遊 Travel-常用3000單": "travel",
        "工作 Work-常用3000單": "work",
        "家庭 Family-常用3000單": "family",
        "朋友 Friends-常用3000單": "friends",
    },
    "advanced": {},
}

QUESTION_RANGE_OPTIONS = [
    "1-100",
    "101-200",
    "201-300",
    "301-400",
    "401-500",
    "1-500",
    "錯題出題",
]

PLAYBACK_SPEEDS = {
    "正常速": "normal",
    "0.75倍速": "slow_075",
}

BASE_DIR = Path(__file__).resolve().parent
WRONG_FILE = BASE_DIR / "wrong_records.csv"


def load_topic(level_key: str, topic_key: str) -> pd.DataFrame:
    csv_path = BASE_DIR / "topics" / level_key / f"{topic_key}.csv"
    if not csv_path.exists():
        st.error(f"找不到題庫檔案：{csv_path}")
        st.stop()

    df = pd.read_csv(csv_path)
    required_cols = {"id", "type", "english", "chinese", "difficulty"}
    missing = required_cols - set(df.columns)
    if missing:
        st.error(f"題庫缺少欄位：{', '.join(sorted(missing))}")
        st.stop()

    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df = df.dropna(subset=["id"]).copy()
    df["id"] = df["id"].astype(int)
    return df


def filter_by_question_range(df: pd.DataFrame, range_label: str) -> pd.DataFrame:
    if range_label == "1-500":
        start_id, end_id = 1, 500
    else:
        start_text, end_text = range_label.split("-")
        start_id, end_id = int(start_text), int(end_text)
    return df[(df["id"] >= start_id) & (df["id"] <= end_id)].copy()


def pick_question(df: pd.DataFrame) -> dict:
    if df.empty:
        st.warning("這個範圍目前沒有題目，請改選其他出題範圍。")
        st.stop()
    return df.sample(1).iloc[0].to_dict()


def _normalize_wrong_df(df: pd.DataFrame) -> pd.DataFrame:
    defaults = {
        "level_name": "",
        "level_key": "",
        "topic_name": "",
        "topic_key": "",
        "id": "",
        "type": "sentence",
        "english": "",
        "chinese": "",
        "difficulty": "medium",
        "last_user_answer": "",
        "last_similarity": 0.0,
        "wrong_count": 0,
        "first_wrong_at": "",
        "last_wrong_at": "",
    }

    for col, default in defaults.items():
        if col not in df.columns:
            if col == "last_user_answer" and "user_answer" in df.columns:
                df[col] = df["user_answer"]
            elif col == "last_similarity" and "similarity" in df.columns:
                df[col] = df["similarity"]
            elif col in {"first_wrong_at", "last_wrong_at"} and "created_at" in df.columns:
                df[col] = df["created_at"]
            else:
                df[col] = default

    df["id"] = df["id"].astype(str)
    df["wrong_count"] = pd.to_numeric(df["wrong_count"], errors="coerce").fillna(0).astype(int)
    df["last_similarity"] = pd.to_numeric(df["last_similarity"], errors="coerce").fillna(0.0)
    return df[list(defaults.keys())]


def load_wrong_records() -> pd.DataFrame:
    if not WRONG_FILE.exists():
        return _normalize_wrong_df(pd.DataFrame())
    try:
        return _normalize_wrong_df(pd.read_csv(WRONG_FILE))
    except Exception:
        return _normalize_wrong_df(pd.DataFrame())


def save_wrong_records(df: pd.DataFrame) -> None:
    _normalize_wrong_df(df).to_csv(WRONG_FILE, index=False, encoding="utf-8-sig")


def get_wrong_records_for_current_topic(level_key: str, topic_key: str) -> pd.DataFrame:
    wrong_df = load_wrong_records()
    if wrong_df.empty:
        return wrong_df
    filtered = wrong_df[
        (wrong_df["level_key"].astype(str) == str(level_key))
        & (wrong_df["topic_key"].astype(str) == str(topic_key))
    ].copy()
    if filtered.empty:
        return filtered
    filtered = filtered.sort_values("last_wrong_at")
    filtered = filtered.drop_duplicates(subset=["level_key", "topic_key", "id", "english"], keep="last")
    return filtered


def pick_wrong_question(level_key: str, topic_key: str):
    wrong_df = get_wrong_records_for_current_topic(level_key, topic_key)
    if wrong_df.empty:
        return None
    return wrong_df.sample(1).iloc[0].to_dict()


def save_wrong_record(level_name: str, level_key: str, topic_name: str, topic_key: str, question: dict, user_answer: str, similarity: float) -> None:
    now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    wrong_df = load_wrong_records()
    qid = str(question["id"])
    english = str(question["english"])

    mask = (
        (wrong_df["level_key"].astype(str) == str(level_key))
        & (wrong_df["topic_key"].astype(str) == str(topic_key))
        & (wrong_df["id"].astype(str) == qid)
        & (wrong_df["english"].astype(str) == english)
    )

    if mask.any():
        idx = wrong_df[mask].index[-1]
        wrong_df.loc[idx, "level_name"] = level_name
        wrong_df.loc[idx, "topic_name"] = topic_name
        wrong_df.loc[idx, "type"] = question.get("type", "sentence")
        wrong_df.loc[idx, "chinese"] = question.get("chinese", "")
        wrong_df.loc[idx, "difficulty"] = question.get("difficulty", "medium")
        wrong_df.loc[idx, "last_user_answer"] = user_answer
        wrong_df.loc[idx, "last_similarity"] = similarity
        wrong_df.loc[idx, "wrong_count"] = int(wrong_df.loc[idx, "wrong_count"]) + 1
        wrong_df.loc[idx, "last_wrong_at"] = now
    else:
        row = pd.DataFrame([{
            "level_name": level_name,
            "level_key": level_key,
            "topic_name": topic_name,
            "topic_key": topic_key,
            "id": qid,
            "type": question.get("type", "sentence"),
            "english": english,
            "chinese": question.get("chinese", ""),
            "difficulty": question.get("difficulty", "medium"),
            "last_user_answer": user_answer,
            "last_similarity": similarity,
            "wrong_count": 1,
            "first_wrong_at": now,
            "last_wrong_at": now,
        }])
        wrong_df = pd.concat([wrong_df, row], ignore_index=True)

    save_wrong_records(wrong_df)


def remove_wrong_record(level_key: str, topic_key: str, question: dict) -> int:
    wrong_df = load_wrong_records()
    if wrong_df.empty:
        return 0
    qid = str(question["id"])
    english = str(question["english"])
    mask = (
        (wrong_df["level_key"].astype(str) == str(level_key))
        & (wrong_df["topic_key"].astype(str) == str(topic_key))
        & (wrong_df["id"].astype(str) == qid)
        & (wrong_df["english"].astype(str) == english)
    )
    count = int(mask.sum())
    if count:
        save_wrong_records(wrong_df[~mask].copy())
    return count


def clear_answer(answer_key: str) -> None:
    st.session_state[answer_key] = ""


def make_audio_or_show_error(level_key: str, topic_key: str, q: dict, playback_speed_key: str):
    """Try to generate audio. If TTS fails, keep the app alive and show details."""
    try:
        from audio_generator import get_audio_path
        audio_path = get_audio_path(
            level_key,
            topic_key,
            q["id"],
            q["english"],
            repeat_count=2,
            playback_speed_key=playback_speed_key,
        )
        st.audio(str(audio_path))
        st.caption("按一次播放鈕會播放兩次：第一次女聲，第二次男聲。")
    except Exception as exc:
        st.error("語音產生失敗，但程式仍可繼續作答。")
        with st.expander("查看語音錯誤原因"):
            st.exception(exc)
        st.info("可先按『答題後顯示正解』測試題庫；若要恢復語音，通常重新整理頁面或重新部署後即可再試。")


def main() -> None:
    st.set_page_config(page_title="英文聽力練習系統", layout="centered")
    st.title("英文聽力練習系統")
    st.caption("先選等級與類型，再選出題範圍。可練指定題號區間，也可改用錯題記錄出題；錯題答對後會自動移出錯題記錄。")

    st.markdown("### 練習設定")
    level_names = list(LEVELS.keys())
    col1, col2 = st.columns(2)
    with col1:
        level_name = st.selectbox("1. 選擇等級", level_names, index=1)
        level_key = LEVELS[level_name]

    available_topics = TOPICS_BY_LEVEL[level_key]
    if not available_topics:
        st.info("這個等級目前還沒有建立類型。之後可以新增新的題庫 CSV。")
        st.stop()

    with col2:
        topic_name = st.selectbox("2. 選擇類型", list(available_topics.keys()))
        topic_key = available_topics[topic_name]

    current_wrong_count = len(get_wrong_records_for_current_topic(level_key, topic_key))
    question_range = st.selectbox(
        "3. 選擇出題範圍",
        QUESTION_RANGE_OPTIONS,
        index=0,
        help="選擇題號區間時，系統會從目前等級與類型的 CSV 題庫中隨機抽題。選擇錯題出題時，系統只會從目前等級與類型的錯題記錄抽題；答對後會自動移出錯題記錄。",
    )

    playback_speed_label = st.selectbox(
        "4. 選擇播放速度",
        list(PLAYBACK_SPEEDS.keys()),
        index=0,
        help="正常速適合一般練習；0.75倍速適合較長句或第一次聽寫練習。",
    )
    playback_speed_key = PLAYBACK_SPEEDS[playback_speed_label]

    mode_key = "wrong" if question_range == "錯題出題" else "normal"
    if mode_key == "normal":
        st.info(f"目前模式：一般隨機出題，範圍：{question_range}。")
    else:
        if current_wrong_count:
            st.warning(f"目前模式：錯題出題。這個類型目前有 {current_wrong_count} 題錯題；答對後會自動移出錯題記錄。")
        else:
            st.warning("目前模式：錯題出題。不過這個類型現在還沒有錯題，請先用一般範圍出題練習。")

    with st.expander("進階設定"):
        show_chinese_hint = st.checkbox("顯示中文提示", value=False)
        show_answer_after_submit = st.checkbox("答題後顯示正解", value=True)

    df = load_topic(level_key, topic_key)
    if mode_key == "normal":
        practice_df = filter_by_question_range(df, question_range)
        if practice_df.empty:
            st.warning(f"目前類型沒有第 {question_range} 題範圍的題目，請改選其他範圍。")
            st.stop()
    else:
        practice_df = df

    range_key = question_range.replace("-", "_").replace("錯題出題", "wrong")
    state_key = f"question_{level_key}_{topic_key}_{mode_key}_{range_key}"
    answer_key = f"user_answer_{level_key}_{topic_key}_{mode_key}_{range_key}"

    if answer_key not in st.session_state:
        st.session_state[answer_key] = ""

    if state_key not in st.session_state:
        st.session_state[state_key] = pick_wrong_question(level_key, topic_key) if mode_key == "wrong" else pick_question(practice_df)

    if st.button("換一題"):
        st.session_state[state_key] = pick_wrong_question(level_key, topic_key) if mode_key == "wrong" else pick_question(practice_df)
        clear_answer(answer_key)

    q = st.session_state[state_key]

    if q is None:
        st.subheader(f"等級：{level_name}")
        st.write(f"類型：{topic_name}　｜　出題範圍：{question_range}")
        st.info("目前這個類型沒有錯題記錄。請先用一般隨機出題練習，答錯後會自動加入錯題記錄。")
    else:
        st.subheader(f"等級：{level_name}")
        st.write(f"類型：{topic_name}　｜　題型：{q['type']}　｜　出題範圍：{question_range}　｜　播放速度：{playback_speed_label}　｜　題號：{q['id']}")

        if show_chinese_hint:
            st.info(f"中文提示：{q['chinese']}")

        make_audio_or_show_error(level_key, topic_key, q, playback_speed_key)

        user_answer = st.text_input("請輸入你聽到的英文", key=answer_key)

        if st.button("送出答案"):
            result = check_answer(user_answer, q["english"])
            similarity = result["similarity"]

            if result["is_correct"]:
                st.success(f"答對了！相似度：{similarity}%")
                removed = remove_wrong_record(level_key, topic_key, q)
                if mode_key == "wrong" and removed > 0:
                    st.info("這一句已經從錯題記錄移除。")
                    remaining = get_wrong_records_for_current_topic(level_key, topic_key)
                    st.session_state[state_key] = None if remaining.empty else pick_wrong_question(level_key, topic_key)
            else:
                st.error(f"答錯了。相似度：{similarity}%")
                save_wrong_record(level_name, level_key, topic_name, topic_key, q, user_answer, similarity)
                st.warning("已加入錯題記錄。")
                if mode_key == "wrong":
                    st.session_state[state_key] = pick_wrong_question(level_key, topic_key)

            if show_answer_after_submit:
                st.write("正確答案：")
                st.info(q["english"])
                st.write("中文意思：")
                st.write(q["chinese"])

    st.divider()
    with st.expander("查看錯題記錄"):
        current_wrong_df = get_wrong_records_for_current_topic(level_key, topic_key)
        st.write(f"目前類型錯題數：{len(current_wrong_df)}")
        if not current_wrong_df.empty:
            st.dataframe(current_wrong_df.tail(50), use_container_width=True)
        else:
            st.write("目前沒有錯題記錄。")


try:
    main()
except Exception as exc:
    try:
        st.set_page_config(page_title="英文聽力練習系統 - 錯誤診斷", layout="centered")
    except Exception:
        pass
    st.title("英文聽力練習系統：錯誤診斷")
    st.error("程式啟動時發生錯誤。這版會把錯誤顯示在畫面上，方便修正。")
    st.exception(exc)
    with st.expander("完整 traceback"):
        st.code(traceback.format_exc())
