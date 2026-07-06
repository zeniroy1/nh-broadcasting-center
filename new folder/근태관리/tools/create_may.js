const ExcelJS = require('exceljs');
const path = require('path');

// 대상자 순서
const targetNames = ['박세영', '김동석', '김준호', '함현식', '김성주', '주경훈', '이동근', '윤태우', '박성준', '주희준'];

const srcFile = path.resolve(__dirname, '../2026-05_근태현황_중앙본부_20260504200341.xlsx');
const outFile = path.resolve(__dirname, '../방송팀_근태현황_2026-05.xlsx');

// thin 테두리 정의
const thinBorder = {
  left:   { style: 'thin' },
  right:  { style: 'thin' },
  top:    { style: 'thin' },
  bottom: { style: 'thin' }
};

// 헤더 배경색 (원본: indexed 22 = 연노랑)
const headerFill = {
  type: 'pattern',
  pattern: 'solid',
  fgColor: { indexed: 22 }
};

// 기본 폰트
const baseFont = { size: 11, name: '맑은 고딕', family: 2, scheme: 'minor' };
const baseFontWhite = { size: 11, color: { indexed: 8 }, name: '맑은 고딕', family: 2, scheme: 'minor' };

// 셀에서 실제 문자열 값 추출 (RichText / null 처리)
function getCellText(cell) {
  const v = cell.value;
  if (v === null || v === undefined) return '';
  if (typeof v === 'object' && v.richText) {
    return v.richText.map(t => t.text).join('');
  }
  return String(v);
}

// \r\n을 실제 줄바꿈으로 처리 (ExcelJS는 \n으로 줄바꿈)
function normalizeLineBreak(text) {
  if (!text) return '';
  return text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
}

async function run() {
  // 원본 읽기
  const srcWb = new ExcelJS.Workbook();
  await srcWb.xlsx.readFile(srcFile);
  const srcWs = srcWb.worksheets[0];

  // 원본에서 대상자 행 수집 (이름 기준)
  const foundRows = {};
  srcWs.eachRow({ includeEmpty: false }, (row, rowNum) => {
    if (rowNum <= 2) return; // 헤더 스킵
    const name = getCellText(row.getCell(6));
    if (targetNames.includes(name)) {
      if (!foundRows[name]) foundRows[name] = [];
      foundRows[name].push(row);
    }
  });

  // 원본 헤더행 1, 2 셀 데이터 수집
  const hdr1 = srcWs.getRow(1);
  const hdr2 = srcWs.getRow(2);
  const colCount = srcWs.columnCount || 38; // 원본 컬럼 수

  // 원본 컬럼 너비 수집
  const colWidths = [];
  for (let c = 1; c <= colCount; c++) {
    const col = srcWs.getColumn(c);
    colWidths.push(col.width || 10);
  }

  // ===== 새 워크북 생성 =====
  const newWb = new ExcelJS.Workbook();
  newWb.creator = srcWb.creator || '방송팀';
  newWb.created = new Date();

  const newWs = newWb.addWorksheet('Sheet1');

  // 컬럼 너비 설정
  for (let c = 1; c <= colCount; c++) {
    newWs.getColumn(c).width = colWidths[c - 1];
  }

  // ===== 헤더 행 1 복사 =====
  const newHdr1 = newWs.getRow(1);
  newHdr1.height = hdr1.height || 20;
  hdr1.eachCell({ includeEmpty: true }, (cell, colNum) => {
    if (colNum > colCount) return;
    const newCell = newHdr1.getCell(colNum);
    newCell.value = getCellText(cell) || null;
    newCell.border = thinBorder;
    newCell.fill = headerFill;
    newCell.font = { ...baseFontWhite };
    newCell.alignment = { horizontal: 'center', vertical: 'middle', wrapText: true };
  });

  // ===== 헤더 행 2 복사 =====
  const newHdr2 = newWs.getRow(2);
  newHdr2.height = hdr2.height || 20;
  hdr2.eachCell({ includeEmpty: true }, (cell, colNum) => {
    if (colNum > colCount) return;
    const newCell = newHdr2.getCell(colNum);
    const txt = getCellText(cell);
    newCell.value = txt || null;
    newCell.border = thinBorder;
    newCell.fill = headerFill;
    // 토/일은 원본에서 다른 색(빨강 indexed:10)
    const srcFont = cell.font || {};
    newCell.font = { ...baseFontWhite, ...srcFont };
    newCell.alignment = { horizontal: 'center', vertical: 'middle', wrapText: true };
  });

  // ===== 데이터 행 작성 =====
  let newRowNum = 3;
  let no = 1;

  for (const name of targetNames) {
    if (!foundRows[name]) {
      console.warn(`[경고] ${name} 을 찾지 못했습니다.`);
      continue;
    }
    for (const srcRow of foundRows[name]) {
      const newRow = newWs.getRow(newRowNum);
      newRow.height = srcRow.height || 36;

      srcRow.eachCell({ includeEmpty: true }, (cell, colNum) => {
        if (colNum > colCount) return;
        const newCell = newRow.getCell(colNum);

        // NO 컬럼은 재번호
        if (colNum === 1) {
          newCell.value = no;
        } else {
          // 출퇴근 시간 줄바꿈 처리
          const rawText = getCellText(cell);
          const text = normalizeLineBreak(rawText);
          newCell.value = text || null;
        }

        // 서식 적용
        newCell.border = thinBorder;
        newCell.font = { ...baseFontWhite, ...(cell.font || {}) };
        newCell.alignment = {
          horizontal: 'center',
          vertical: 'middle',
          wrapText: true   // ← 줄바꿈 핵심
        };
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
      no++;
    }
  }

  // 저장
  await newWb.xlsx.writeFile(outFile);
  console.log(`✅ 저장 완료: ${outFile}`);
  console.log(`   총 ${no - 1}명 포함 (헤더 2행 + 데이터 ${newRowNum - 3}행)`);
}

run().catch(err => {
  console.error('오류 발생:', err);
  process.exit(1);
});
