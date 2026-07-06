const XLSX = require('xlsx');
const path = require('path');

// 찾을 이름 목록
const targetNames = ['박세영', '김동석', '김준호', '함현식', '김성주', '주경훈', '이동근', '윤태우', '박성준', '주희준'];

const files = [
  '../2026-04_근태현황(4.27~30)_중앙본부_20260504200348.xlsx',
  '../2026-05_근태현황_중앙본부_20260504200341.xlsx'
];

files.forEach(file => {
  console.log('\n========================================');
  console.log('파일:', path.basename(file));
  console.log('========================================');
  
  const wb = XLSX.readFile(path.resolve(__dirname, file));
  const sheetName = wb.SheetNames[0];
  const ws = wb.Sheets[sheetName];
  
  const data = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });
  console.log('헤더행1:', JSON.stringify(data[0]));
  console.log('헤더행2:', JSON.stringify(data[1]));
  
  // 각 대상자 찾기
  targetNames.forEach(name => {
    for (let i = 2; i < data.length; i++) {
      if (data[i][5] === name) {
        console.log(`\n[${name}] 행${i+1}:`, JSON.stringify(data[i]));
      }
    }
  });
});
