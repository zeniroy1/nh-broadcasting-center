const ExcelJS = require('exceljs');
const path = require('path');
const fs = require('fs');

// 대상자 순서
const targetNames = ['박세영', '김동석', '김준호', '함현식', '김성주', '주경훈', '이동근', '윤태우', '박성준', '주희준'];

// thin 테두리
const thinBorder = {
  left:   { style: 'thin' },
  right:  { style: 'thin' },
  top:    { style: 'thin' },
  bottom: { style: 'thin' }
};

// 배경색 없음
const noFill = { type: 'pattern', pattern: 'none' };

const baseFontWhite = { size: 11, color: { indexed: 8 }, name: '맑은 고딕', family: 2, scheme: 'minor' };

// 셀 값 추출 (RichText / null 처리)
function getCellText(cell) {
  const v = cell.value;
  if (v === null || v === undefined) return '';
  if (typeof v === 'object' && v.richText) {
    return v.richText.map(t => t.text).join('');
  }
  return String(v);
}

// \r\n → \n (Excel 줄바꿈)
function normalizeLineBreak(text) {
  if (!text) return '';
  return text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
}

async function createFile(srcPath, outPath, label) {
  console.log(`\n[${label} 처리 중...]`);

  const srcWb = new ExcelJS.Workbook();
  await srcWb.xlsx.readFile(srcPath);
  const srcWs = srcWb.worksheets[0];

  // 대상자 행 수집
  const foundRows = {};
  srcWs.eachRow({ includeEmpty: false }, (row, rowNum) => {
    if (rowNum <= 2) return;
    const name = getCellText(row.getCell(6));
    if (targetNames.includes(name)) {
      if (!foundRows[name]) foundRows[name] = [];
      foundRows[name].push(row);
    }
  });

  const colCount = srcWs.columnCount || 11;

  // 원본 컬럼 너비 수집
  const colWidths = [];
  for (let c = 1; c <= colCount; c++) {
    colWidths.push(srcWs.getColumn(c).width || 10);
  }

  // 새 워크북 생성
  const newWb = new ExcelJS.Workbook();
  newWb.created = new Date();
  const newWs = newWb.addWorksheet('Sheet1');

  // 컬럼 너비 설정
  for (let c = 1; c <= colCount; c++) {
    newWs.getColumn(c).width = colWidths[c - 1];
  }

  // 헤더 행 1 복사
  const hdr1 = srcWs.getRow(1);
  const newHdr1 = newWs.getRow(1);
  newHdr1.height = hdr1.height || 20;
  hdr1.eachCell({ includeEmpty: true }, (cell, colNum) => {
    if (colNum > colCount) return;
    const newCell = newHdr1.getCell(colNum);
    newCell.value = getCellText(cell) || null;
    newCell.border = thinBorder;
    newCell.fill = noFill;
    newCell.font = { ...baseFontWhite, ...(cell.font || {}) };
    newCell.alignment = { horizontal: 'center', vertical: 'middle', wrapText: true };
  });

  // 헤더 행 2 복사
  const hdr2 = srcWs.getRow(2);
  const newHdr2 = newWs.getRow(2);
  newHdr2.height = hdr2.height || 20;
  hdr2.eachCell({ includeEmpty: true }, (cell, colNum) => {
    if (colNum > colCount) return;
    const newCell = newHdr2.getCell(colNum);
    newCell.value = getCellText(cell) || null;
    newCell.border = thinBorder;
    newCell.fill = noFill;
    newCell.font = { ...baseFontWhite, ...(cell.font || {}) };
    newCell.alignment = { horizontal: 'center', vertical: 'middle', wrapText: true };
  });

  // 데이터 행 작성 (지정 순서)
  let newRowNum = 3;

  for (const name of targetNames) {
    if (!foundRows[name]) {
      console.warn(`  [경고] "${name}" 을 찾지 못했습니다.`);
      continue;
    }
    for (const srcRow of foundRows[name]) {
      const newRow = newWs.getRow(newRowNum);
      newRow.height = srcRow.height || 36;

      srcRow.eachCell({ includeEmpty: true }, (cell, colNum) => {
        if (colNum > colCount) return;
        const newCell = newRow.getCell(colNum);

        // A열 번호는 원본 그대로 복사
        const text = normalizeLineBreak(getCellText(cell));
        newCell.value = text || null;

        newCell.border = thinBorder;
        newCell.font = { ...baseFontWhite, ...(cell.font || {}) };
        newCell.alignment = { horizontal: 'center', vertical: 'middle', wrapText: true };
        newCell.fill = { type: 'pattern', pattern: 'none' };
      });

      // 빈 셀에도 테두리 적용
      for (let c = 1; c <= colCount; c++) {
        const newCell = newRow.getCell(c);
        if (!newCell.border) {
          newCell.border = thinBorder;
          newCell.alignment = { horizontal: 'center', vertical: 'middle', wrapText: true };
          newCell.fill = { type: 'pattern', pattern: 'none' };
        }
      }

      newRowNum++;
    }
  }

  await newWb.xlsx.writeFile(outPath);
  console.log(`  ✅ 저장 완료: ${outPath}`);
  console.log(`     데이터 ${newRowNum - 3}행`);
}

// 원본 파일명에서 날짜 부분 자동 추출
// 예) 2026-04_근태현황(4.27~30)_중앙본부_...xlsx → 2026-04(4.27~30)
// 예) 2026-05_근태현황_중앙본부_...xlsx         → 2026-05
function extractDateSuffix(filename) {
  const base = path.basename(filename, '.xlsx');
  const match = base.match(/^(\d{4}-\d{2})_근태현황(\([^)]*\))?_/);
  if (!match) return null;
  return match[1] + (match[2] || '');
}

async function main() {
  const isCompiled = typeof process.pkg !== 'undefined';
  // exe 파일로 실행될 때는 exe 파일이 있는 곳이 기준, 스크립트로 실행될 때는 상위 폴더가 기준
  const srcDir = isCompiled ? path.dirname(process.execPath) : path.resolve(__dirname, '..');

  // 근태관리 폴더에서 원본 파일 자동 탐색 (농협방송단_ 제외)
  const srcFiles = fs.readdirSync(srcDir)
    .filter(f => f.endsWith('.xlsx') && !f.startsWith('농협방송단_') && !f.startsWith('~$'))
    .map(f => path.join(srcDir, f));

  if (srcFiles.length === 0) {
    console.log('처리할 원본 파일이 없습니다.');
    return;
  }

  for (const srcFile of srcFiles) {
    const dateSuffix = extractDateSuffix(srcFile);
    if (!dateSuffix) {
      console.warn(`[스킵] 파일명 패턴 불일치: ${path.basename(srcFile)}`);
      continue;
    }
    const outFile = path.join(srcDir, `농협방송단_근태현황_${dateSuffix}.xlsx`);
    await createFile(srcFile, outFile, dateSuffix);
  }

  console.log('\n✅ 전체 완료!');
  
  // 실행 완료 후 창이 바로 닫히지 않게 대기
  if (isCompiled) {
    const readline = require('readline');
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    rl.question('\n엔터 키를 누르면 창이 닫힙니다...', () => {
      rl.close();
    });
  }
}

main().catch(err => {
  console.error('오류:', err);
  process.exit(1);
});
