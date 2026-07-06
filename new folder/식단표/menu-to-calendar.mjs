/**
 * ============================================================
 * 주간 점심메뉴 → Google Calendar 자동 등록 스크립트
 * ============================================================
 *
 * 사용법:
 *   node menu-to-calendar.mjs "식단표03.02_03.06"          (등록)
 *   node menu-to-calendar.mjs "식단표03.02_03.06" --delete  (삭제)
 *
 * 사전 준비:
 *   1. 식단표 하위 폴더에 신관/본관 HTML 메뉴 파일 배치
 *   2. credentials.json 및 token.json 이 프로젝트 루트에 존재
 *
 * 기능:
 *   1. HTML 파싱 → 점심 A/B 코너 메뉴 추출
 *   2. 날짜별로 1개 이벤트 (본관+신관 메뉴 통합)
 *   3. 11:00 알림 + 행사/공휴일/빈칸 자동 처리
 * ============================================================
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import http from 'http';
import { URL } from 'url';
import { google } from 'googleapis';
import * as cheerio from 'cheerio';

// ===== 포터블 경로 설정 (하드코딩 없음) =====
// 스크립트 위치: [루트]/new folder/식단표/menu-to-calendar.mjs
// 루트(PROJECT_ROOT) = 스크립트 기준 2단계 상위
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const BASE_DIR = __dirname;                                           // new folder/식단표/
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');             // 루트
const CREDENTIALS_PATH = path.join(PROJECT_ROOT, 'credentials.json');
const TOKEN_PATH = path.join(PROJECT_ROOT, 'token.json');

const SCOPES = ['https://www.googleapis.com/auth/calendar'];

// ===== 1. OAuth 인증 =====
async function authorize() {
    const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf-8'));
    const { client_id, client_secret } = credentials.installed;
    const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, 'http://localhost:3939');

    if (fs.existsSync(TOKEN_PATH)) {
        const token = JSON.parse(fs.readFileSync(TOKEN_PATH, 'utf-8'));
        oAuth2Client.setCredentials(token);

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

    console.log('🔗 아래 URL을 브라우저에서 열어 인증해주세요:\n');
    console.log(authUrl + '\n');

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
        server.listen(3939, () => console.log('⏳ 인증 대기 중...'));
    });

    const { tokens } = await oAuth2Client.getToken(code);
    oAuth2Client.setCredentials(tokens);
    fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens, null, 2));
    console.log('✅ 인증 완료!\n');
    return oAuth2Client;
}

// ===== 2. 캘린더 찾기 =====
async function findCalendarId(auth) {
    const calendar = google.calendar({ version: 'v3', auth });
    const res = await calendar.calendarList.list();
    let cal = res.data.items.find(c => c.summary.includes('함현식'));
    if (!cal) {
        cal = res.data.items.find(c => c.id.includes('hhs11201120'));
    }
    if (!cal) {
        console.log('❌ 캘린더를 찾을 수 없습니다.');
        console.log('사용 가능한 캘린더:');
        res.data.items.forEach(c => console.log(`  - ${c.summary} (${c.id})`));
        process.exit(1);
    }
    console.log(`📅 캘린더: ${cal.summary}\n`);
    return cal.id;
}

// ===== 3. HTML 파싱 =====
function parseMenuHTML(htmlPath, building) {
    const html = fs.readFileSync(htmlPath, 'utf-8');
    const $ = cheerio.load(html);

    // 연도 추출
    const dateRangeText = $('.date-range').text();
    const yearMatch = dateRangeText.match(/(20\d{2})/);
    const year = yearMatch ? yearMatch[1] : new Date().getFullYear().toString();

    // 헤더에서 날짜 추출 (5일치)
    const dates = [];
    $('thead th').each((i, el) => {
        if (i === 0) return;
        const text = $(el).text().trim();
        // 다양한 날짜 형식 지원: 03월 30일, 3/30, 3.30, 3-30
        const match = text.match(/(\d{1,2})\s*[월\/\.\-]\s*(\d{1,2})/);
        if (match) {
            dates.push(`${year}-${match[1].padStart(2, '0')}-${match[2].padStart(2, '0')}`);
        }
    });

    // 코너 행 파싱 (A/B 또는 코너1/2/3)
    let cornerAMenus = [];
    let cornerBMenus = [];
    let cornerCMenus = []; // NH타워 코너3용
    let currentMeal = '';

    $('tbody tr').each((_, row) => {
        const rowText = $(row).text().replace(/\s+/g, '');

        const categoryCell = $(row).find('td.category, td.sub-category, th.category, th.sub-category');
        if (!categoryCell.length) return;

        const catText = categoryCell.text().replace(/\s+/g, '');

        // 식사 구분자 (조식, 중식, 석식) 영구 트래킹
        // ※ rowText(전체 셀 텍스트)는 메뉴 내용("모닝빵샌드위치" 등)을 포함하여 오검출 위험이 있으므로
        //    카테고리 셀(catText)만 사용하여 정확하게 식사 구분을 판별함
        if (catText.match(/(조식|아침|모닝)/)) {
            currentMeal = '조식';
        } else if (catText.match(/(중식|점심|A코너|B코너|코너A|코너B|두레A|두레B)/)) {
            currentMeal = '중식';
        } else if (catText.match(/(석식|저녁|디너)/)) {
            currentMeal = '석식';
        }
        let cornerType = null; // 'A', 'B', 'C'

        // 중식이 아닌 경우 파싱 건너뛰기
        if (currentMeal && currentMeal !== '중식' && currentMeal !== '조식' && currentMeal !== '석식') {
            // 알 수 없는 섹션은 기본적으로 무시 (하지만 조식/석식은 스킵 대상)
        }
        if (currentMeal === '조식' || currentMeal === '석식') return;

        if (building === 'NH타워') {
            if (catText.includes('코너1')) cornerType = 'A';
            else if (catText.includes('코너2')) cornerType = 'B';
            else if (catText.includes('코너3')) cornerType = 'C';
        } else if (building === '신관') {
            if (catText.includes('A') && (catText.includes('코너') || catText.includes('코'))) cornerType = 'A';
            else if (catText.includes('B') && (catText.includes('코너') || catText.includes('코'))) cornerType = 'B';
        } else if (building === '본관') {
            if (catText.includes('두레') && catText.includes('A')) cornerType = 'A';
            else if (catText.includes('두레') && catText.includes('B')) cornerType = 'B';
        }

        if (!cornerType) return;

        // .category, .sub-category를 제외한 모든 td 순회
        const menuCells = $(row).children('td').not('.category').not('.sub-category');

        const menus = [];
        menuCells.each((j, cell) => {
            if (j >= dates.length) return;

            const $cell = $(cell);
            const rawText = $cell.text().trim();

            const isEvent = $cell.hasClass('event-text') || $cell.hasClass('holiday-cell') ||
                rawText.includes('행 사') || rawText.includes('행사') || rawText.includes('< 행 사 >') || rawText.includes('<행사>') || 
                rawText.includes('휴 무') || rawText.includes('휴무') || rawText.includes('휴 점') || rawText.includes('휴점');

            const isEmpty = !rawText || rawText === '\u00a0' || rawText.replace(/\s/g, '') === '';

            let items = [];
            if (!isEvent && !isEmpty) {
                const clone = $cell.clone();
                clone.find('.section-title').remove();
                clone.find('em').remove();

                let cellHtml = clone.html();
                if (cellHtml) {
                    cellHtml = cellHtml.replace(/<br\s*\/?>/gi, '\n');
                    const textOnly = cellHtml.replace(/<[^>]*>/g, '').trim();
                    items = textOnly
                        .split('\n')
                        .map(s => s.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').trim())
                        .filter(Boolean);
                }
            }

            menus.push({ date: dates[j], isEvent, isEmpty, items });
        });

        if (cornerType === 'A') cornerAMenus = menus;
        if (cornerType === 'B') cornerBMenus = menus;
        if (cornerType === 'C') cornerCMenus = menus;
    });

    return { building, cornerAMenus, cornerBMenus, cornerCMenus, dates };
}

// ===== 4. 코너별 설명 텍스트 생성 =====
function buildCornerSection(label, menuA, menuB, menuC) {
    const lines = [];

    function addCorner(cornerLabel, menu, refMenu, refLabel) {
        const hasMenu = menu && !menu.isEvent && !menu.isEmpty && menu.items.length > 0;
        const isEvent = menu && menu.isEvent;
        const isEmpty = !menu || menu.isEmpty;
        const refHasMenu = refMenu && !refMenu.isEvent && !refMenu.isEmpty && refMenu.items.length > 0;

        if (lines.length > 0 && (hasMenu || isEvent || (isEmpty && refHasMenu))) {
            lines.push('');
        }

        if (hasMenu) {
            lines.push(`【 ${cornerLabel} 】`);
            lines.push(menu.items.join('\n'));
        } else if (isEvent) {
            lines.push(`【 ${cornerLabel} 】 행사`);
        } else if (isEmpty && refHasMenu) {
            lines.push(`【 ${cornerLabel} 】 ${refLabel}와 동일 메뉴`);
        }
    }

    if (label === 'NH타워') {
        addCorner(`${label} 코너1`, menuA, null, '');
        addCorner(`${label} 코너2`, menuB, null, '');
        if (menuC) addCorner(`${label} 코너3`, menuC, null, '');
    } else {
        addCorner(`${label}A`, menuA, null, '');
        addCorner(`${label}B`, menuB, menuA, `${label}A`);
    }

    return lines.join('\n');
}

// ===== 5. 날짜별 통합 이벤트 생성 =====
function buildDailyEvents(singwanParsed, bongwanParsed, nhtowerParsed) {
    // 모든 유효 날짜 수집 (보통 월~금 5일)
    const allDates = new Set();
    if (singwanParsed) singwanParsed.dates.forEach(d => allDates.add(d));
    if (bongwanParsed) bongwanParsed.dates.forEach(d => allDates.add(d));
    if (nhtowerParsed) nhtowerParsed.dates.forEach(d => allDates.add(d));

    const sortedDates = [...allDates].sort();
    const events = [];

    for (const date of sortedDates) {
        const sections = [];

        // 본관 메뉴
        if (bongwanParsed) {
            const menuA = bongwanParsed.cornerAMenus.find(m => m.date === date);
            const menuB = bongwanParsed.cornerBMenus.find(m => m.date === date);
            const section = buildCornerSection('본관', menuA, menuB);
            if (section.trim()) sections.push(section);
        }

        // 신관 메뉴
        if (singwanParsed) {
            const menuA = singwanParsed.cornerAMenus.find(m => m.date === date);
            const menuB = singwanParsed.cornerBMenus.find(m => m.date === date);
            const section = buildCornerSection('신관', menuA, menuB);
            if (section.trim()) sections.push(section);
        }

        // NH타워 메뉴
        if (nhtowerParsed) {
            const menu1 = nhtowerParsed.cornerAMenus.find(m => m.date === date);
            const menu2 = nhtowerParsed.cornerBMenus.find(m => m.date === date);
            const menu3 = nhtowerParsed.cornerCMenus.find(m => m.date === date);
            const section = buildCornerSection('NH타워', menu1, menu2, menu3);
            if (section.trim()) sections.push(section);
        }

        if (sections.length > 0) {
            const description = sections.join('\n\n━━━━━━━━━━━━━━━━━━━━\n\n');
            // console.log(`  ✅ [DEBUG] ${date} 이벤트 생성됨 (${sections.length}개 섹션)`);
            events.push({
                date,
                title: `오늘의 점심메뉴`,
                description,
            });
        }
    }

    return events;
}

// ===== 6. Google Calendar 이벤트 생성 =====
async function createCalendarEvent(auth, calendarId, event) {
    const calendar = google.calendar({ version: 'v3', auth });

    const calendarEvent = {
        summary: event.title,
        description: event.description,
        start: {
            dateTime: `${event.date}T11:00:00`,
            timeZone: 'Asia/Seoul',
        },
        end: {
            dateTime: `${event.date}T11:05:00`,
            timeZone: 'Asia/Seoul',
        },
        reminders: {
            useDefault: false,
            overrides: [
                { method: 'popup', minutes: 0 },
            ],
        },
    };

    const response = await calendar.events.insert({
        calendarId,
        resource: calendarEvent,
    });

    return response.data;
}

// ===== 7. 기존 이벤트 삭제 =====
async function deleteMenuEvents(auth, calendarId, dates) {
    const calendar = google.calendar({ version: 'v3', auth });

    const minDate = dates[0];
    const maxDate = dates[dates.length - 1];

    console.log(`🗑️  ${minDate} ~ ${maxDate} 기간 점심메뉴 이벤트 삭제 중...`);

    const res = await calendar.events.list({
        calendarId,
        timeMin: `${minDate}T00:00:00+09:00`,
        timeMax: `${maxDate}T23:59:59+09:00`,
        q: '점심',
        singleEvents: true,
    });

    const menuEvents = res.data.items.filter(e =>
        e.summary && (e.summary.includes('점심메뉴') || e.summary.includes('🍽️'))
    );

    if (menuEvents.length === 0) {
        console.log('  삭제할 이벤트가 없습니다.\n');
        return 0;
    }

    let deleted = 0;
    for (const evt of menuEvents) {
        try {
            await calendar.events.delete({ calendarId, eventId: evt.id });
            console.log(`  🗑️ 삭제: ${evt.summary} (${evt.start.dateTime?.slice(0, 10)})`);
            deleted++;
        } catch (err) {
            console.error(`  ❌ 삭제 실패: ${evt.summary} - ${err.message}`);
        }
    }

    console.log(`  ✅ ${deleted}건 삭제 완료\n`);
    return deleted;
}

// ===== 메인 실행 =====
async function main() {
    const folderArg = process.argv[2];
    const isDeleteMode = process.argv.includes('--delete');

    if (!folderArg) {
        console.log('❌ 사용법:');
        console.log('   node menu-to-calendar.mjs "식단표03.02_03.06"          (등록)');
        console.log('   node menu-to-calendar.mjs "식단표03.02_03.06" --delete  (삭제)');
        process.exit(1);
    }

    const menuDir = path.join(BASE_DIR, folderArg);
    if (!fs.existsSync(menuDir)) {
        console.log(`❌ 폴더를 찾을 수 없습니다: ${menuDir}`);
        process.exit(1);
    }

    console.log('');
    console.log('╔══════════════════════════════════════════╗');
    console.log('║   주간 점심메뉴 → Google Calendar 등록   ║');
    console.log('╚══════════════════════════════════════════╝');
    console.log('');

    // HTML 파일 찾기
    const files = fs.readdirSync(menuDir);
    const singwanFile = files.find(f => f.includes('신관') && f.endsWith('.html'));
    const bongwanFile = files.find(f => f.includes('본관') && f.endsWith('.html'));
    const nhtowerFile = files.find(f => f.includes('NH타워') && f.endsWith('.html'));

    if (!singwanFile && !bongwanFile && !nhtowerFile) {
        console.log('❌ HTML 메뉴 파일을 찾을 수 없습니다.');
        process.exit(1);
    }

    // 메뉴 파싱
    let singwanParsed = null;
    let bongwanParsed = null;
    let nhtowerParsed = null;

    if (singwanFile) {
        console.log(`📄 신관 파싱: ${singwanFile}`);
        singwanParsed = parseMenuHTML(path.join(menuDir, singwanFile), '신관');
        console.log(`  📅 날짜 추출 완료: ${singwanParsed.dates.join(', ')}`);
    }

    if (bongwanFile) {
        console.log(`📄 본관 파싱: ${bongwanFile}`);
        bongwanParsed = parseMenuHTML(path.join(menuDir, bongwanFile), '본관');
        console.log(`  📅 날짜 추출 완료: ${bongwanParsed.dates.join(', ')}`);
    }

    if (nhtowerFile) {
        console.log(`📄 NH타워 파싱: ${nhtowerFile}`);
        nhtowerParsed = parseMenuHTML(path.join(menuDir, nhtowerFile), 'NH타워');
        console.log(`  📅 날짜 추출 완료: ${nhtowerParsed.dates.join(', ')}`);
    }

    console.log('');

    // 인증
    const auth = await authorize();
    const calendarId = await findCalendarId(auth);

    // 삭제 모드
    if (isDeleteMode) {
        const allDates = [
            ...(singwanParsed?.dates || []),
            ...(bongwanParsed?.dates || []),
            ...(nhtowerParsed?.dates || []),
        ];
        const uniqueDates = [...new Set(allDates)].sort();
        await deleteMenuEvents(auth, calendarId, uniqueDates);
        return;
    }

    // 날짜별 통합 이벤트 생성
    const dailyEvents = buildDailyEvents(singwanParsed, bongwanParsed, nhtowerParsed);

    // 미리보기
    console.log('📋 등록할 이벤트 (날짜별 1개):');
    console.log('─'.repeat(60));
    dailyEvents.forEach((evt, i) => {
        console.log(`\n  ${i + 1}. ${evt.date} | ${evt.title}`);
        console.log('  ' + evt.description.split('\n').map(l => '  ' + l).join('\n'));
    });
    console.log('\n' + '─'.repeat(60));
    console.log('');

    // 기존 이벤트 삭제 후 등록
    const allDates = dailyEvents.map(e => e.date);
    await deleteMenuEvents(auth, calendarId, allDates);

    // 이벤트 등록
    let success = 0;
    let fail = 0;

    for (let i = 0; i < dailyEvents.length; i++) {
        const evt = dailyEvents[i];
        console.log(`[${i + 1}/${dailyEvents.length}] ${evt.date} 등록중...`);
        try {
            await createCalendarEvent(auth, calendarId, evt);
            console.log(`  ✅ 완료!`);
            success++;
        } catch (err) {
            console.error(`  ❌ 오류: ${err.message}`);
            fail++;
        }
    }

    console.log('');
    console.log('╔══════════════════════════════════════════╗');
    console.log(`║   결과: 성공 ${success}건 / 실패 ${fail}건                ║`);
    console.log('╚══════════════════════════════════════════╝');
}

main().catch(e => {
    console.error('❌ 오류:', e.message);
    process.exit(1);
});
