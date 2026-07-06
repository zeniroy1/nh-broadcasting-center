const ExcelJS = require('exceljs');
const path = require('path');

async function inspectStyles() {
  const wb = new ExcelJS.Workbook();
  await wb.xlsx.readFile(path.resolve(__dirname, '../2026-05_근태현황_중앙본부_20260504200341.xlsx'));
  
  const ws = wb.worksheets[0];
  
  console.log('=== 컬럼 정보 ===');
  ws.columns.forEach((col, i) => {
    console.log(`컬럼 ${i+1} (${col.letter}): width=${col.width}`);
  });
  
  console.log('\n=== 행 높이 ===');
  for (let r = 1; r <= 5; r++) {
    const row = ws.getRow(r);
    console.log(`행 ${r}: height=${row.height}`);
  }
  
  console.log('\n=== 셀 서식 샘플 (행1~3, 컬럼1~8) ===');
  for (let r = 1; r <= 3; r++) {
    for (let c = 1; c <= 8; c++) {
      const cell = ws.getCell(r, c);
      const border = cell.border;
      const fill = cell.fill;
      const font = cell.font;
      const align = cell.alignment;
      console.log(`  셀(${r},${c}) val="${cell.value}" font=${JSON.stringify(font)} border=${JSON.stringify(border)} fill=${JSON.stringify(fill)} align=${JSON.stringify(align)}`);
    }
  }
  
  // 데이터 행 샘플 (행3)
  console.log('\n=== 데이터행 샘플 (행5) ===');
  const row5 = ws.getRow(5);
  row5.eachCell({ includeEmpty: true }, (cell, colNumber) => {
    if (colNumber <= 10) {
      console.log(`  셀(5,${colNumber}) val="${cell.value}" align=${JSON.stringify(cell.alignment)} border=${JSON.stringify(cell.border)}`);
    }
  });
}

inspectStyles().catch(console.error);
