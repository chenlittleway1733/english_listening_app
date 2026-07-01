# 英文聽力練習系統

## 安裝套件

```bash
pip install -r requirements.txt
```

## 執行

```bash
streamlit run app.py
```

## 題庫位置

題目放在 `topics/` 資料夾中，每個主題一個 CSV。

必要欄位：

```csv
id,type,english,chinese,difficulty
```

例如：

```csv
1,sentence,How much is this?,這個多少錢?,easy
```

## 新增主題

1. 在 `topics/` 新增 CSV，例如 `hotel.csv`
2. 在 `app.py` 的 `TOPICS` 加入：

```python
"飯店 Hotel": "hotel"
```
