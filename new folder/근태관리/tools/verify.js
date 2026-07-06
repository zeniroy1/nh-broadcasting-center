const ExcelJS = require('exceljs');
const path = require('path');

async function verify() {
  const wb = new ExcelJS.Workbook();
  await wb.xlsx.readFile(path.resolve(__dirname, '../방송팀_근태현황_2026-05.xlsx'));
  const ws = wb.worksheets[0];

  console.log('=== 헤더 확인 ===');
  const row1 = ws.getRow(1);
  const row2 = ws.getRow(2);
  const h1vals = [], h2vals = [];
  row1.eachCell({ includeEmpty: true }, (c, i) => { if (i <= 10) h1vals.push(c.value); });
  row2.eachCell({ includeEmpty: true }, (c, i) => { if (i <= 10) h2vals.push(c.value); });
  console.log('행1:', h1vals);
  console.log('행2:', h2vals);

  console.log('\n=== 데이터 행 확인 (이름 + 4월4일 출퇴근) ===');
  for (let r = 3; r <= 12; r++) {
    const row = ws.getRow(r);
    const name = row.getCell(6).value;
    const col4val = row.getCell(10).value; // 04일 컬럼(6+4=10번째)
    const wrapText = row.getCell(6).alignment?.wrapText;
    const border = row.getCell(6).border?.left?.style;
    console.log(`행${r}: ${name} | 04일="${col4val}" | wrapText=${wrapText} | border=${border}`);
  }
}

verify().catch(console.error);
