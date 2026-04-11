"""
sync_sheets.py
GitHub Actions 執行此腳本，從 Google Sheets 拉取語料，
輸出 data/27.csv 和 data/data.json。
"""

import os, json, csv, io
import gspread
from google.oauth2.service_account import Credentials

# ── Auth ──────────────────────────────────────────────────────
creds_json = json.loads(os.environ['GOOGLE_CREDENTIALS'])
scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
gc = gspread.authorize(creds)

# ── Read sheet ────────────────────────────────────────────────
SPREADSHEET_ID = os.environ['SPREADSHEET_ID']
sh = gc.open_by_key(SPREADSHEET_ID)
ws = sh.sheet1
print(f"讀取試算表：{sh.title}")

rows = ws.get_all_values()
if len(rows) < 2:
    print("❌ 試算表無資料")
    raise SystemExit(1)

headers = rows[0]
data_rows = [r for r in rows[1:] if any(c.strip() for c in r)]
print(f"共 {len(data_rows)} 列資料，{len(headers)} 個欄位")
print(f"欄位：{headers}")

# ── Write CSV ─────────────────────────────────────────────────
os.makedirs('data', exist_ok=True)

with open('data/27.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(data_rows)
print("✅ data/27.csv 寫入完成")

# ── Write JSON ────────────────────────────────────────────────
# 只保留有值的欄位，縮小檔案體積
records = []
for row in data_rows:
    r = {}
    for i, h in enumerate(headers):
        v = row[i].strip() if i < len(row) else ''
        if v:
            r[h] = v
    if r.get('語句') or r.get('翻譯'):
        records.append(r)

with open('data/data.json', 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, separators=(',', ':'))
print(f"✅ data/data.json 寫入完成（{len(records)} 筆有效資料）")
