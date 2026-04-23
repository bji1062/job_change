#!/usr/bin/env bash
# 동작: styles.css/app.js 해시 산출 → index.html 해시 주입 → gzip 사전 압축 → PLACEHOLDER 잔존 가드
# 실행: 프로젝트 루트에서 `bash server/deploy/release-frontend.sh`

set -euo pipefail

# 프로젝트 루트로 이동 (스크립트 위치 기준 상위 2단계)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${ROOT_DIR}"

if [[ ! -f styles.css || ! -f app.js || ! -f index.html ]]; then
    echo "오류: styles.css, app.js, index.html 이 프로젝트 루트에 모두 있어야 합니다." >&2
    exit 2
fi

CSS_HASH="$(sha1sum styles.css | cut -c1-8)"
JS_HASH="$(sha1sum app.js | cut -c1-8)"

# 상대경로 기준 치환. 정규식은 PLACEHOLDER(대문자) + 기존 해시(대소문자 영숫자) 모두 매칭.
sed -i.bak -E "s|styles\\.css\\?v=[A-Za-z0-9]+|styles.css?v=${CSS_HASH}|g" index.html
sed -i.bak -E "s|app\\.js\\?v=[A-Za-z0-9]+|app.js?v=${JS_HASH}|g" index.html
rm -f index.html.bak

# gzip pre-compress for gzip_static
gzip -9kf styles.css app.js

# 주입 실패 가드 — PLACEHOLDER 잔존 시 즉시 실패
if grep -q '?v=PLACEHOLDER' index.html; then
    echo "해시 주입 실패: index.html 에 'v=PLACEHOLDER' 잔존" >&2
    exit 1
fi

echo "CSS=${CSS_HASH} JS=${JS_HASH}"
echo "Generated: styles.css.gz ($(wc -c < styles.css.gz) bytes), app.js.gz ($(wc -c < app.js.gz) bytes)"
