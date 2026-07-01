# 英文聽力練習系統 v8

## 本版重點

1. 把「等級、類型、出題來源」改放在主畫面，不放側邊欄，避免側邊欄收合時看不到選項。
2. 頁面說明文字改得更清楚：
   - 一般隨機出題：從目前等級與類型的 CSV 題庫隨機抽一句。
   - 錯題記錄出題：只從目前等級與類型的錯題記錄抽題。
3. 錯題記錄出題選項會直接顯示在主畫面第 3 步。
4. 錯題模式下，答對後會把該句子從 `wrong_records.csv` 移除。
5. 一般模式下，答錯會加入錯題記錄；同一句答錯多次不重複新增，而是增加 `wrong_count`。
6. 音檔使用暫存資料夾，不會寫入專案內的 `audio/`，避免 Streamlit Cloud 出現 `NotADirectoryError`。
7. 每題按一次播放，英文句子會連續唸兩次。

## 執行方式

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 題庫位置

```text
topics/
├─ beginner/
├─ intermediate/
│  ├─ shopping.csv
│  ├─ restaurant.csv
│  ├─ school.csv
│  ├─ travel.csv
│  ├─ work.csv
│  ├─ family.csv
│  └─ friends.csv
└─ advanced/
```

目前 Shopping-常用3000單 已有 100 句。

## 錯題記錄

系統會自動建立：

```text
wrong_records.csv
```

錯題記錄會依照 `level_key + topic_key + id + english` 判斷同一句。  
同一句答錯多次時，不會一直新增重複列，而是增加 `wrong_count`。
