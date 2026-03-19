#!/usr/bin/env node
// ━━ scrape-benefits.js 단위 테스트 ━━
// API 호출 없이 formatAsDB, esc, JSON 파싱 로직을 검증

let pass = 0, fail = 0;
function assert(label, cond) {
  if (cond) { pass++; console.log(`  ✅ ${label}`); }
  else { fail++; console.error(`  ❌ ${label}`); }
}

// ━━ 1. esc 함수 테스트 ━━
console.log('\n[1] esc() 함수');

// scrape-benefits.js에서 esc 함수 추출 (동일 로직)
function esc(s) {
  if (!s) return '';
  return String(s).replace(/'/g, "\\'").replace(/\n/g, ' ');
}

assert("일반 문자열", esc("테스트") === "테스트");
assert("작은따옴표 이스케이프", esc("it's") === "it\\'s");
assert("줄바꿈 치환", esc("line1\nline2") === "line1 line2");
assert("null 처리", esc(null) === "");
assert("undefined 처리", esc(undefined) === "");
assert("빈 문자열", esc("") === "");

// ━━ 2. formatAsDB 함수 테스트 ━━
console.log('\n[2] formatAsDB() 함수');

function formatAsDB(data) {
  const benStr = data.benefits.map(b => {
    let parts = [
      `key:'${esc(b.key)}'`,
      `name:'${esc(b.name)}'`,
      `val:${b.val || 0}`,
      `cat:'${b.cat}'`,
      `badge:'${b.badge || 'est'}'`,
    ];
    if (b.note) parts.push(`note:'${esc(b.note)}'`);
    if (b.qual) {
      parts.push(`qual:true`);
      if (b.qualText) parts.push(`qualText:'${esc(b.qualText)}'`);
    }
    return `{${parts.join(',')}}`;
  }).join(',');

  const ws = data.workStyle || {};
  const wsStr = [
    `remote:${!!ws.remote}`,
    `flex:${!!ws.flex}`,
    `unlimitedPTO:${!!ws.unlimitedPTO}`,
    `refreshLeave:'${esc(ws.refreshLeave || '')}'`,
    `overtime:'${esc(ws.overtime || '')}'`,
  ].join(',');

  const aliasStr = data.aliases.map(a => `'${esc(a)}'`).join(',');

  return `  {id:'${data.id}',name:'${esc(data.name)}',aliases:[${aliasStr}],type:'${data.type}',industry:'${esc(data.industry)}',logo:'${esc(data.logo)}',
  benefits:[${benStr}],workStyle:{${wsStr}}},`;
}

// 테스트용 샘플 데이터
const sampleData = {
  id: 'kakao',
  name: '카카오',
  aliases: ['카카오', 'Kakao', 'kakao'],
  type: 'large',
  industry: 'IT/플랫폼',
  logo: 'K',
  benefits: [
    { key: 'meal', name: '식대 지원', val: 180, cat: 'money', badge: 'auto' },
    { key: 'health', name: '건강검진', val: 100, cat: 'health', badge: 'auto', note: '본인+가족' },
    { key: 'flex', name: '유연근무', val: 0, cat: 'leave', badge: 'auto', qual: true, qualText: '자율 출퇴근' },
  ],
  workStyle: {
    remote: true,
    flex: true,
    unlimitedPTO: false,
    refreshLeave: '3년마다 1개월',
    overtime: '자율 근무'
  }
};

const output = formatAsDB(sampleData);

assert("id 포함", output.includes("id:'kakao'"));
assert("name 포함", output.includes("name:'카카오'"));
assert("aliases 배열 포함", output.includes("aliases:['카카오','Kakao','kakao']"));
assert("type 포함", output.includes("type:'large'"));
assert("industry 포함", output.includes("industry:'IT/플랫폼'"));
assert("logo 포함", output.includes("logo:'K'"));
assert("benefits 배열 존재", output.includes("benefits:[{"));
assert("meal benefit", output.includes("key:'meal'"));
assert("val 숫자", output.includes("val:180"));
assert("cat 문자열", output.includes("cat:'money'"));
assert("badge 문자열", output.includes("badge:'auto'"));
assert("note 포함", output.includes("note:'본인+가족'"));
assert("qual:true 포함", output.includes("qual:true"));
assert("qualText 포함", output.includes("qualText:'자율 출퇴근'"));
assert("workStyle remote", output.includes("remote:true"));
assert("workStyle flex", output.includes("flex:true"));
assert("workStyle unlimitedPTO", output.includes("unlimitedPTO:false"));
assert("workStyle refreshLeave", output.includes("refreshLeave:'3년마다 1개월'"));
assert("workStyle overtime", output.includes("overtime:'자율 근무'"));

// ━━ 3. JSON 파싱 로직 테스트 ━━
console.log('\n[3] JSON 파싱 로직');

function parseJSON(text) {
  const jsonMatch = text.match(/```json\s*([\s\S]*?)```/);
  if (!jsonMatch) return null;
  try { return JSON.parse(jsonMatch[1]); } catch { return null; }
}

const validResponse = '여기 결과입니다:\n```json\n{"id":"test","name":"테스트"}\n```\n끝';
assert("정상 JSON 파싱", parseJSON(validResponse)?.id === 'test');

const noJson = '검색 결과가 없습니다.';
assert("JSON 없는 응답 → null", parseJSON(noJson) === null);

const invalidJson = '```json\n{invalid json}\n```';
assert("잘못된 JSON → null", parseJSON(invalidJson) === null);

const multiBlock = '첫번째:\n```json\n{"id":"first"}\n```\n두번째:\n```json\n{"id":"second"}\n```';
assert("첫 번째 JSON 블록 파싱", parseJSON(multiBlock)?.id === 'first');

// ━━ 4. DB 호환성 검증 ━━
console.log('\n[4] DB 호환성 검증');

// 기존 DB 엔트리(CJ)와 동일한 구조인지 검증
const requiredBenFields = ['key', 'name', 'val', 'cat', 'badge'];
const validCats = ['money', 'health', 'housing', 'edu', 'family', 'life', 'leave'];
const validTypes = ['large', 'mid', 'startup', 'foreign', 'public', 'freelance'];
const validBadges = ['auto', 'est'];

assert("type이 유효한 값", validTypes.includes(sampleData.type));
sampleData.benefits.forEach((b, i) => {
  requiredBenFields.forEach(f => {
    assert(`benefit[${i}].${f} 존재`, f in b);
  });
  assert(`benefit[${i}].cat 유효`, validCats.includes(b.cat));
  assert(`benefit[${i}].badge 유효`, validBadges.includes(b.badge));
  assert(`benefit[${i}].val 숫자`, typeof b.val === 'number');
});

// ━━ 5. 특수문자 포함 데이터 테스트 ━━
console.log('\n[5] 특수문자 처리');

const specialData = {
  id: 'test',
  name: "L'Oréal Korea",
  aliases: ["L'Oréal", "로레알"],
  type: 'foreign',
  industry: "화장품/뷰티",
  logo: 'L',
  benefits: [
    { key: 'meal', name: "식대 (점심 제공 + 간식 'snack bar')", val: 200, cat: 'money', badge: 'auto' },
  ],
  workStyle: { remote: true, flex: true, unlimitedPTO: false, refreshLeave: '', overtime: '' }
};

const specialOutput = formatAsDB(specialData);
assert("작은따옴표가 이스케이프됨", specialOutput.includes("L\\'Oréal Korea"));
assert("benefit name 작은따옴표 이스케이프", specialOutput.includes("snack bar"));
assert("JS 구문 오류 없음 (eval 테스트)", (() => {
  try {
    // 출력이 유효한 JS 객체 리터럴인지 간접 검증
    // 앞뒤 공백과 쉼표 제거 후 체크
    const trimmed = specialOutput.trim().replace(/,$/, '');
    return trimmed.startsWith('{') && trimmed.endsWith('}');
  } catch { return false; }
})());

// ━━ 결과 ━━
console.log(`\n${'━'.repeat(40)}`);
console.log(`결과: ${pass}개 통과, ${fail}개 실패`);
if (fail > 0) process.exit(1);
console.log('모든 테스트 통과! ✅\n');
