"""
sync_letters.py
從「語料_字母」Google Sheets 抓取字母分類資料，轉換為 letters.json。

獨立於既有的 sync_sheets.py，使用獨立的 GitHub Secret：SPREADSHEET_ID_LETTERS。
輸出：data/letters.json

字母資料的處理邏輯與一般語料不同：
  1. 字母組（元音/輔音/符號）需以 (字母編號, 字母, 類型, 族語別, 方言別)
     為主鍵合併多列範例
  2. 注意事項（類型=注意事項）獨立成 notes 陣列，code 用「字母編號」
"""

import os
import json
from collections import defaultdict
import gspread
from google.oauth2.service_account import Credentials


def main():
    # ── Auth ────────────────────────────────────────────────
    creds_json = json.loads(os.environ['GOOGLE_CREDENTIALS'])
    scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
    gc = gspread.authorize(creds)

    SPREADSHEET_ID = os.environ['SPREADSHEET_ID_LETTERS']
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.sheet1
    print(f"讀取試算表：{sh.title}")

    rows = ws.get_all_values()
    if len(rows) < 2:
        print("❌ 試算表無資料")
        raise SystemExit(1)

    headers = rows[0]
    data_rows = [r for r in rows[1:] if any(c.strip() for c in r)]
    print(f"共 {len(data_rows)} 列資料")

    # 建立 header → 索引對照（容許不同欄位順序）
    h = {name: i for i, name in enumerate(headers)}
    required = ['字母編號', '字母', '類型', '發音位置', '發音方式/高低',
                '清濁/唇形', '使用方式', 'IPA', '族語別', '方言別',
                '注意事項', '語句編號', '語句', '翻譯', '音檔']
    missing = [c for c in required if c not in h]
    if missing:
        print(f"❌ 試算表缺少欄位：{missing}")
        raise SystemExit(1)

    def get(row, col):
        idx = h[col]
        return row[idx].strip() if idx < len(row) else ''

    # ── 1) 字母組（元音/輔音/符號）：合併同字母編號+方言別的多列範例 ──
    letter_groups = defaultdict(lambda: {'examples': []})
    for r in data_rows:
        type_ = get(r, '類型')
        if type_ not in ('元音', '輔音', '符號'):
            continue
        letter_no = get(r, '字母編號')
        letter_str = get(r, '字母')  # 已 strip，避免 'ng ' 之類尾隨空白
        lang = get(r, '族語別')
        dial = get(r, '方言別')
        key = (letter_no, letter_str, type_, lang, dial)

        g = letter_groups[key]
        g.update({
            'no':       letter_no,
            'letter':   letter_str,
            'type':     type_,
            'pos':      get(r, '發音位置'),
            'manner':   get(r, '發音方式/高低'),
            'voice':    get(r, '清濁/唇形'),
            'usage':    get(r, '使用方式'),
            'ipa':      get(r, 'IPA'),
            'lang':     lang,
            'dial':     dial,
            'note_ref': get(r, '注意事項') or None,
        })

        sentence = get(r, '語句')
        if sentence:
            audio = get(r, '音檔')
            # 容許音檔欄位寫 .mp3 或不寫；統一去除副檔名讓前端組路徑
            if audio.lower().endswith('.mp3'):
                audio = audio[:-4]
            g['examples'].append({
                'sentence':    sentence,
                'translation': get(r, '翻譯'),
                'audio':       audio or None,
            })

    # ── 2) 注意事項：code 用「字母編號」 ───────────────────
    notes = []
    for r in data_rows:
        if get(r, '類型') != '注意事項':
            continue
        notes.append({
            'code': get(r, '字母編號'),     # 字母列引用的「注意事項」欄位值 == 此 code
            'lang': get(r, '族語別'),
            'text': get(r, '字母'),          # 注意事項全文存在「字母」欄
        })

    output = {
        'letters': list(letter_groups.values()),
        'notes': notes,
    }

    # ── 統計 ──────────────────────────────────────────────
    ec = defaultdict(int)
    for lg in output['letters']:
        ec[len(lg['examples'])] += 1
    print(f"✓ 字母組（合併後）：{len(output['letters'])}")
    print(f"✓ 範例分布：")
    for n in sorted(ec):
        print(f"    {n} 個範例：{ec[n]} 組")
    print(f"✓ 注意事項：{len(output['notes'])} 條")

    # ── Write JSON ───────────────────────────────────────
    os.makedirs('data', exist_ok=True)
    with open('data/letters.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, separators=(',', ':'))
    print(f"✓ 輸出：data/letters.json")


if __name__ == '__main__':
    main()
