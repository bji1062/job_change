#!/usr/bin/env node
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  회사 복지 스크래퍼 — Claude API + Web Search
//  Usage: ANTHROPIC_API_KEY=sk-... node scrape-benefits.js "삼성전자"
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const Anthropic = require('@anthropic-ai/sdk');

const SYSTEM_PROMPT = `당신은 한국 기업의 복지 정보를 조사하는 전문가입니다.
사용자가 회사명을 입력하면, 웹 검색을 통해 해당 회사의 복지 정보를 수집하고
아래 JavaScript 객체 형식으로 정리해주세요.

## 출력 형식

반드시 아래 JSON 구조를 따라야 합니다. 코드블록(\`\`\`json ... \`\`\`) 안에 넣어주세요:

\`\`\`json
{
  "id": "영문 소문자 약어 (예: samsung, kakao, naver)",
  "name": "공식 회사명 (예: 삼성전자)",
  "aliases": ["검색용 별칭 배열 — 한글, 영문, 약어 등"],
  "type": "large | mid | startup | foreign | public | freelance 중 하나",
  "industry": "업종 (예: 전자/반도체, IT/플랫폼)",
  "logo": "1~2글자 약어 (예: 삼, K, N)",
  "benefits": [
    {
      "key": "영문 소문자 고유키 (예: meal, transport, housing)",
      "name": "복지 항목명 (한국어)",
      "val": "연간 환산 금액 (만원 단위, 정수). 금전 가치 산정 어려우면 0",
      "cat": "money | health | housing | edu | family | life | leave 중 하나",
      "badge": "auto (검증된 정보) 또는 est (추정치)",
      "note": "선택사항 — 부연 설명",
      "qual": "true면 정성적 복지 (금전 가치 없음)",
      "qualText": "qual이 true일 때 설명 텍스트"
    }
  ],
  "workStyle": {
    "remote": true/false,
    "flex": true/false,
    "unlimitedPTO": true/false,
    "refreshLeave": "리프레시 휴가 설명 또는 빈 문자열",
    "overtime": "야근 문화 한 줄 설명"
  }
}
\`\`\`

## 카테고리 (cat) 기준
- money: 식대, 교통비, 복지포인트, 성과급, 인센티브 등 직접 금전 혜택
- health: 건강검진, 의료비, 피트니스, 심리상담 등
- housing: 주택자금, 사내대출, 기숙사, 주거지원 등
- edu: 교육비, 자기개발비, 도서구입, 세미나, 자격증 등
- family: 자녀학자금, 출산지원, 육아휴직, 어린이집 등
- life: 사내할인, 동호회, 여행, 문화생활 등
- leave: 유연근무, 자율휴가, 리프레시, 안식휴가 등

## val (연간 만원) 산정 가이드
- 식대: 일 금액 × 연간 근무일수(약 240일)로 환산
- 월 정액 지원: × 12
- 1회성 지원: 그대로 사용
- 금액 불명확: 유사 기업 기준 추정 후 badge를 "est"로 설정
- 정성적 복지(유연근무, 자율휴가 등): val=0, qual=true

## type 판별 기준
- large: 재계 순위 상위, 대기업 집단 소속, 직원 수 1000명 이상
- mid: 중견기업, 직원 수 300~1000명
- startup: 스타트업, 벤처기업, 설립 10년 이내
- foreign: 외국계 기업 한국 법인
- public: 공기업, 공공기관
- freelance: 프리랜서

## 주의사항
- 최신 정보를 우선하세요 (2024~2025년 기준)
- 잡플래닛, 블라인드, 원티드, 회사 공식 채용페이지 등을 참고하세요
- 확인된 정보는 badge:"auto", 추정은 badge:"est"로 구분하세요
- benefits 배열에 최소 5개 이상의 항목을 포함하세요
- 검색 결과가 부족하면 동종 업계 유사 규모 기업 기준으로 추정하되, 추정임을 명시하세요`;

const FEW_SHOT_EXAMPLE = `
## 참고 예시 (CJ그룹)

\`\`\`json
{
  "id": "cj",
  "name": "CJ그룹",
  "aliases": ["CJ", "cj", "씨제이", "CJ제일제당", "CJ올리브영", "CJ ENM"],
  "type": "large",
  "industry": "식품/유통/엔터",
  "logo": "CJ",
  "benefits": [
    {"key":"meal","name":"구내식당 (아침·점심·저녁 100%)","val":432,"cat":"money","badge":"auto","note":"일 18,000원 × 240일"},
    {"key":"cafe_point","name":"카페테리아 포인트","val":200,"cat":"money","badge":"auto"},
    {"key":"health","name":"건강검진 (본인+가족)","val":100,"cat":"health","badge":"auto"},
    {"key":"housing","name":"주택대부 이자절감","val":200,"cat":"housing","badge":"est"},
    {"key":"child_edu","name":"자녀 학자금","val":300,"cat":"family","badge":"auto","note":"초·중·고·대학"},
    {"key":"parenting","name":"임신·출산·육아 지원","val":0,"cat":"family","badge":"auto","qual":true,"qualText":"키즈빌 운영, 배우자 출산휴가, 최대 2년 육아휴직"},
    {"key":"creative_leave","name":"창의휴가 (근속 시 2주 유급)","val":0,"cat":"leave","badge":"auto","qual":true,"qualText":"3·5·7·10년 근속 시 2주간 유급 휴가"}
  ],
  "workStyle": {
    "remote": false,
    "flex": false,
    "unlimitedPTO": false,
    "refreshLeave": "3·5·7·10년 근속 시 2주 유급",
    "overtime": "일반적 대기업 수준"
  }
}
\`\`\``;

async function scrape(companyName) {
  const client = new Anthropic();

  console.log(`\n🔍 "${companyName}" 복지 정보 검색 중...\n`);

  const response = await client.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 4096,
    system: SYSTEM_PROMPT + '\n\n' + FEW_SHOT_EXAMPLE,
    tools: [{ type: 'web_search_20250305', name: 'web_search', max_uses: 10 }],
    messages: [
      {
        role: 'user',
        content: `"${companyName}"의 복지 정보를 웹 검색으로 조사하여 JSON 형식으로 정리해주세요.

검색 키워드 예시:
- "${companyName} 복지"
- "${companyName} 채용 복리후생"
- "${companyName} 직원 혜택"
- "${companyName} 잡플래닛 복지"

최대한 많은 복지 항목을 찾아주세요.`
      }
    ]
  });

  // Extract text content from response
  let fullText = '';
  for (const block of response.content) {
    if (block.type === 'text') {
      fullText += block.text;
    }
  }

  // Parse JSON from response
  const jsonMatch = fullText.match(/```json\s*([\s\S]*?)```/);
  if (!jsonMatch) {
    console.error('❌ JSON 파싱 실패. 원본 응답:\n');
    console.log(fullText);
    process.exit(1);
  }

  let data;
  try {
    data = JSON.parse(jsonMatch[1]);
  } catch (e) {
    console.error('❌ JSON 구문 오류:', e.message);
    console.error('원본:\n', jsonMatch[1]);
    process.exit(1);
  }

  // Validate required fields
  const required = ['id', 'name', 'aliases', 'type', 'industry', 'logo', 'benefits', 'workStyle'];
  const missing = required.filter(k => !(k in data));
  if (missing.length) {
    console.error(`⚠️  누락된 필드: ${missing.join(', ')}`);
  }

  console.log('✅ 스크래핑 완료!\n');

  // ── 1) 회사 기본 정보 ──
  const typeLabels = {large:'대기업',mid:'중견기업',startup:'스타트업',foreign:'외국계',public:'공기업',freelance:'프리랜서'};
  console.log('━'.repeat(60));
  console.log('  📋 스크래핑 결과');
  console.log('━'.repeat(60));
  console.log(`  회사명  : ${data.name} (${data.id})`);
  console.log(`  유형    : ${typeLabels[data.type] || data.type} (${data.type})`);
  console.log(`  업종    : ${data.industry}`);
  console.log(`  로고    : ${data.logo}`);
  console.log(`  별칭    : ${data.aliases.join(', ')}`);
  console.log();

  // ── 2) 근무 형태 ──
  const ws = data.workStyle || {};
  console.log('  🏠 근무 형태');
  console.log(`    원격근무      : ${ws.remote ? '✓' : '✗'}`);
  console.log(`    유연출퇴근    : ${ws.flex ? '✓' : '✗'}`);
  console.log(`    자율휴가      : ${ws.unlimitedPTO ? '✓' : '✗'}`);
  console.log(`    리프레시 휴가 : ${ws.refreshLeave || '-'}`);
  console.log(`    야근 문화     : ${ws.overtime || '-'}`);
  console.log();

  // ── 3) 복지 항목 목록 ──
  const catLabels = {money:'💰 금전',health:'🏥 건강',housing:'🏠 주거',edu:'📚 교육',family:'👨‍👩‍👧 가족',life:'🎯 생활',leave:'🌴 휴가'};
  const benCount = data.benefits ? data.benefits.length : 0;
  const autoCount = data.benefits ? data.benefits.filter(b => b.badge === 'auto').length : 0;
  const estCount = benCount - autoCount;
  const totalVal = data.benefits ? data.benefits.reduce((s,b) => s + (b.val || 0), 0) : 0;

  console.log(`  🎁 복지 항목 (${benCount}개 — 검증 ${autoCount} / 추정 ${estCount} | 합계 ${totalVal.toLocaleString()}만원/년)`);
  console.log('  ' + '─'.repeat(56));
  console.log('  ' + padR('항목', 30) + padR('카테고리', 10) + padR('연간(만원)', 10) + '신뢰');
  console.log('  ' + '─'.repeat(56));
  for (const b of (data.benefits || [])) {
    const badge = b.badge === 'auto' ? '✓검증' : '~추정';
    const valStr = b.qual ? '(정성적)' : String(b.val || 0);
    console.log('  ' + padR(b.name, 30) + padR(catLabels[b.cat] || b.cat, 10) + padR(valStr, 10) + badge);
    if (b.note) console.log('  ' + ' '.repeat(2) + `↳ ${b.note}`);
    if (b.qual && b.qualText) console.log('  ' + ' '.repeat(2) + `↳ ${b.qualText}`);
  }
  console.log();

  // ── 4) DB 저장 계획 ──
  console.log('━'.repeat(60));
  console.log('  🗄️  DB 저장 계획 (3개 테이블)');
  console.log('━'.repeat(60));
  console.log();

  // 4-a) companies
  const wsJson = JSON.stringify({
    remote: !!ws.remote, flex: !!ws.flex, unlimitedPTO: !!ws.unlimitedPTO,
    refreshLeave: ws.refreshLeave || '', overtime: ws.overtime || ''
  });
  console.log('  [1] companies — 1행 INSERT');
  console.log('  ' + '─'.repeat(56));
  console.log(`  INSERT INTO companies (id, name, type_id, industry, logo, work_style)`);
  console.log(`  VALUES ('${esc(data.id)}', '${esc(data.name)}', '${esc(data.type)}', '${esc(data.industry)}', '${esc(data.logo)}', '${esc(wsJson)}');`);
  console.log();

  // 4-b) company_aliases
  console.log(`  [2] company_aliases — ${data.aliases.length}행 INSERT`);
  console.log('  ' + '─'.repeat(56));
  for (const alias of data.aliases) {
    console.log(`  INSERT INTO company_aliases (company_id, alias) VALUES ('${esc(data.id)}', '${esc(alias)}');`);
  }
  console.log();

  // 4-c) company_benefits
  console.log(`  [3] company_benefits — ${benCount}행 INSERT`);
  console.log('  ' + '─'.repeat(56));
  for (let i = 0; i < (data.benefits || []).length; i++) {
    const b = data.benefits[i];
    console.log(`  INSERT INTO company_benefits (company_id, ben_key, name, val, category, badge, note, is_qualitative, qual_text, sort_order)`);
    console.log(`  VALUES ('${esc(data.id)}', '${esc(b.key)}', '${esc(b.name)}', ${b.val || 0}, '${esc(b.cat)}', '${esc(b.badge || 'est')}', ${b.note ? "'" + esc(b.note) + "'" : 'NULL'}, ${b.qual ? 'TRUE' : 'FALSE'}, ${b.qualText ? "'" + esc(b.qualText) + "'" : 'NULL'}, ${i});`);
  }
  console.log();
  console.log('━'.repeat(60));
  console.log(`  합계: ${1 + data.aliases.length + benCount}행 INSERT (3개 테이블)`);
  console.log('━'.repeat(60));

  // ── 5) JSON 원본 출력 ──
  console.log();
  console.log('📎 원본 JSON (--save 옵션으로 자동 저장 예정):');
  console.log(JSON.stringify(data, null, 2));
}

function padR(str, len) {
  const s = String(str);
  // Approximate: count CJK characters as width 2
  let w = 0;
  for (const ch of s) w += ch.charCodeAt(0) > 0x7f ? 2 : 1;
  return s + ' '.repeat(Math.max(0, len - w));
}

function esc(s) {
  if (!s) return '';
  return String(s).replace(/'/g, "\\'").replace(/\n/g, ' ');
}

// ━━ Main ━━
const company = process.argv[2];
if (!company) {
  console.log(`
  회사 복지 스크래퍼 (Claude API + Web Search)
  ─────────────────────────────────────────────
  사용법: ANTHROPIC_API_KEY=sk-... node scrape-benefits.js "회사명"

  예시:
    node scrape-benefits.js "삼성전자"
    node scrape-benefits.js "네이버"
    node scrape-benefits.js "카카오"

  결과를 미리보기로 출력하고, DB 저장 계획(SQL)을 보여줍니다.
  `);
  process.exit(0);
}

if (!process.env.ANTHROPIC_API_KEY) {
  console.error('❌ ANTHROPIC_API_KEY 환경변수를 설정해주세요.');
  console.error('   예: ANTHROPIC_API_KEY=sk-ant-... node scrape-benefits.js "회사명"');
  process.exit(1);
}

scrape(company).catch(err => {
  console.error('❌ 오류 발생:', err.message);
  process.exit(1);
});
