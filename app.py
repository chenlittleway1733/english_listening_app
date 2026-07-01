import streamlit as st
import pandas as pd
from pathlib import Path
from answer_checker import check_answer
from audio_generator import get_audio_path

st.set_page_config(page_title="英文聽力練習系統", layout="centered")

st.title("英文聽力練習系統")
st.caption("選擇等級 → 選擇類型 → 聽英文 → 輸入答案 → 系統比對 → 錯題記錄")

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
    if df.empty:
        st.warning("這個等級與類型下沒有題目，請換等級或類型。")
        st.stop()
    return df.sample(1).iloc[0].to_dict()


def save_wrong_record(level_name: str, level_key: str, topic_name: str, topic_key: str, question: dict, user_answer: str, similarity: float):
    wrong_file = Path("wrong_records.csv")
    row = pd.DataFrame([{
        "level_name": level_name,
        "level_key": level_key,
        "topic_name": topic_name,
        "topic_key": topic_key,
        "id": question["id"],
        "type": question["type"],
        "english": question["english"],
        "chinese": question["chinese"],
        "difficulty": question["difficulty"],
        "user_answer": user_answer,
        "similarity": similarity,
        "created_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
    }])

    if wrong_file.exists():
        old = pd.read_csv(wrong_file)
        row = pd.concat([old, row], ignore_index=True)

    row.to_csv(wrong_file, index=False, encoding="utf-8-sig")


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

    show_chinese_hint = st.checkbox("顯示中文提示", value=False)
    show_answer_after_submit = st.checkbox("答題後顯示正解", value=True)

# ---------- 載入題庫 ----------
df = load_topic(level_key, topic_key)

# 類型或等級改變時，使用不同的 session_state key，避免沿用上一個主題的題目。
state_key = f"question_{level_key}_{topic_key}"
if state_key not in st.session_state:
    st.session_state[state_key] = pick_question(df)

if st.button("換一題"):
    st.session_state[state_key] = pick_question(df)
    st.session_state.user_answer = ""

q = st.session_state[state_key]

st.subheader(f"等級：{level_name}")
st.write(f"類型：{topic_name}　｜　題型：{q['type']}")

if show_chinese_hint:
    st.info(f"中文提示：{q['chinese']}")

# ---------- 音檔 ----------
audio_path = get_audio_path(level_key, topic_key, q["id"], q["english"])
st.audio(str(audio_path))

# ---------- 作答 ----------
user_answer = st.text_input("請輸入你聽到的英文", key="user_answer")

if st.button("送出答案"):
    result = check_answer(user_answer, q["english"])
    similarity = result["similarity"]

    if result["is_correct"]:
        st.success(f"答對了！相似度：{similarity}%")
    else:
        st.error(f"答錯了。相似度：{similarity}%")
        save_wrong_record(level_name, level_key, topic_name, topic_key, q, user_answer, similarity)
        st.warning("已加入錯題記錄。")

    if show_answer_after_submit:
        st.write("正確答案：")
        st.info(q["english"])
        st.write("中文意思：")
        st.write(q["chinese"])

# ---------- 錯題紀錄 ----------
st.divider()
with st.expander("查看錯題記錄"):
    wrong_file = Path("wrong_records.csv")
    if wrong_file.exists():
        wrong_df = pd.read_csv(wrong_file)
        st.dataframe(wrong_df.tail(20), use_container_width=True)
    else:
        st.write("目前沒有錯題記錄。")
