const XLSX = require('xlsx');
const path = require('path');
const fs = require('fs');

// 대상자 순서 (이 순서대로 출력)
const targetNames = ['박세영', '김동석', '김준호', '함현식', '김성주', '주경훈', '이동근', '윤태우', '박성준', '주희준'];

const file04 = path.resolve(__dirname, '../2026-04_근태현황(4.27~30)_중앙본부_20260504200348.xlsx');
const file05 = path.resolve(__dirname, '../2026-05_근태현황_중앙본부_20260504200341.xlsx');

// ===== 원본 서식 복사를 위해 raw 바이너리로 읽기 =====
function parseFile(filePath) {
  const wb = XLSX.readFile(filePath, { cellStyles: true, cellDates: true });
  const sheetName = wb.SheetNames[0];
  const ws = wb.Sheets[sheetName];
  const data = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });
  return { wb, ws, data, sheetName };
}

// ===== 파일 파싱 =====
const result04 = parseFile(file04);
const result05 = parseFile(file05);

// ===== 각 파일에서 대상자 행 추출 (순서 유지) =====
function extractTargetRows(data, names) {
  const found = {};
  for (let i = 2; i < data.length; i++) {
    const name = data[i][5];
    if (names.includes(name)) {
      if (!found[name]) found[name] = [];
      found[name].push({ rowIdx: i, rowData: data[i] });
    }
  }
  // 순서대로 정렬
  const ordered = [];
  let no = 1;
  names.forEach(name => {
    if (found[name]) {
      found[name].forEach(entry => {
        const row = [...entry.rowData];
        row[0] = no++; // NO 재번호
        ordered.push(row);
      });
    } else {
      console.warn(`[경고] ${name} 을 찾지 못했습니다.`);
    }
  });
  return ordered;
}

// ===== 새 워크북 생성 함수 =====
function createNewWorkbook(sourceData, targetRows, outFileName) {
  const header1 = sourceData.data[0]; // 첫번째 헤더행
  const header2 = sourceData.data[1]; // 두번째 헤더행

  const newData = [header1, header2, ...targetRows];

  const newWb = XLSX.utils.book_new();
  const newWs = XLSX.utils.aoa_to_sheet(newData);

  // 열 너비 설정 (원본 컬럼 수에 맞게)
  const colCount = header1.length;
  const colWidths = [];
  for (let i = 0; i < colCount; i++) {
    if (i === 0) colWidths.push({ wch: 5 });       // NO
    else if (i === 1) colWidths.push({ wch: 14 }); // 부서
    else if (i === 2) colWidths.push({ wch: 14 }); // 거래처
    else if (i === 3) colWidths.push({ wch: 16 }); // 현장
    else if (i === 4) colWidths.push({ wch: 10 }); // 사번
    else if (i === 5) colWidths.push({ wch: 8 });  // 성명
    else if (i === colCount - 1) colWidths.push({ wch: 8 }); // 담당자
    else colWidths.push({ wch: 18 });              // 날짜 컬럼
  }
  newWs['!cols'] = colWidths;

  // 행 높이 설정 (출퇴근 시간 2줄 표시)
  const rowHeights = newData.map((_, idx) => {
    if (idx < 2) return { hpt: 20 };
    return { hpt: 36 }; // 2줄 높이
  });
  newWs['!rows'] = rowHeights;

  XLSX.utils.book_append_sheet(newWb, newWs, 'Sheet1');

  const outPath = path.resolve(__dirname, '..', outFileName);
  XLSX.writeFile(newWb, outPath);
  console.log(`✅ 저장됨: ${outPath}`);
  console.log(`   총 ${targetRows.length}명 포함`);
  return outPath;
}

// ===== 4월 파일 처리 =====
console.log('\n[4월 파일 처리 중...]');
const rows04 = extractTargetRows(result04.data, targetNames);
console.log('추출된 행:', rows04.length);
rows04.forEach(r => console.log(` - ${r[5]}`));
createNewWorkbook(result04, rows04, '방송팀_근태현황_2026-04(4.27~30).xlsx');

// ===== 5월 파일 처리 =====
console.log('\n[5월 파일 처리 중...]');
const rows05 = extractTargetRows(result05.data, targetNames);
console.log('추출된 행:', rows05.length);
rows05.forEach(r => console.log(` - ${r[5]}`));
createNewWorkbook(result05, rows05, '방송팀_근태현황_2026-05.xlsx');

console.log('\n✅ 완료! 두 파일이 근태관리 폴더에 생성되었습니다.');
