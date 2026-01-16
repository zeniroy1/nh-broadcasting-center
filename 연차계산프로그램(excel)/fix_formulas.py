import zipfile
import shutil
import re
import os
import tempfile

# File paths
original_file = '⁕연차·반차(26.1~) - 방송운영단.xlsx'
output_file = '⁕연차·반차(26.1~) - 방송운영단_수정본.xlsx'

# Delete old output file if exists
if os.path.exists(output_file):
    os.remove(output_file)

print("=== Excel 수식 수정 시작 ===\n")

# Create a temp directory
temp_dir = tempfile.mkdtemp()
extract_dir = os.path.join(temp_dir, 'xlsx_contents')

try:
    # Extract the xlsx file (it's a zip file)
    with zipfile.ZipFile(original_file, 'r') as z:
        z.extractall(extract_dir)
    
    print("1. Excel 파일 압축 해제 완료")
    
    # Read and modify sheet1.xml
    sheet_path = os.path.join(extract_dir, 'xl', 'worksheets', 'sheet1.xml')
    with open(sheet_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("2. 시트 내용 읽기 완료")
    
    # New formula for 근속기간 (E column)
    # 1년 미만: "N개월 N일" 또는 "N일"
    # 1년 이상: "N년 N개월 N일"
    new_tenure_formula = '''IF(OR(D{row}="",NOT(ISNUMBER(D{row}))),"",IF(DATEDIF(D{row},$C$2,"Y")&gt;=1,DATEDIF(D{row},$C$2,"Y")&amp;"년 "&amp;DATEDIF(D{row},$C$2,"YM")&amp;"개월 "&amp;DATEDIF(D{row},$C$2,"MD")&amp;"일",IF(DATEDIF(D{row},$C$2,"M")&gt;=1,DATEDIF(D{row},$C$2,"M")&amp;"개월 "&amp;DATEDIF(D{row},$C$2,"MD")&amp;"일",DATEDIF(D{row},$C$2,"D")&amp;"일")))'''
    
    # New formula for 근속연수 (F column) - use $C$2 instead of $C$2+1
    new_years_formula = '''IF(OR(D{row}="",NOT(ISNUMBER(D{row}))),"",DATEDIF(D{row},$C$2,"Y"))'''
    
    updated_count = 0
    
    # Update E column formulas
    print("\n3. E열 (근속기간) 수식 수정 중...")
    for row in [5, 8, 11, 14, 17, 20, 23, 26, 29, 32]:
        cell_ref = f"E{row}"
        new_formula = new_tenure_formula.format(row=row)
        
        # Find and replace the formula in the cell
        # Pattern: <c r="E5" ...><f>OLD_FORMULA</f>...
        pattern = rf'(<c r="{cell_ref}"[^>]*>.*?<f[^>]*>)([^<]*)(</f>)'
        
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, rf'\1{new_formula}\3', content, count=1, flags=re.DOTALL)
            print(f"  ✓ {cell_ref} 수정 완료")
            updated_count += 1
    
    # Update F column formulas
    print("\n4. F열 (근속연수) 수식 수정 중...")
    for row in [5, 8, 11, 14, 17, 20, 23, 26, 29, 32]:
        cell_ref = f"F{row}"
        new_formula = new_years_formula.format(row=row)
        
        pattern = rf'(<c r="{cell_ref}"[^>]*>.*?<f[^>]*>)([^<]*)(</f>)'
        
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, rf'\1{new_formula}\3', content, count=1, flags=re.DOTALL)
            print(f"  ✓ {cell_ref} 수정 완료")
            updated_count += 1
    
    print(f"\n   → 총 {updated_count}개 셀 수정")
    
    # Save modified sheet
    with open(sheet_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n5. 수정된 시트 저장 완료")
    
    # Repack as xlsx with correct compression
    print("6. Excel 파일 재압축 중...")
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, extract_dir)
                # Use forward slashes for zip archive
                arcname = arcname.replace('\\', '/')
                z.write(file_path, arcname)
    
    print(f"\n=== 수정 완료 ===")
    print(f"수정된 파일: {output_file}")
    print(f"파일 크기: {os.path.getsize(output_file):,} bytes")
    
finally:
    # Cleanup temp directory
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

print("\n변경 사항:")
print("  • 근속기간 (E열): 1년 미만은 '개월 일' 또는 '일'로만 표시")
print("  • 근속연수 (F열): 기준일 $C$2로 통일")
print("  • 기본, 가산, 합계 수식은 기존과 동일 (이미 올바르게 작동)")
