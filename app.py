import streamlit as st
import pandas as pd
from pathlib import Path
from answer_checker import check_answer
from audio_generator import get_audio_path

st.set_page_config(page_title="英文聽力練習系統", layout="centered")

st.title("英文聽力練習系統")
st.caption("選擇等級 → 選擇類型 → 選擇一般出題或錯題出題 → 聽英文 → 輸入答案 → 系統比對 → 錯題記錄")

# 等級：現在七大類都放在「中級」。
# 之後要新增初級或高級類型時，只要在 TOPICS_BY_LEVEL 對應等級加入顯示名稱與檔名即可。
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

WRONG_FILE = Path("wrong_records.csv")

# ---------- 工具函式 ----------
def load_topic(level_key: str, topic_key: str) -> pd.DataFrame:
    csv_path = Path("topics") / level_key / f"{topic_key}.csv"
    if not csv_path.exists():
        st.error(f"找不到題庫檔案：{csv_path}")
        st.stop()

    df = pd.read_csv(csv_path)
    required_cols = {"id", "type", "english", "chinese", "difficulty"}
    missing = required_cols - set(df.columns)
    if missing:
        st.error(f"題庫缺少欄位：{', '.join(missing)}")
        st.stop()

    return df


def pick_question(df: pd.DataFrame) -> dict:
    """從目前選定的等級與類型題庫中隨機抽一題。"""
    if df.empty:
        st.warning("這個等級與類型下沒有題目，請換等級或類型。")
        st.stop()
    return df.sample(1).iloc[0].to_dict()


def _normalize_wrong_df(df: pd.DataFrame) -> pd.DataFrame:
    """補齊錯題檔欄位，避免舊版 wrong_records.csv 造成錯誤。"""
    columns_defaults = {
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

    for col, default in columns_defaults.items():
        if col not in df.columns:
            # 舊版欄位名稱相容
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
    return df[list(columns_defaults.keys())]


def load_wrong_records() -> pd.DataFrame:
    if not WRONG_FILE.exists():
        return _normalize_wrong_df(pd.DataFrame())
    try:
        df = pd.read_csv(WRONG_FILE)
    except Exception:
        return _normalize_wrong_df(pd.DataFrame())
    return _normalize_wrong_df(df)


def save_wrong_records(df: pd.DataFrame) -> None:
    df = _normalize_wrong_df(df)
    df.to_csv(WRONG_FILE, index=False, encoding="utf-8-sig")


def get_wrong_records_for_current_topic(level_key: str, topic_key: str) -> pd.DataFrame:
    """只取目前等級與目前類型的錯題，並去除同一題重複記錄。"""
    wrong_df = load_wrong_records()
    if wrong_df.empty:
        return wrong_df

    filtered = wrong_df[
        (wrong_df["level_key"].astype(str) == str(level_key))
        & (wrong_df["topic_key"].astype(str) == str(topic_key))
    ].copy()

    if filtered.empty:
        return filtered

    filtered["id"] = filtered["id"].astype(str)
    filtered = filtered.sort_values("last_wrong_at")
    filtered = filtered.drop_duplicates(subset=["level_key", "topic_key", "id", "english"], keep="last")
    return filtered


def pick_wrong_question(level_key: str, topic_key: str):
    """從目前類型的錯題記錄隨機抽一題。"""
    wrong_df = get_wrong_records_for_current_topic(level_key, topic_key)
    if wrong_df.empty:
        return None
    return wrong_df.sample(1).iloc[0].to_dict()


def save_wrong_record(level_name: str, level_key: str, topic_name: str, topic_key: str, question: dict, user_answer: str, similarity: float) -> None:
    """錯題以題目為單位保存；同一題再錯時增加 wrong_count，不重複新增多列。"""
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
    """答對錯題後，把該句子從錯題記錄移除。回傳移除筆數。"""
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
    removed_count = int(mask.sum())

    if removed_count > 0:
        wrong_df = wrong_df[~mask].copy()
        save_wrong_records(wrong_df)

    return removed_count


def clear_answer(answer_key: str) -> None:
    st.session_state[answer_key] = ""


# ---------- 側邊設定 ----------
with st.sidebar:
    st.header("練習設定")

    # 目前主題都在中級，所以預設選中級。
    level_names = list(LEVELS.keys())
    level_name = st.selectbox("選擇等級", level_names, index=1)
    level_key = LEVELS[level_name]

    available_topics = TOPICS_BY_LEVEL[level_key]

    if not available_topics:
        st.info("這個等級目前還沒有建立類型。之後可以新增新的題庫 CSV。")
        st.stop()

    topic_name = st.selectbox("選擇類型", list(available_topics.keys()))
    topic_key = available_topics[topic_name]

    practice_mode = st.radio(
        "出題來源",
        ["一般隨機出題", "錯題記錄出題"],
        index=0,
        help="一般隨機出題：從目前類型題庫隨機抽題。錯題記錄出題：只從目前類型的錯題中抽題，答對後自動移出錯題。",
    )

    show_chinese_hint = st.checkbox("顯示中文提示", value=False)
    show_answer_after_submit = st.checkbox("答題後顯示正解", value=True)

# ---------- 載入題庫與決定出題來源 ----------
df = load_topic(level_key, topic_key)
mode_key = "wrong" if practice_mode == "錯題記錄出題" else "normal"
state_key = f"question_{level_key}_{topic_key}_{mode_key}"
answer_key = f"user_answer_{level_key}_{topic_key}_{mode_key}"

if answer_key not in st.session_state:
    st.session_state[answer_key] = ""

if state_key not in st.session_state:
    if mode_key == "wrong":
        st.session_state[state_key] = pick_wrong_question(level_key, topic_key)
    else:
        st.session_state[state_key] = pick_question(df)

# ---------- 換題 ----------
if st.button("換一題"):
    if mode_key == "wrong":
        st.session_state[state_key] = pick_wrong_question(level_key, topic_key)
    else:
        st.session_state[state_key] = pick_question(df)
    clear_answer(answer_key)

q = st.session_state[state_key]

if q is None:
    st.subheader(f"等級：{level_name}")
    st.write(f"類型：{topic_name}　｜　出題來源：{practice_mode}")
    st.info("目前這個類型沒有錯題記錄。請先用一般隨機出題練習，答錯後會自動加入錯題記錄。")
else:
    st.subheader(f"等級：{level_name}")
    st.write(f"類型：{topic_name}　｜　題型：{q['type']}　｜　出題來源：{practice_mode}")

    if show_chinese_hint:
        st.info(f"中文提示：{q['chinese']}")

    # ---------- 音檔 ----------
    audio_path = get_audio_path(level_key, topic_key, q["id"], q["english"])
    st.caption("播放一次會連續唸兩次。")
    st.audio(str(audio_path))

    # ---------- 作答 ----------
    user_answer = st.text_input("請輸入你聽到的英文", key=answer_key)

    if st.button("送出答案"):
        result = check_answer(user_answer, q["english"])
        similarity = result["similarity"]

        if result["is_correct"]:
            st.success(f"答對了！相似度：{similarity}%")

            if mode_key == "wrong":
                removed_count = remove_wrong_record(level_key, topic_key, q)
                if removed_count > 0:
                    st.info("這一句已經從錯題記錄移除。")
                remaining_wrong_df = get_wrong_records_for_current_topic(level_key, topic_key)
                st.session_state[state_key] = None if remaining_wrong_df.empty else pick_wrong_question(level_key, topic_key)
            else:
                # 一般出題答對時，也順手移除同題錯題，避免學生已會的題目留在錯題本。
                remove_wrong_record(level_key, topic_key, q)
        else:
            st.error(f"答錯了。相似度：{similarity}%")
            save_wrong_record(level_name, level_key, topic_name, topic_key, q, user_answer, similarity)
            st.warning("已加入錯題記錄。")

            if mode_key == "wrong":
                # 錯題模式答錯時仍留在錯題本，下一題繼續從目前類型錯題隨機抽。
                st.session_state[state_key] = pick_wrong_question(level_key, topic_key)

        if show_answer_after_submit:
            st.write("正確答案：")
            st.info(q["english"])
            st.write("中文意思：")
            st.write(q["chinese"])

# ---------- 錯題紀錄 ----------
st.divider()
with st.expander("查看錯題記錄"):
    wrong_df = load_wrong_records()
    current_wrong_df = get_wrong_records_for_current_topic(level_key, topic_key)

    st.write(f"目前類型錯題數：{len(current_wrong_df)}")

    if not current_wrong_df.empty:
        st.dataframe(current_wrong_df.tail(50), use_container_width=True)
    elif not wrong_df.empty:
        st.write("目前類型沒有錯題，但其他類型有錯題。")
    else:
        st.write("目前沒有錯題記錄。")
