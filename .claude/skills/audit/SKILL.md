---
name: audit
description: 코드 리뷰 + 보안 점검 통합 에이전트
user-invocable: true
---

# /audit — 코드 리뷰 + 보안 점검

사용자가 `/audit`, `/audit {파일}`, 또는 `/audit full` 을 실행하면 아래 단계를 수행합니다.

## 실행 단계

### 1단계: 범위 결정

| 호출 | 범위 |
|------|------|
| `/audit` | 최근 커밋 변경분 (`git diff HEAD~1`) |
| `/audit {파일}` | 지정 파일만 |
| `/audit full` | 전체 코드베이스 |

### 2단계: 변경 수집

- `/audit`: `Bash "git diff HEAD~1 --name-only"` → 변경 파일 목록, `Bash "git diff HEAD~1"` → diff 내용
- `/audit {파일}`: `Read {파일}`
- `/audit full`: `Glob "server/**/*.py"` + `Read index.html`

### 3단계: 품질 검사 (5항목)

다음 항목을 **병렬**로 검사합니다:

#### Q1. 컨벤션 준수
- **FE**: camelCase 변수, side 패턴 (`s='a'/'b'`), innerHTML+onclick, 한국어 UI
- **BE**: snake_case 함수/파일, PascalCase 클래스, `%s` SQL
- **DB**: ENUM 미사용, COMMENT 필수, 금액=만원
- `Grep` 패턴: `f"SELECT|f"INSERT|f"UPDATE|f"DELETE` → SQL 인젝션 위험

#### Q2. 코드 중복 / 불필요 복잡성
- 같은 쿼리 반복 여부
- 불필요한 추상화 또는 미사용 변수

#### Q3. 에러 핸들링
- API 응답에서 에러 상태 처리 여부
- null/undefined 체크 (특히 `compare()` 내부)

#### Q4. 성능
- N+1 쿼리 패턴 (`for` 루프 안 `fetch_one`)
- 불필요한 전체 로드 (pagination 미적용)
- 캐시 무효화 누락

#### Q5. 타입 안전성
- Pydantic 모델 누락 (dict 직접 반환)
- Optional 필드 처리

### 4단계: 보안 검사 (6항목)

#### S1. SQL 인젝션
```
Grep "f['\"].*SELECT|f['\"].*INSERT|f['\"].*UPDATE|f['\"].*DELETE" --type py
Grep "format.*SELECT|format.*INSERT" --type py
```
발견 시 🔴 CRITICAL

#### S2. XSS
- `index.html`에서 `innerHTML`에 사용자 입력 직접 삽입 여부
- `esc()` 함수 사용 확인
- `onclick` 내 문자열 보간에서 인용부호 이스케이프 여부

#### S3. 인증/인가
- 보호 필요 엔드포인트에 `Depends(get_current_user)` 있는지
- JWT 토큰 만료 처리
- 비밀번호 해싱 (bcrypt 사용 확인)

#### S4. 시크릿 노출
```
Grep "password|secret|key|token" --glob "*.py" --glob "*.js" --glob "*.html"
```
`.env` 파일이 `.gitignore`에 있는지 확인

#### S5. 의존성
- `server/requirements.txt` 버전 확인
- 알려진 취약 버전 여부 (주요 패키지만)

#### S6. 헤더/CORS
- `server/main.py` CORS 설정 확인 (와일드카드 `*` 사용 여부)
- `server/deploy/nginx.conf` 보안 헤더 확인

### 5단계: 리포트 출력

```
## 감사 리포트 (YYYY-MM-DD)

### 범위
- 최근 커밋: {커밋 해시} "{메시지}"
- 변경 파일: {N}개

### 품질 ({건수}건)
- ⚠️ server/routers/companies.py:45 — LIMIT 20 하드코딩, 환경변수로 분리 권장
- ✅ 컨벤션 준수
- ✅ 에러 핸들링 양호

### 보안 ({건수}건)
- 🔴 {파일}:{행} — SQL f-string 발견 (CRITICAL)
- ⚠️ nginx.conf — X-Frame-Options 헤더 누락
- ✅ JWT/bcrypt 정상

### 요약
품질: ✅{N} ⚠️{N} | 보안: 🔴{N} ⚠️{N} ✅{N}

### 조치 필요
1. 🔴 SQL 인젝션 수정 → `/be {파일} SQL 파라미터화`
2. ⚠️ nginx 보안 헤더 → `/deploy nginx 보안 헤더 추가`
```

---

## 심각도 기준

| 등급 | 기준 | 예시 |
|------|------|------|
| 🔴 CRITICAL | 즉시 수정 필요 | SQL 인젝션, 시크릿 하드코딩, 인증 우회 |
| ⚠️ WARNING | 개선 권장 | 미사용 변수, 하드코딩 값, 헤더 누락 |
| ✅ PASS | 문제 없음 | 정상 패턴 확인 |

## 주의사항

- 리팩토링 제안은 사용자가 요청한 경우에만
- 코드 스타일 지적은 프로젝트 컨벤션 기준 (일반적 Python/JS 스타일 아님)
- `// [FIX]` 주석이 있는 코드는 이미 수정된 항목 — 재지적 금지
