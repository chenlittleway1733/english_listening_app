# 英文聽力練習系統 v7

## 本版重點

1. 目前七大類型都放在「中級 Level 2 / Intermediate」。
2. 題目會依照目前選定的「等級 + 類型」隨機出題。
3. 新增「出題來源」選項：
   - 一般隨機出題：從目前類型的 CSV 題庫隨機出題。
   - 錯題記錄出題：只從目前類型的錯題記錄出題。
4. 錯題模式下，答對後會把該句子從 `wrong_records.csv` 移除。
5. 一般模式下，答錯會加入錯題記錄；答對也會順手移除同一句的舊錯題。
6. 音檔仍使用暫存資料夾，不會寫入專案內的 `audio/`，避免 Streamlit Cloud 出現 `NotADirectoryError`。
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
