---
name: fe
description: 프론트엔드(index.html) 개발 전문 에이전트
user-invocable: true
---

# /fe — 프론트엔드 개발

사용자가 `/fe {작업 설명}` 을 실행하면 아래 단계를 수행합니다.

## 실행 단계

### 1단계: 변경 대상 파악

`index.html` (1,746행)을 Read하여 변경 대상 섹션을 찾습니다.
섹션은 ASCII 주석 헤더로 구분됩니다:

| 헤더 | 행 범위 (대략) | 내용 |
|------|---------------|------|
| `// ━━ LANDING ━━` | CSS+HTML 앞부분 | 랜딩 페이지 |
| `// ━━ SHARED ━━` | CSS 중간 | 공통 CSS 유틸리티 |
| `// ━━ PROFILER ━━` | CSS+HTML+JS | 커리어 가치 진단 |
| `// ━━ SEARCH ━━` | JS | 회사 검색 + 선택 |
| `// ━━ BENEFITS ━━` | JS | 복지 설정 + 계산 |
| `// ━━ WORK STYLE ━━` | JS | 근무 형태 (야근, 재택, 유연) |
| `// ━━ PRIORITY ━━` | JS | 우선순위 + 희생 선택 |
| `// ━━ COMPARE ENGINE ━━` | JS 1300-1700 | 핵심 비교 + 리포트 생성 |
| `// ━━ INIT ━━` | JS 마지막 | 앱 초기화 |

### 2단계: 구현

Edit 도구로 `index.html` 을 수정합니다.

**구조 규칙:**
- `<head>` > `<style>` — 모든 CSS
- `<body>` — 모든 HTML 마크업 (3개 화면: `s-landing`, `s-profiler`, `s-input`)
- `<body>` 하단 `<script>` — 모든 JavaScript

**변경 시 반드시 확인:**
1. `compare()` 함수 내부 수정 시 — 변수 섀도잉 여부 체크 (barWA/barWB 등)
2. benefits 관련 — `val`(숫자)과 `checked`(boolean) 구분
3. 초과근무 — 포괄임금(`inclusive`) vs 비포괄(`separate`) 계산 차이
4. 새 전역 변수 추가 시 — `saveDraft()`/`restoreDraft()`에 포함 여부 확인

### 3단계: 완료 출력

```
## 변경 완료
- index.html 1450-1480행: OT 계산 UI 렌더링 추가
- 추가 함수: renderOTCalc(s)
- CSS: .ot-calc-box 클래스 추가

### 다음 추천
- `/test` — 변경 검증
- `/audit` — 코드 리뷰
```

---

## 필수 컨벤션

### 변수 네이밍
| 종류 | 규칙 | 예시 |
|------|------|------|
| 변수 | camelCase (축약) | `pfJob`, `wsState`, `curPri`, `benS` |
| 함수 | camelCase | `doSearch()`, `compare()`, `calc()`, `renderBen()` |
| 상수 | UPPER_SNAKE_CASE | `DIMS`, `OT_HRS`, `DB`, `PRIORITIES` |
| CSS 클래스 | kebab-case (축약) | `.pf-intro`, `.ws-btn`, `.vs-card` |
| DOM ID | camelCase 또는 축약 | `sA`, `sB`, `tA`, `tB`, `blA`, `blB` |

### 사이드 패턴
- 함수 첫 파라미터 `s` = `'a'`(현직) 또는 `'b'`(이직처)
- DOM 요소 ID: `{접두사}{s.toUpperCase()}` (예: `sA`, `sB`, `otBtnsA`, `otBtnsB`)
- 상태 객체: `wsState.a`, `wsState.b`, `benS.a`, `benS.b`

```javascript
// 올바른 패턴
function setWS(s, key, val) {
  wsState[s][key] = val;
  document.getElementById('otBtns' + s.toUpperCase())...
}

// HTML에서 호출
onclick="setWS('a','ot','low')"
```

### HTML 렌더링 패턴
- **리스트**: `.map().join('')` → `innerHTML`
- **조건부**: 삼항 연산자 `?:`
- **이벤트**: 인라인 `onclick` (addEventListener 사용 안 함)

```javascript
// 올바른 패턴
el.innerHTML = items.map(item =>
  `<button class="ws-btn${item.active ? ' on' : ''}"
    onclick="setWS('${s}','${key}','${item.val}')">
    ${item.label}
  </button>`
).join('');
```

### CSS 패턴
- 커스텀 프로퍼티 사용: `--bg-0`~`--bg-4` (배경), `--t1`~`--t4` (텍스트)
- 색상 악센트: `--blue`, `--amber`, `--green`, `--red`, `--purple`, `--gold` (각각 `-d` dim 변형)
- 반응형: `@media(max-width:480px)`
- 애니메이션: `fadeUp`, `slideUp` with `cubic-bezier`

### UI 텍스트
- **사용자에게 보이는 텍스트**: 한국어
- **코드(변수, 함수, 주석)**: 영어

---

## 위험 지점

| 위치 | 위험 | 대응 |
|------|------|------|
| `compare()` ~300행 | 변수 섀도잉 | `// [FIX]` 주석 확인, 새 변수명 충돌 방지 |
| `compare()` 입력 검증 | null/undefined | 새 비교 로직은 반드시 null 체크 |
| benefits `val` vs `checked` | 타입 혼동 | 합산 시 `val`(숫자) 사용, 토글은 `checked`(boolean) |
| OT 계산 | inclusive/separate | 포괄임금은 초과근무수당 0, 비포괄은 시급×1.5 |
| `innerHTML` | XSS 위험 | 사용자 입력은 `esc()` 함수로 이스케이프 |

---

## 주요 참조

| 함수 | 역할 | 행 (대략) |
|------|------|----------|
| `compare()` | 메인 비교 리포트 생성 | 1300-1600 |
| `calc()` | 실시간 요약 업데이트 | 입력 변경 시 호출 |
| `doSearch(s)` | 회사 검색 (디바운스 300ms) | SEARCH 섹션 |
| `selComp(s, id)` | 회사 선택 → 복지/근무 자동 채움 | SEARCH 섹션 |
| `renderBen(s)` | 복지 목록 렌더링 | BENEFITS 섹션 |
| `setWS(s, key, val)` | 근무 스타일 상태 업데이트 | WORK STYLE 섹션 |
| `go(screenId)` | SPA 화면 전환 | INIT 섹션 |
| `apiFetch(path, opts)` | API 호출 (JWT 자동 첨부) | INIT 섹션 |
| `saveDraft()` | localStorage 자동 저장 (디바운스) | INIT 섹션 |
| `esc(str)` | HTML 이스케이프 (XSS 방지) | SHARED 섹션 |
