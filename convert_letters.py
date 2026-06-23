#!/usr/bin/env python3
"""
convert_letters.py — 將 data_A.csv 轉換為 letters.json

用法：
  python convert_letters.py <輸入 CSV 路徑> <輸出 JSON 路徑>

範例：
  python convert_letters.py data_A.csv www/data/letters.json
"""
import csv
import json
import sys
from collections import defaultdict


def convert(csv_path: str, json_path: str) -> None:
    with open(csv_path, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    # CSV 第一個欄位可能有 BOM
    LET = next(k for k in rows[0].keys() if '字母編號' in k)

    # 1) 字母組（元音/輔音/符號）：以 (字母編號, 字母, 類型, 族語別, 方言別) 主鍵合併範例
    letter_groups: dict = defaultdict(lambda: {'examples': []})
    for r in rows:
        if r['類型'] not in ('元音', '輔音', '符號'):
            continue
        key = (r[LET], r['字母'], r['類型'], r['族語別'], r['方言別'])
        g = letter_groups[key]
        g.update({
            'no':       r[LET].strip(),
            'letter':   r['字母'],
            'type':     r['類型'],
            'pos':      r['發音位置'].strip(),
            'manner':   r['發音方式/高低'].strip(),
            'voice':    r['清濁/唇形'].strip(),
            'usage':    r['使用方式'].strip(),
            'ipa':      r['IPA'].strip(),
            'lang':     r['族語別'],
            'dial':     r['方言別'],
            'note_ref': r['注意事項'].strip() or None,
        })
        if r['語句']:
            g['examples'].append({
                'sentence':    r['語句'],
                'translation': r['翻譯'],
                'audio':       r['音檔'].strip() or None,
            })

    # 2) 注意事項：以「語句編號」前 4 碼為代號，內容存在「字母」欄
    notes = []
    for r in rows:
        if r['類型'] != '注意事項':
            continue
        sent_no = r['語句編號'].strip()
        note_code = sent_no[:4] if len(sent_no) >= 4 else sent_no
        notes.append({
            'code': note_code,
            'lang': r['族語別'],
            'text': r['字母'],
        })

    output = {
        'letters': list(letter_groups.values()),
        'notes': notes,
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, separators=(',', ':'))

    # 統計
    example_counts: dict = defaultdict(int)
    for lg in output['letters']:
        example_counts[len(lg['examples'])] += 1
    print(f'✓ 字母組（合併後）：{len(output["letters"])}')
    print(f'✓ 範例分布：')
    for n in sorted(example_counts):
        print(f'    {n} 個範例：{example_counts[n]} 組')
    print(f'✓ 注意事項：{len(output["notes"])} 條')
    print(f'✓ 輸出：{json_path}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
