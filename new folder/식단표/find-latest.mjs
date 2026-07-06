// 식단표 폴더 자동 감지 (배치파일에서 node find-latest.mjs 로 호출)
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const dirs = fs.readdirSync(__dirname)
    .filter(f => {
        try {
            const full = path.join(__dirname, f);
            return fs.statSync(full).isDirectory() && /^식단표\d{2}\.\d{2}_\d{2}\.\d{2}$/.test(f);
        } catch { return false; }
    })
    .sort((a, b) => {
        const mA = fs.statSync(path.join(__dirname, a)).mtimeMs;
        const mB = fs.statSync(path.join(__dirname, b)).mtimeMs;
        return mB - mA; // 최신 순
    });

if (dirs.length > 0) {
    process.stdout.write(dirs[0]);
} else {
    process.exit(1);
}
