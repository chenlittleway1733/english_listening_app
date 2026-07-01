# 英文聽力練習系統

## 安裝套件

```bash
pip install -r requirements.txt
```

## 執行

```bash
streamlit run app.py
```

## 目前版本設計

目前採用「先選等級，再選類型」：

```text
初級 Level 1 / Beginner：暫時沒有類型，以後再新增
中級 Level 2 / Intermediate：目前七大類都放在這裡
高級 Level 3 / Advanced：暫時沒有類型，以後再新增
```

中級目前有七大類：

```text
購物 Shopping-常用3000單
餐廳 Restaurant-常用3000單
學校 School-常用3000單
旅遊 Travel-常用3000單
工作 Work-常用3000單
家庭 Family-常用3000單
朋友 Friends-常用3000單
```

## 題庫資料夾結構

```text
topics/
├─ beginner/
│  └─ .gitkeep
├─ intermediate/
│  ├─ shopping.csv
│  ├─ restaurant.csv
│  ├─ school.csv
│  ├─ travel.csv
│  ├─ work.csv
│  ├─ family.csv
│  └─ friends.csv
└─ advanced/
   └─ .gitkeep
```

音檔會自動產生到：

```text
audio/等級/類型/
```

例如：

```text
audio/intermediate/shopping/1.mp3
```

## 題庫 CSV 必要欄位

```csv
id,type,english,chinese,difficulty
```

例如：

```csv
1,sentence,How much is this?,這個多少錢?,medium
```

## 以後新增初級類型

假設要在初級新增「日常生活 Daily Life-常用3000單」：

1. 新增檔案：

```text
topics/beginner/daily_life.csv
```

2. 在 `app.py` 的 `TOPICS_BY_LEVEL` 中加入：

```python
"beginner": {
    "日常生活 Daily Life-常用3000單": "daily_life",
},
```

## 以後新增高級類型

假設要在高級新增「商務 Business-常用3000單」：

1. 新增檔案：

```text
topics/advanced/business.csv
```

2. 在 `app.py` 的 `TOPICS_BY_LEVEL` 中加入：

```python
"advanced": {
    "商務 Business-常用3000單": "business",
},
```

## 錯題紀錄

答錯會自動記錄到：

```text
wrong_records.csv
```
