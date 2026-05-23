"""
sync_sheets.py
GitHub Actions 執行此腳本，從多個 Google Sheets 拉取語料（依語族分流），
輸出 data/index.json 和 data/dial_XX.json（每個方言別一個檔案）。
"""

import os, json, csv
from datetime import datetime, timezone
import gspread
from google.oauth2.service_account import Credentials

# ── Auth ──────────────────────────────────────────────────────
creds_json = json.loads(os.environ['GOOGLE_CREDENTIALS'])
scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
gc = gspread.authorize(creds)

# ── Spreadsheet ID mapping ────────────────────────────────────
# Each env var maps to one spreadsheet covering certain dialects
SPREADSHEET_IDS = {
    'SPREADSHEET_ID_AMIS':   '語料_阿美（阿美語、噶瑪蘭語、撒奇萊雅語）',
    'SPREADSHEET_ID_ATAYAL': '語料_泰雅（泰雅語、賽夏語）',
    'SPREADSHEET_ID_SEEDIQ': '語料_賽德克（賽德克語、太魯閣語）',
    'SPREADSHEET_ID_BUNUN':  '語料_布農（布農語、邵語）',
    'SPREADSHEET_ID_PAIWAN': '語料_排灣（排灣語）',
    'SPREADSHEET_ID_RUKAI':  '語料_魯凱（魯凱語）',
    'SPREADSHEET_ID_PUYUMA': '語料_卑南（卑南語）',
    'SPREADSHEET_ID_TSOU':   '語料_鄒（鄒語、卡那卡那富語、拉阿魯哇語、雅美語）',
}

# ── Helper: pad dial ID ───────────────────────────────────────
def pad_dial(raw):
    raw = str(raw).strip().replace('.0','')
    if not raw or raw == '0': return ''
    try:
        n = int(float(raw))
        return f'{n:02d}' if n < 10 else str(n)
    except:
        return raw

# ── Read all spreadsheets ─────────────────────────────────────
os.makedirs('data', exist_ok=True)
all_records = []
headers_ref = None

for env_key, desc in SPREADSHEET_IDS.items():
    sid = os.environ.get(env_key, '').strip()
    if not sid:
        print(f'⚠ {env_key} 未設定，略過（{desc}）')
        continue
    try:
        sh = gc.open_by_key(sid)
        ws = sh.sheet1
        rows = ws.get_all_values()
        if len(rows) < 2:
            print(f'⚠ {desc}：無資料')
            continue
        headers = rows[0]
        if headers_ref is None:
            headers_ref = headers
        data_rows = [r for r in rows[1:] if any(c.strip() for c in r)]
        n_cols = len(headers)
        count = 0
        for row in data_rows:
            padded = row + [''] * (n_cols - len(row))
            r = {}
            for i, h in enumerate(headers):
                v = padded[i].strip() if i < len(padded) else ''
                if v:
                    r[h] = v
            if r.get('語句') or r.get('翻譯'):
                all_records.append(r)
                count += 1
        print(f'✅ {desc}：{count} 筆')
    except Exception as e:
        print(f'❌ {desc} 讀取失敗：{e}')

print(f'\n合計：{len(all_records)} 筆資料')

if not all_records:
    print('❌ 無任何資料，中止')
    raise SystemExit(1)

headers = headers_ref or ['編號','分類','等級','分類1','分類2','分類3','分類4','語句','翻譯','音檔路徑','語別','方言別','備註']

# ── Write full CSV ────────────────────────────────────────────
with open('data/data.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(all_records)
print('✅ data/data.csv 寫入完成')

# ── Group by 方言別（無方言別者用語別代號）────────────────────
dial_groups = {}
for r in all_records:
    dial = pad_dial(r.get('方言別',''))
    if not dial:
        lang_id = str(r.get('語別','')).strip()
        if lang_id:
            dial = pad_dial(lang_id)
    if dial:
        if dial not in dial_groups:
            dial_groups[dial] = []
        dial_groups[dial].append(r)
    else:
        print(f'⚠ 無法識別方言/語別，略過：{r.get("語句","")[:20]}')

# ── Write per-dialect JSON ────────────────────────────────────
for dial_id, recs in sorted(dial_groups.items()):
    fname = f'data/dial_{dial_id}.json'
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(recs, f, ensure_ascii=False, separators=(',',':'))
    print(f'✅ {fname}（{len(recs)} 筆）')

# ── Write index.json ──────────────────────────────────────────
sync_ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
lang_map = {}
for r in all_records:
    dial = pad_dial(r.get('方言別',''))
    if not dial:
        lang_id = str(r.get('語別','')).strip()
        if lang_id:
            dial = pad_dial(lang_id)
    if dial and dial not in lang_map:
        lang_map[dial] = r.get('語別','')

index_data = [
    {
        'dialId': dial,
        'lang': lang_map.get(dial,''),
        'count': len(recs),
        'updatedAt': sync_ts
    }
    for dial, recs in sorted(dial_groups.items())
]

with open('data/index.json', 'w', encoding='utf-8') as f:
    json.dump(index_data, f, ensure_ascii=False, separators=(',',':'))
print(f'✅ data/index.json（{len(index_data)} 個方言）')

# ── Write combined data.json for fallback ─────────────────────
with open('data/data.json', 'w', encoding='utf-8') as f:
    json.dump(all_records, f, ensure_ascii=False, separators=(',',':'))
print(f'✅ data/data.json（{len(all_records)} 筆，備用）')

print(f'\n🎉 同步完成：{len(all_records)} 筆資料，{len(dial_groups)} 個方言')
