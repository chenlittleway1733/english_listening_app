import streamlit as st
import pandas as pd
from pathlib import Path
from answer_checker import check_answer
from audio_generator import get_audio_path

st.set_page_config(page_title="英文聽力練習系統", layout="centered")

st.title("英文聽力練習系統")
st.caption("選擇主題 → 聽英文 → 輸入答案 → 系統比對 → 錯題記錄")

TOPICS = {
    "購物 Shopping": "shopping",
    "餐廳 Restaurant": "restaurant",
    "學校 School": "school",
    "旅遊 Travel": "travel",
}

# ---------- 工具函式 ----------
def load_topic(topic_key: str) -> pd.DataFrame:
    csv_path = Path("topics") / f"{topic_key}.csv"
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


def pick_question(df: pd.DataFrame):
    if df.empty:
        st.warning("這個條件下沒有題目，請換主題或難度。")
        st.stop()
    return df.sample(1).iloc[0].to_dict()


def save_wrong_record(topic_key: str, question: dict, user_answer: str, similarity: float):
    wrong_file = Path("wrong_records.csv")
    row = pd.DataFrame([{
        "topic": topic_key,
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
    topic_name = st.selectbox("選擇對話主題", list(TOPICS.keys()))
    topic_key = TOPICS[topic_name]

    raw_df = load_topic(topic_key)
    difficulties = ["全部"] + sorted(raw_df["difficulty"].dropna().unique().tolist())
    difficulty = st.selectbox("選擇難度", difficulties)

    show_chinese_hint = st.checkbox("顯示中文提示", value=False)
    show_answer_after_submit = st.checkbox("答題後顯示正解", value=True)

# ---------- 載入題庫 ----------
df = raw_df.copy()
if difficulty != "全部":
    df = df[df["difficulty"] == difficulty]

state_key = f"question_{topic_key}_{difficulty}"
if state_key not in st.session_state:
    st.session_state[state_key] = pick_question(df)

if st.button("換一題"):
    st.session_state[state_key] = pick_question(df)
    st.session_state.user_answer = ""

q = st.session_state[state_key]

st.subheader(f"主題：{topic_name}")
st.write(f"難度：{q['difficulty']}　｜　題型：{q['type']}")

if show_chinese_hint:
    st.info(f"中文提示：{q['chinese']}")

# ---------- 音檔 ----------
audio_path = get_audio_path(topic_key, q["id"], q["english"])
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
        save_wrong_record(topic_key, q, user_answer, similarity)
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
