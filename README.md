# 英文聽力練習系統 v5

這版修正 Streamlit Cloud 可能出現的：

```text
NotADirectoryError
```

原因通常是 GitHub 上的 `audio` 被上傳成「檔案」，不是資料夾；程式再嘗試建立 `audio/intermediate/shopping` 時就會失敗。

v5 已改成：

```text
音檔不再寫入專案的 audio/ 資料夾
改寫入 Streamlit Cloud 的暫存資料夾 /tmp/english_listening_audio
```

所以即使 GitHub 裡面有錯誤的 `audio` 檔案，也不會影響產生音檔。

## 執行方式

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 題庫位置

目前七大類都放在中級：

```text
topics/intermediate/shopping.csv
topics/intermediate/restaurant.csv
topics/intermediate/school.csv
topics/intermediate/travel.csv
topics/intermediate/work.csv
topics/intermediate/family.csv
topics/intermediate/friends.csv
```

其中 `shopping.csv` 已擴充為 100 句「Shopping-常用3000單」。

## 上傳 GitHub 建議

請把壓縮檔解開後，將資料夾內的檔案上傳到 repo 根目錄。至少要有：

```text
app.py
audio_generator.py
answer_checker.py
requirements.txt
topics/
README.md
```

`audio/` 不需要上傳，v5 壓縮檔內也已移除 `audio/`。程式會自動使用暫存資料夾產生音檔。

如果 GitHub 上已經有一個錯誤的 `audio` 檔案，可以刪掉；但 v5 不刪也能跑。


## v6 更新

- 每個英文題目產生音檔時會自動重複 2 次。
- 使用者按一次播放鍵，就會聽到同一句英文連續播放兩遍。
- 音檔檔名改為 `題號_x2.mp3`，避免沿用舊版只播放一次的暫存音檔。
