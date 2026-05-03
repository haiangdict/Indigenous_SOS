"""
sync_sheets.py
GitHub Actions 執行此腳本，從 Google Sheets 拉取語料，
輸出 data/index.json 和 data/dial_XX.json（每個方言別一個檔案）。
"""

import os, json, csv
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

# ── Helper: pad dial ID ───────────────────────────────────────
def pad_dial(raw):
    raw = str(raw).strip().replace('.0','')
    if not raw or raw == '0': return ''
    try:
        n = int(float(raw))
        return f'{n:02d}' if n < 10 else str(n)
    except:
        return raw

# ── Write full CSV (for backward compat) ─────────────────────
os.makedirs('data', exist_ok=True)

with open('data/data.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(data_rows)
print("✅ data/data.csv 寫入完成")

# ── Build records list ────────────────────────────────────────
records = []
for row in data_rows:
    r = {}
    for i, h in enumerate(headers):
        v = row[i].strip() if i < len(row) else ''
        if v:
            r[h] = v
    if r.get('語句') or r.get('翻譯'):
        records.append(r)

print(f"有效資料：{len(records)} 筆")

# ── Group by 方言別 ────────────────────────────────────────────
dial_groups = {}
no_dial = []
for r in records:
    dial = pad_dial(r.get('方言別',''))
    if dial:
        if dial not in dial_groups:
            dial_groups[dial] = []
        dial_groups[dial].append(r)
    else:
        no_dial.append(r)

if no_dial:
    print(f"⚠ 無方言別資料：{len(no_dial)} 筆（略過）")

# ── Write per-dialect JSON files ───────────────────────────────
for dial_id, recs in sorted(dial_groups.items()):
    fname = f'data/dial_{dial_id}.json'
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(recs, f, ensure_ascii=False, separators=(',',':'))
    print(f"✅ {fname}（{len(recs)} 筆）")

# ── Write index.json ──────────────────────────────────────────
lang_map = {}
for r in records:
    dial = pad_dial(r.get('方言別',''))
    if dial and dial not in lang_map:
        lang_map[dial] = r.get('語別','')

index_data = [
    {
        'dialId': dial,
        'lang': lang_map.get(dial,''),
        'count': len(recs)
    }
    for dial, recs in sorted(dial_groups.items())
]

with open('data/index.json', 'w', encoding='utf-8') as f:
    json.dump(index_data, f, ensure_ascii=False, separators=(',',':'))
print(f"✅ data/index.json（{len(index_data)} 個方言）")

# ── Also write combined data.json for fallback ───────────────
with open('data/data.json', 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, separators=(',',':'))
print(f"✅ data/data.json（{len(records)} 筆，備用）")

print(f"\n🎉 同步完成：{len(records)} 筆資料，{len(dial_groups)} 個方言")
