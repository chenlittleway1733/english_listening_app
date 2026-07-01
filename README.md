# 英文聽力練習系統 v14

## v14 修正

- 保留 Shopping 1–500 句。
- 保留出題範圍：1-100、101-200、201-300、301-400、401-500、1-500、錯題出題。
- 移除 v13 的瀏覽器語音元件，改回 `st.audio` 播放 mp3。
- mp3 產生在系統暫存資料夾 `/tmp`，不會使用專案中的 `audio/`，避免 GitHub 上的 audio 檔案/資料夾衝突。
- 加入錯誤診斷：如果 Streamlit Cloud 出錯，會在畫面上顯示錯誤，不會只看到 Oh no。

## 安裝

```bash
pip install -r requirements.txt
```

## 執行

```bash
streamlit run app.py
```
