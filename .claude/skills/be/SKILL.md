---
name: be
description: 백엔드(FastAPI) + DB(MySQL) 개발 전문 에이전트
user-invocable: true
---

# /be — 백엔드 + DB 개발

사용자가 `/be {작업 설명}` 을 실행하면 아래 단계를 수행합니다.

## 실행 단계

### 1단계: 작업 유형 판별

작업 설명을 분석하여 유형을 결정합니다:

| 유형 | 판별 기준 | 작업 순서 |
|------|----------|----------|
| **API 추가** | 새 엔드포인트 필요 | models/ → routers/ → main.py 등록 |
| **스키마 변경** | 테이블/컬럼 추가·수정 | schema.sql DDL → seed 업데이트 → models/ → routers/ 동기화 |
| **쿼리 수정** | 기존 엔드포인트 로직 변경 | routers/ Edit |
| **서비스 추가** | 비즈니스 로직 분리 | services/ 생성 → routers/에서 import |

### 2단계: 기존 코드 읽기

변경 대상 파일을 **반드시** 먼저 Read합니다:

- `server/main.py` — 라우터 등록 현황 (36행)
- `server/database.py` — DB 헬퍼 패턴 (98행)
- 관련 `server/routers/*.py`, `server/models/*.py`
- 스키마 변경 시: `server/seed/schema.sql` (211행)

### 3단계: 구현

#### API 추가 시

1. `server/models/{모듈}.py` — Pydantic 요청/응답 모델 작성
2. `server/routers/{모듈}.py` — 엔드포인트 함수 작성
3. `server/main.py` — 라우터 등록:
   ```python
   from routers import {모듈}
   app.include_router({모듈}.router, prefix="/api/v1/{경로}", tags=["{태그}"])
   ```

#### 스키마 변경 시

1. `server/seed/schema.sql` 수정 — DDL 추가
2. 마이그레이션 SQL을 별도로 사용자에게 제시:
   ```sql
   -- 마이그레이션: {변경 설명}
   ALTER TABLE {테이블} ADD COLUMN ...;
   ```
3. 관련 models/, routers/ 동기화

### 4단계: 완료 출력

```
## 변경 완료
| 파일 | 변경 내용 |
|------|----------|
| server/models/user.py | PasswordResetReq 모델 추가 |
| server/routers/auth.py | POST /reset-password 엔드포인트 |
| server/main.py | 변경 없음 (기존 auth 라우터에 추가) |

### 다음 추천
- `/test auth` — 새 엔드포인트 테스트 작성
- `/fe 비밀번호 재설정 UI` — 프론트엔드 연동
```

---

## 필수 컨벤션

### Python 코드
- 파일명/함수: `snake_case` (예: `auth_service.py`, `create_token()`)
- 클래스: `PascalCase` (예: `RegisterReq`, `TokenResp`)
- 설정 상수: `UPPER_SNAKE_CASE` (예: `DB_HOST`, `JWT_SECRET`)
- 비동기: 모든 라우터 함수는 `async def`

### SQL 쿼리
- **Raw SQL만 사용** — ORM 사용 금지
- **`%s` 플레이스홀더** 필수 — f-string, format() SQL 절대 금지
- DB 헬퍼 사용:
  ```python
  from database import fetch_all, fetch_one, execute
  rows = await fetch_all("SELECT * FROM users WHERE email = %s", (email,))
  row = await fetch_one("SELECT * FROM companies WHERE id = %s", (company_id,))
  last_id = await execute("INSERT INTO users (email, password_hash) VALUES (%s, %s)", (email, hashed))
  ```
- `autocommit=True` — 멀티 INSERT 시 부분 실패 가능성 인지

### DB 스키마 규칙
- **ENUM 사용 금지** — 모든 컬럼 `VARCHAR`, 허용 값은 `COMMENT`에 명시
- **모든 컬럼에 한국어 COMMENT 필수** — 용도, 단위, 허용 값 범위
  ```sql
  company_type VARCHAR(20) NOT NULL COMMENT '기업유형 (large, startup, mid, foreign, public, freelance)'
  ```
- **FK 참조 대상 COMMENT에 명시**:
  ```sql
  user_id INT NOT NULL COMMENT '사용자 FK (users.id)'
  ```
- **금액 단위: 만원** — COMMENT에 `(만원)` 명시
- **JSON 컬럼**: `TEXT` 타입 + COMMENT에 구조 설명

### Pydantic 모델
- 요청: `{동작}Req` (예: `RegisterReq`, `ComparisonReq`)
- 응답: `{동작}Resp` 또는 `{엔티티}Detail` (예: `TokenResp`, `CompanyDetail`)
- Optional 필드는 `= None`으로 기본값

---

## 주요 참조 파일

| 파일 | 내용 | 행수 |
|------|------|------|
| `server/main.py` | FastAPI 앱, 라우터 등록, 미들웨어 | 36 |
| `server/database.py` | aiomysql 풀, fetch_all/one/execute | 98 |
| `server/config.py` | 환경변수 (DB, JWT, CORS) | 16 |
| `server/seed/schema.sql` | 전체 DDL (15 테이블) | 211 |
| `server/routers/auth.py` | 인증 패턴 참조 | 27 |
| `server/routers/comparisons.py` | 복잡한 CRUD 패턴 참조 | 126 |
| `server/routers/reference.py` | 캐시 + 배치 쿼리 패턴 | 118 |
| `server/models/*.py` | Pydantic 모델 참조 | 145 |
| `server/services/auth_service.py` | 서비스 레이어 패턴 | 23 |

## 주의사항

- `database.py`의 `_convert_row()`가 Decimal→float 자동 변환
- `cache.py`의 TTL 캐시 — 데이터 변경 시 `delete()` 호출 필요
- 라우터에서 인증 필요 시: `user_id: int = Depends(get_current_user)`
- rate_limiter.py가 엔드포인트별 제한 설정 — 새 엔드포인트는 기본 60/분
