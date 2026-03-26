/**
 * ============================================================
 * 로비전광판 월별 일정 → Google Calendar 자동 등록 스크립트
 * ============================================================
 * 
 * 사용법:
 *   node upload.mjs <월>
 *   예시: node upload.mjs 4     (4월 일정 등록)
 *         node upload.mjs 12    (12월 일정 등록)
 * 
 * 사전 준비:
 *   1. new folder/로비전광판/N월/ 폴더에 아래 파일 넣기:
 *      - PDF 일정표 (파일명에 "일정" 포함)
 *      - JPG 송출자료 (파일명: 0101 시도 농협명.jpg 형식)
 *   2. credentials.json 및 token.json 이 프로젝트 루트에 존재
 * 
 * 기능:
 *   1. PDF 자동 파싱 → 일정 데이터 추출
 *   2. 루트 폴더의 JPG 자동 분류 → 해당 월 폴더로 이동
 *   3. JPG 파일 → Google Drive 업로드
 *   4. Google Calendar "농협" 캘린더에 이벤트 생성 또는 업데이트(첨부 포함)
 * ============================================================
 */

import fs from 'fs';
import path from 'path';
import http from 'http';
import { URL } from 'url';
import { google } from 'googleapis';
import { getDocument } from 'pdfjs-dist/legacy/build/pdf.mjs';

// ===== 경로 설정 =====
const PROJECT_ROOT = 'c:\\Users\\hamcoding\\Desktop\\codding';
const BASE_DIR = path.join(PROJECT_ROOT, 'new folder', '로비전광판');
const CREDENTIALS_PATH = path.join(PROJECT_ROOT, 'credentials.json');
const TOKEN_PATH = path.join(PROJECT_ROOT, 'token.json');

const NONGHYUP_CAL_ID = '94b0588151436866e8f740b164a2f47b9e2fdca47df5e52dec5c4f9968046e2f@group.calendar.google.com';

const SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive.file',
];

// ===== 1. PDF 파싱 =====
async function parsePDF(pdfPath, month) {
    console.log(`📄 PDF 파싱 중: ${path.basename(pdfPath)}`);

    const data = new Uint8Array(fs.readFileSync(pdfPath));
    const doc = await getDocument({ data }).promise;

    let fullText = '';
    for (let i = 1; i <= doc.numPages; i++) {
        const page = await doc.getPage(i);
        const textContent = await page.getTextContent();
        fullText += textContent.items.map(item => item.str).join(' ');
    }

    // 정규식으로 각 이벤트 행 추출
    // 패턴: MM 월 DD 일 ( 요일 ) HH:MM 시도 시/군 농협명 HH:MM HH:MM
    const pattern = /(\d{2})\s*월\s*(\d{2})\s*일\s*\(\s*([월화수목금토일])\s*\)\s*(\d{1,2}:\d{2})\s+(\S+)\s+(\S+)\s+(.+?)\s+(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})/g;

    const events = [];
    let match;

    while ((match = pattern.exec(fullText)) !== null) {
        const [, mm, dd, day, visitTime, sido, sigun, rawName, startTime, endTime] = match;

        // 농협명에서 불필요한 공백 정리
        const name = rawName.trim().replace(/\s+/g, '');

        // 현재 연도 기준
        const year = new Date().getFullYear();
        const date = `${year}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`;

        events.push({
            date,
            day,
            visitTime,
            region: `${sido} ${sigun}`,
            name,
            start: startTime,
            end: endTime,
            jpg: null, // 나중에 매칭
        });
    }

    console.log(`  ✅ ${events.length}건의 일정 추출됨\n`);
    return events;
}

// ===== 1-2. JPG 파일 자동 분류 =====
function organizeFiles() {
    console.log('📂 루트 폴더의 JPG 파일 분류 중...');
    const rootFiles = fs.readdirSync(BASE_DIR);
    const jpgFiles = rootFiles.filter(f => f.toLowerCase().endsWith('.jpg'));

    let movedCount = 0;
    for (const file of jpgFiles) {
        // 파일명에서 월 추출 (예: 0331 -> 3월)
        const monthMatch = file.match(/^(\d{2})/);
        if (monthMatch) {
            const month = parseInt(monthMatch[1]);
            if (month >= 1 && month <= 12) {
                const targetDir = path.join(BASE_DIR, `${month}월`);
                if (!fs.existsSync(targetDir)) {
                    fs.mkdirSync(targetDir, { recursive: true });
                }
                const oldPath = path.join(BASE_DIR, file);
                const newPath = path.join(targetDir, file);
                
                // 파일 이동 (이미 있으면 덮어씀)
                fs.renameSync(oldPath, newPath);
                console.log(`  ➡️  ${file} → ${month}월 폴더로 이동됨`);
                movedCount++;
            }
        }
    }
    if (movedCount > 0) {
        console.log(`  ✅ 총 ${movedCount}개의 파일 이동 완료\n`);
    } else {
        console.log('  ✨ 이동할 파일이 없습니다.\n');
    }
}

// ===== 2. JPG 파일 매칭 =====
function matchJPGFiles(events, monthDir) {
    const jpgFiles = fs.readdirSync(monthDir).filter(f => f.toLowerCase().endsWith('.jpg'));

    console.log(`🖼️  JPG 파일 매칭 중... (${jpgFiles.length}개 발견)`);

    for (const event of events) {
        const datePrefix = event.date.slice(5).replace('-', ''); // MM/DD → MMDD

        // 날짜 + 농협명으로 매칭
        const matched = jpgFiles.find(f => {
            const normalized = f.replace(/\s+/g, '');
            return f.startsWith(datePrefix) && normalized.includes(event.name.replace(/\s+/g, ''));
        });

        if (matched) {
            event.jpg = matched;
            console.log(`  ✅ ${event.date} ${event.name} → ${matched}`);
        } else {
            // 날짜만으로 매칭 시도
            const dateMatched = jpgFiles.find(f => f.startsWith(datePrefix));
            if (dateMatched && events.filter(e => e.date === event.date).length === 1) {
                event.jpg = dateMatched;
                console.log(`  ✅ ${event.date} ${event.name} → ${dateMatched} (날짜 매칭)`);
            } else {
                console.log(`  ⚠️  ${event.date} ${event.name} → JPG 파일 없음`);
            }
        }
    }
    console.log('');
    return events;
}

// ===== 3. OAuth 인증 =====
async function authorize() {
    const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf-8'));
    const { client_id, client_secret } = credentials.installed;
    const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, 'http://localhost:3939');

    if (fs.existsSync(TOKEN_PATH)) {
        const token = JSON.parse(fs.readFileSync(TOKEN_PATH, 'utf-8'));
        oAuth2Client.setCredentials(token);

        // 토큰 만료 확인 및 갱신
        try {
            await oAuth2Client.getAccessToken();
            console.log('🔑 기존 토큰으로 인증 완료\n');
            return oAuth2Client;
        } catch (e) {
            console.log('🔄 토큰 만료, 재인증 필요...\n');
        }
    }

    const authUrl = oAuth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: SCOPES,
    });

    console.log('🔗 아래 URL을 브라우저에서 열어 인증해주세요:');
    console.log('');
    console.log(authUrl);
    console.log('');

    const code = await new Promise((resolve) => {
        const server = http.createServer((req, res) => {
            const url = new URL(req.url, 'http://localhost:3939');
            const authCode = url.searchParams.get('code');
            if (authCode) {
                res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
                res.end('<h1>✅ 인증 완료! 이 창을 닫으셔도 됩니다.</h1>');
                server.close();
                resolve(authCode);
            }
        });
        server.listen(3939, () => {
            console.log('⏳ 인증 대기 중... (브라우저에서 인증을 완료해주세요)');
        });
    });

    const { tokens } = await oAuth2Client.getToken(code);
    oAuth2Client.setCredentials(tokens);
    fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens, null, 2));
    console.log('✅ 인증 완료! 토큰 저장됨\n');

    return oAuth2Client;
}

// ===== 4. Google Drive 업로드 =====
async function uploadToDrive(auth, filePath, fileName) {
    const drive = google.drive({ version: 'v3', auth });

    const response = await drive.files.create({
        resource: { name: fileName },
        media: { mimeType: 'image/jpeg', body: fs.createReadStream(filePath) },
        fields: 'id, webViewLink',
    });

    await drive.permissions.create({
        fileId: response.data.id,
        resource: { role: 'reader', type: 'anyone' },
    });

    return response.data;
}

// ===== 5. 캘린더 이벤트 생성 =====
async function createEvent(auth, event, driveFile) {
    const calendar = google.calendar({ version: 'v3', auth });

    // 중복 체크
    const searchStart = new Date(`${event.date}T00:00:00+09:00`);
    const searchEnd = new Date(`${event.date}T23:59:59+09:00`);
    const res = await calendar.events.list({
        calendarId: NONGHYUP_CAL_ID,
        timeMin: searchStart.toISOString(),
        timeMax: searchEnd.toISOString(),
        q: event.name,
        singleEvents: true,
    });

    if (res.data.items && res.data.items.length > 0) {
        const existingEvent = res.data.items[0];
        console.log(`  🔄 기존 일정을 찾았습니다 (ID: ${existingEvent.id}), 업데이트를 시도합니다...`);
        
        const description = [
            `[로비전광판 송출]`,
            ``,
            `시간: ${event.visitTime}`,
            ``,
            `시도: ${event.region}`,
            `농협명: ${event.name}`,
            ``,
            event.jpg ? `송출자료: ${event.jpg}` : '',
        ].filter(Boolean).join('\n');

        const calendarEvent = {
            summary: '로비전광판 송출',
            location: '농업박물관 로비',
            description,
            start: { dateTime: `${event.date}T${event.start}:00`, timeZone: 'Asia/Seoul' },
            end: { dateTime: `${event.date}T${event.end}:00`, timeZone: 'Asia/Seoul' },
            attachments: driveFile ? [{
                fileUrl: `https://drive.google.com/file/d/${driveFile.id}/view`,
                title: event.jpg,
                mimeType: 'image/jpeg',
            }] : (existingEvent.attachments || []),
        };

        const response = await calendar.events.patch({
            calendarId: NONGHYUP_CAL_ID,
            eventId: existingEvent.id,
            resource: calendarEvent,
            supportsAttachments: true,
        });

        return response.data;
    }

    const description = [
        `[로비전광판 송출]`,
        ``,
        `시간: ${event.visitTime}`,
        ``,
        `시도: ${event.region}`,
        `농협명: ${event.name}`,
        ``,
        event.jpg ? `송출자료: ${event.jpg}` : '',
    ].filter(Boolean).join('\n');

    const calendarEvent = {
        summary: '로비전광판 송출',
        location: '농업박물관 로비',
        description,
        start: { dateTime: `${event.date}T${event.start}:00`, timeZone: 'Asia/Seoul' },
        end: { dateTime: `${event.date}T${event.end}:00`, timeZone: 'Asia/Seoul' },
        attachments: driveFile ? [{
            fileUrl: `https://drive.google.com/file/d/${driveFile.id}/view`,
            title: event.jpg,
            mimeType: 'image/jpeg',
        }] : [],
    };

    const response = await calendar.events.insert({
        calendarId: NONGHYUP_CAL_ID,
        resource: calendarEvent,
        supportsAttachments: true,
    });

    return response.data;
}

// ===== 메인 실행 =====
async function main() {
    // 인자에서 월 가져오기
    const monthArg = process.argv[2];
    if (!monthArg) {
        console.log('❌ 사용법: node upload.mjs <월>');
        console.log('   예시: node upload.mjs 4');
        process.exit(1);
    }

    const month = parseInt(monthArg);
    if (month < 1 || month > 12) {
        console.log('❌ 월은 1~12 사이의 숫자로 입력해주세요.');
        process.exit(1);
    }

    const monthDir = path.join(BASE_DIR, `${month}월`);

    if (!fs.existsSync(monthDir)) {
        console.log(`❌ 폴더를 찾을 수 없습니다: ${monthDir}`);
        process.exit(1);
    }

    console.log('');
    console.log('╔══════════════════════════════════════════╗');
    console.log(`║   로비전광판 ${month}월 일정 → Google Calendar   ║`);
    console.log('╚══════════════════════════════════════════╝');
    console.log('');

    // 1. PDF 찾기 및 파싱
    const files = fs.readdirSync(monthDir);
    const pdfFile = files.find(f => f.toLowerCase().endsWith('.pdf') && f.includes('일정'));

    if (!pdfFile) {
        console.log('❌ PDF 일정표를 찾을 수 없습니다. (파일명에 "일정"이 포함된 PDF 필요)');
        process.exit(1);
    }

    let events = await parsePDF(path.join(monthDir, pdfFile), month);

    if (events.length === 0) {
        console.log('❌ PDF에서 일정을 추출할 수 없습니다.');
        process.exit(1);
    }

    // 2. JPG 매칭
    events = matchJPGFiles(events, monthDir);

    // 3. 추출된 일정 미리보기
    console.log('📋 등록할 일정 미리보기:');
    console.log('─'.repeat(80));
    events.forEach((evt, i) => {
        console.log(`  ${i + 1}. ${evt.date}(${evt.day}) ${evt.start}~${evt.end} | 시간: ${evt.visitTime} | ${evt.region} ${evt.name} | ${evt.jpg || '(JPG 없음)'}`);
    });
    console.log('─'.repeat(80));
    console.log('');

    // 3-2. 파일 자동 분류 실행
    organizeFiles();

    // 4. 인증
    const auth = await authorize();

    // 5. 이벤트 등록
    let successCount = 0;
    let errorCount = 0;

    for (let i = 0; i < events.length; i++) {
        const event = events[i];
        console.log(`[${i + 1}/${events.length}] ${event.date} ${event.name} 처리중...`);

        try {
            // JPG 업로드
            let driveFile = null;
            if (event.jpg) {
                const jpgPath = path.join(monthDir, event.jpg);
                if (fs.existsSync(jpgPath)) {
                    driveFile = await uploadToDrive(auth, jpgPath, event.jpg);
                    console.log(`  📤 Drive 업로드 완료 (ID: ${driveFile.id})`);
                }
            }

            // 캘린더 이벤트 생성 (직접 농협 캘린더에)
            await createEvent(auth, event, driveFile);
            console.log(`  📅 농협 캘린더에 이벤트 생성 완료`);

            successCount++;
            console.log(`  ✅ 완료!`);
        } catch (error) {
            if (error.message === 'DUPLICATE_EVENT') {
                console.log(`  👉 이미 등록된 일정입니다 (건너뜀)`);
            } else {
                errorCount++;
                console.error(`  ❌ 오류: ${error.message}`);
            }
        }
        console.log('');
    }

    // 6. 결과 요약
    console.log('╔══════════════════════════════════════════╗');
    console.log(`║   결과: 성공 ${successCount}건 / 실패 ${errorCount}건${' '.repeat(20 - String(successCount).length - String(errorCount).length)}║`);
    console.log('╚══════════════════════════════════════════╝');
}

main().catch(e => {
    console.error('❌ 오류 발생:', e.message);
    process.exit(1);
});
