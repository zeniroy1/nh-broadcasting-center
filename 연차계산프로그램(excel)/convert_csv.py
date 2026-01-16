import csv
import json
import os

# Get directory and find CSV file
csv_file = '⁕연차·반차(26.1~) - 방송운영단.csv'

# Try different encodings
encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr']
content = None
used_encoding = None

for enc in encodings:
    try:
        with open(csv_file, 'r', encoding=enc) as f:
            content = f.read()
            used_encoding = enc
            print(f'Successfully read with encoding: {enc}')
            break
    except Exception as e:
        print(f'Failed with {enc}: {e}')

if content:
    # Parse CSV
    lines = content.strip().split('\n')
    print(f'Total lines: {len(lines)}')
    print('\n--- First 50 lines ---')
    for i, line in enumerate(lines[:50]):
        print(f'{i+1}: {line}')
    
    # Also save as JSON for easier processing
    reader = csv.reader(lines)
    data = list(reader)
    
    with open('연차_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'\nSaved JSON to 연차_data.json')
