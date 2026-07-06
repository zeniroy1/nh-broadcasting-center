const XLSX = require('xlsx');
const path = require('path');

const files = [
  '../2026-04_근태현황(4.27~30)_중앙본부_20260504200348.xlsx',
  '../2026-05_근태현황_중앙본부_20260504200341.xlsx'
];

files.forEach(file => {
  console.log('\n========================================');
  console.log('파일:', path.basename(file));
  console.log('========================================');
  
  const wb = XLSX.readFile(path.resolve(__dirname, file));
  console.log('시트 목록:', wb.SheetNames);
  
  wb.SheetNames.forEach(sheetName => {
    console.log('\n--- 시트:', sheetName, '---');
    const ws = wb.Sheets[sheetName];
    const range = ws['!ref'];
    console.log('범위:', range);
    
    // 처음 20행 출력
    const data = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });
    console.log('총 행수:', data.length);
    console.log('\n처음 30행 내용:');
    data.slice(0, 30).forEach((row, i) => {
      const nonEmpty = row.filter(c => c !== '');
      if (nonEmpty.length > 0) {
        console.log(`행${i+1}:`, JSON.stringify(row));
      }
    });
  });
});
