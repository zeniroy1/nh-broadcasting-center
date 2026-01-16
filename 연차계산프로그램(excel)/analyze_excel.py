import zipfile
import xml.etree.ElementTree as ET
import re
import json

# Excel xlsx files are zip archives
xlsx_file = '⁕연차·반차(26.1~) - 방송운영단.xlsx'

with zipfile.ZipFile(xlsx_file, 'r') as z:
    print("=== Excel 파일 구조 ===")
    files = z.namelist()
    for f in files:
        print(f"  {f}")
    
    print("\n=== 시트 목록 ===")
    # Read workbook.xml to get sheet names
    try:
        workbook_xml = z.read('xl/workbook.xml').decode('utf-8')
        sheets = re.findall(r'<sheet[^>]*name="([^"]*)"[^>]*/>', workbook_xml)
        for i, sheet in enumerate(sheets, 1):
            print(f"  {i}. {sheet}")
    except Exception as e:
        print(f"  Error reading workbook: {e}")
    
    print("\n=== 수식 찾기 ===")
    formulas = []
    
    # Check each sheet for formulas
    sheet_files = [f for f in files if f.startswith('xl/worksheets/sheet') and f.endswith('.xml')]
    
    for sheet_file in sheet_files:
        print(f"\n--- {sheet_file} ---")
        try:
            content = z.read(sheet_file).decode('utf-8')
            
            # Find all formulas using regex
            formula_matches = re.findall(r'<f[^>]*>([^<]+)</f>', content)
            
            # Find cell references with formulas
            cell_formula_pattern = r'<c r="([A-Z]+\d+)"[^>]*>.*?<f[^>]*>([^<]+)</f>'
            cell_formulas = re.findall(cell_formula_pattern, content, re.DOTALL)
            
            if cell_formulas:
                print(f"  총 {len(cell_formulas)}개의 수식 발견")
                
                # Show unique formulas
                unique_formulas = {}
                for cell, formula in cell_formulas:
                    # Normalize formula pattern
                    pattern = re.sub(r'\d+', 'N', formula)
                    if pattern not in unique_formulas:
                        unique_formulas[pattern] = (cell, formula)
                
                print(f"\n  고유한 수식 패턴 ({len(unique_formulas)}개):")
                for pattern, (cell, formula) in list(unique_formulas.items())[:30]:
                    print(f"    [{cell}] {formula}")
            else:
                # Alternative search
                all_formulas = re.findall(r'<f(?:\s[^>]*)?>([^<]+)</f>', content)
                if all_formulas:
                    print(f"  총 {len(all_formulas)}개의 수식 발견")
                    unique = list(set(all_formulas))[:30]
                    for f in unique:
                        print(f"    {f}")
                else:
                    print("  수식 없음")
                    
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n=== 스타일 정보 ===")
    try:
        styles_xml = z.read('xl/styles.xml').decode('utf-8')
        # Count number of style definitions
        num_fills = len(re.findall(r'<fill>', styles_xml))
        num_fonts = len(re.findall(r'<font>', styles_xml))
        num_borders = len(re.findall(r'<border>', styles_xml))
        print(f"  색상/채우기: {num_fills}개")
        print(f"  폰트 스타일: {num_fonts}개")
        print(f"  테두리 스타일: {num_borders}개")
    except Exception as e:
        print(f"  Error reading styles: {e}")
    
    print("\n=== 조건부 서식 ===")
    for sheet_file in sheet_files:
        try:
            content = z.read(sheet_file).decode('utf-8')
            cond_formats = re.findall(r'<conditionalFormatting[^>]*sqref="([^"]*)"[^>]*>(.*?)</conditionalFormatting>', content, re.DOTALL)
            if cond_formats:
                print(f"\n  {sheet_file}:")
                for sqref, rules in cond_formats:
                    formulas_in_cf = re.findall(r'<formula>([^<]+)</formula>', rules)
                    print(f"    범위: {sqref}")
                    for f in formulas_in_cf:
                        print(f"      조건: {f}")
        except:
            pass

print("\n분석 완료!")
