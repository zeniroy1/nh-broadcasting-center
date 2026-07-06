/**
 * ============================================================
 * 주간 식단표 자동 처리 스크립트
 * ============================================================
 *
 * 사용법:
 *   node process-menu.mjs --setup                         (폴더 생성 + 이미지 이동)
 *   node process-menu.mjs --calendar "식단표03.02_03.06"   (캘린더 등록)
 *   node process-menu.mjs --delete "식단표03.02_03.06"     (캘린더 삭제)
 *
 * --setup 플로우:
 *   1. 식단표 폴더에서 본관.jpg, 신관.jpg 감지
 *   2. 날짜 범위 입력 (예: 03.09_03.13)
 *   3. 식단표MM.DD_MM.DD 폴더 생성
 *   4. 이미지 파일 이동
 *
 * --calendar 플로우:
 *   menu-to-calendar.mjs를 호출하여 캘린더 등록
 * ============================================================
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createInterface } from 'readline';
import { execSync } from 'child_process';

// ===== 포터블 경로 설정 (하드코딩 없음) =====
// 스크립트 위치: [루트]/new folder/식단표/process-menu.mjs
// 루트(PROJECT_ROOT) = 스크립트 기준 2단계 상위
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const BASE_DIR = __dirname;                          // new folder/식단표/
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');  // 루트 (credentials.json 위치)

// ===== readline 유틸 =====
function ask(question) {
    const rl = createInterface({ input: process.stdin, output: process.stdout });
    return new Promise(resolve => {
        rl.question(question, answer => {
            rl.close();
            resolve(answer.trim());
        });
    });
}

// ===== 이미지 파일 감지 =====
function detectImages() {
    const files = fs.readdirSync(BASE_DIR);
    const imageExts = ['.jpg', '.jpeg', '.png'];

    const find = (keyword) => files.find(f => {
        const lower = f.toLowerCase();
        return lower.includes(keyword) && imageExts.some(ext => lower.endsWith(ext));
    });

    return {
        bongwan: find('본관'),
        singwan: find('신관'),
        nhtower: find('nh타워') || find('nh타워'),
    };
}

// ===== SETUP: 폴더 생성 + 이미지 이동 =====
async function setup() {
    console.log('\n╔══════════════════════════════════════════╗');
    console.log('║   주간 식단표 - 폴더 생성 및 파일 이동   ║');
    console.log('╚══════════════════════════════════════════╝\n');

    // 이미지 감지
    const images = detectImages();

    if (!images.bongwan && !images.singwan && !images.nhtower) {
        console.log('❌ 식단표 폴더에서 이미지 파일을 찾을 수 없습니다.');
        console.log(`   경로: ${BASE_DIR}`);
        console.log('   "본관", "신관", 또는 "NH타워"가 포함된 이미지 파일(.jpg/.png)을 넣어주세요.');
        process.exit(1);
    }

    console.log('📷 감지된 이미지 파일:');
    if (images.bongwan) console.log(`  ✅ 본관: ${images.bongwan}`);
    if (images.singwan) console.log(`  ✅ 신관: ${images.singwan}`);
    if (images.nhtower) console.log(`  ✅ NH타워: ${images.nhtower}`);
    if (!images.bongwan) console.log('  ⚠️ 본관 이미지 없음');
    if (!images.singwan) console.log('  ⚠️ 신관 이미지 없음');
    if (!images.nhtower) console.log('  ⚠️ NH타워 이미지 없음');
    console.log('');

    // 날짜 범위 입력
    const dateRange = await ask('📅 날짜 범위를 입력하세요 (예: 03.09_03.13): ');

    if (!dateRange.match(/^\d{2}\.\d{2}_\d{2}\.\d{2}$/)) {
        console.log('❌ 형식이 올바르지 않습니다. 예: 03.09_03.13');
        process.exit(1);
    }

    const folderName = `식단표${dateRange}`;
    const folderPath = path.join(BASE_DIR, folderName);

    // 폴더 생성
    if (fs.existsSync(folderPath)) {
        console.log(`⚠️ 폴더가 이미 존재합니다: ${folderName}`);
    } else {
        fs.mkdirSync(folderPath);
        console.log(`📁 폴더 생성: ${folderName}`);
    }

    // 이미지 이동
    let moved = 0;
    for (const [key, filename] of Object.entries(images)) {
        if (filename) {
            const src = path.join(BASE_DIR, filename);
            const dst = path.join(folderPath, filename);
            fs.renameSync(src, dst);
            console.log(`  📦 이동: ${filename} → ${folderName}/`);
            moved++;
        }
    }

    console.log(`\n✅ ${moved}개 파일 이동 완료!`);
    console.log(`\n📌 다음 단계: AI에게 HTML 메뉴표 생성을 요청하세요.`);
    console.log(`   폴더: ${folderName}\n`);

    return folderName;
}

// ===== CALENDAR: 캘린더 등록 =====
function calendarRegister(folderName) {
    console.log('\n📅 캘린더 등록 시작...\n');

    const scriptPath = path.join(BASE_DIR, 'menu-to-calendar.mjs');

    try {
        execSync(`node "${scriptPath}" "${folderName}"`, {
            stdio: 'inherit',
            cwd: BASE_DIR,
        });
    } catch (err) {
        console.error('❌ 캘린더 등록 중 오류 발생');
        process.exit(1);
    }
}

// ===== CALENDAR DELETE: 캘린더 삭제 =====
function calendarDelete(folderName) {
    console.log('\n🗑️ 캘린더 이벤트 삭제 시작...\n');

    const scriptPath = path.join(BASE_DIR, 'menu-to-calendar.mjs');

    try {
        execSync(`node "${scriptPath}" "${folderName}" --delete`, {
            stdio: 'inherit',
            cwd: BASE_DIR,
        });
    } catch (err) {
        console.error('❌ 캘린더 삭제 중 오류 발생');
        process.exit(1);
    }
}

// ===== 최신 폴더 감지 유틸 =====
function getLatestFolder() {
    const dirs = fs.readdirSync(BASE_DIR)
        .filter(f => {
            try {
                const full = path.join(BASE_DIR, f);
                return fs.statSync(full).isDirectory() && /^식단표\d{2}\.\d{2}_\d{2}\.\d{2}$/.test(f);
            } catch { return false; }
        })
        .sort((a, b) => {
            const mA = fs.statSync(path.join(BASE_DIR, a)).mtimeMs;
            const mB = fs.statSync(path.join(BASE_DIR, b)).mtimeMs;
            return mB - mA; // 최신 순
        });
    return dirs.length > 0 ? dirs[0] : null;
}

// ===== 메인 =====
async function main() {
    const args = process.argv.slice(2);

    if (args.length === 0) {
        console.log('사용법:');
        console.log('  node process-menu.mjs --setup                         (폴더 생성 + 이미지 이동)');
        console.log('  node process-menu.mjs --calendar "식단표03.02_03.06"   (캘린더 등록)');
        console.log('  node process-menu.mjs --calendar-latest               (최신 폴더 자동 등록)');
        console.log('  node process-menu.mjs --delete "식단표03.02_03.06"     (캘린더 삭제)');
        console.log('  node process-menu.mjs --delete-latest                 (최신 폴더 자동 삭제)');
        process.exit(0);
    }

    const mode = args[0];

    if (mode === '--setup') {
        await setup();
    } else if (mode === '--calendar') {
        const folder = args[1];
        if (!folder) {
            console.log('❌ 폴더명을 지정하세요. 예: node process-menu.mjs --calendar "식단표03.09_03.13"');
            process.exit(1);
        }
        calendarRegister(folder);
    } else if (mode === '--calendar-latest') {
        const folder = getLatestFolder();
        if (!folder) {
            console.log('❌ 최신 식단표 폴더를 찾을 수 없습니다.');
            process.exit(1);
        }
        console.log(`[감지] 최신 폴더: ${folder}`);
        calendarRegister(folder);
    } else if (mode === '--delete') {
        const folder = args[1];
        if (!folder) {
            console.log('❌ 폴더명을 지정하세요. 예: node process-menu.mjs --delete "식단표03.09_03.13"');
            process.exit(1);
        }
        calendarDelete(folder);
    } else if (mode === '--delete-latest') {
        const folder = getLatestFolder();
        if (!folder) {
            console.log('❌ 최신 식단표 폴더를 찾을 수 없습니다.');
            process.exit(1);
        }
        console.log(`[대상] 최신 폴더: ${folder}`);
        calendarDelete(folder);
    } else {
        console.log(`❌ 알 수 없는 옵션: ${mode}`);
        console.log('   --setup, --calendar, --calendar-latest, --delete, --delete-latest 중 하나를 사용하세요.');
        process.exit(1);
    }
}

main().catch(e => {
    console.error('❌ 오류:', e.message);
    process.exit(1);
});
