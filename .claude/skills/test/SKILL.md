---
name: test
description: 테스트 작성 및 실행 전문 에이전트
user-invocable: true
---

# /test — 테스트 작성 및 실행

사용자가 `/test` 또는 `/test {대상}` 을 실행하면 아래 단계를 수행합니다.

## 실행 단계

### 1단계: 인자 파싱

| 호출 | 동작 |
|------|------|
| `/test` | 전체 테스트 실행 |
| `/test {대상}` | 해당 대상 테스트 확인 → 없으면 작성 → 실행 |

대상 예시: `auth`, `companies`, `comparisons`, `profiler`, `landing`, `cache`, `models`

### 2단계: 기존 테스트 읽기

Read `server/tests/test_all.py` — 기존 테스트 구조 파악 (253행, 23개 테스트).

**기존 테스트 프레임워크:** 커스텀 러너 (pytest 아님)
```python
# 테스트 함수 패턴
def test_{기능}_{시나리오}():
    # arrange
    # act
    # assert
    assert 조건

# 섹션 구분
# ━━ {SECTION NAME} ━━

# 러너 (파일 하단)
if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    ...
```

### 3단계: 전체 실행 (`/test`)

```bash
cd server && python tests/test_all.py
```

결과를 파싱하여 리포트 출력:
```
## 테스트 결과
✓ 23/23 통과 (0 실패)

### 커버리지 현황
| 영역 | 테스트 수 | 상태 |
|------|----------|------|
| Auth Service | 3 | ✅ |
| Cache | 4 | ✅ |
| DB Helpers | 2 | ✅ |
| Pydantic Models | 6 | ✅ |
| FastAPI Integration | 5 | ✅ |
| Visitor Tracking | 1 | ✅ |
| Scrape Tools | 2 | ✅ |

### 미커버 영역
- ⚠️ API 엔드포인트 (companies/search, comparisons CRUD)
- ⚠️ 비즈니스 로직 (OT 계산, 복지 합산)
- ⚠️ 에러 핸들링 (DB 미연결, 잘못된 입력)
```

### 4단계: 특정 대상 테스트 (`/test {대상}`)

1. `test_all.py`에서 `# ━━ {대상} ━━` 섹션 검색
2. **있으면**: 해당 섹션 테스트만 실행
3. **없으면**: 테스트 작성 후 실행

#### 테스트 작성 규칙

`test_all.py`에 새 섹션을 **추가** (기존 테스트 절대 수정 안 함):

```python
# ━━ {SECTION NAME} ━━

def test_{기능}_{시나리오}():
    """테스트 설명 (한국어 OK)"""
    # arrange
    from {모듈} import {함수}
    # 또는 FastAPI TestClient:
    from fastapi.testclient import TestClient
    import main
    client = TestClient(main.app, raise_server_exceptions=False)

    # act
    result = ...

    # assert
    assert 조건
```

**위치**: `# ━━ RUNNER ━━` 섹션 바로 위에 추가합니다.

#### 테스트 유형별 패턴

**단위 테스트** (DB 불필요):
```python
def test_hash_password_returns_different_hash():
    from services.auth_service import hash_password
    h1 = hash_password("test")
    h2 = hash_password("test")
    assert h1 != h2  # bcrypt salt differs
```

**FastAPI 통합 테스트** (TestClient):
```python
def test_company_search_requires_query():
    from fastapi.testclient import TestClient
    import main
    client = TestClient(main.app, raise_server_exceptions=False)
    r = client.get("/api/v1/companies/search")
    assert r.status_code == 422

def test_health_returns_ok():
    client = TestClient(main.app, raise_server_exceptions=False)
    r = client.get("/api/v1/health")
    assert r.status_code == 200
```

**Pydantic 모델 검증**:
```python
def test_comparison_req_rejects_invalid_type():
    from models.comparison import ComparisonReq
    try:
        ComparisonReq(type_a="invalid", type_b="large", priority_key="salary")
        # type_a는 varchar이므로 Pydantic 레벨에서는 통과 — DB 레벨 체크
        pass
    except Exception:
        pass
```

### 5단계: 결과 출력

```
## 테스트 결과
✓ {통과}/{전체} 통과 ({실패} 실패)

### 새로 추가된 테스트
- test_company_search_returns_results
- test_company_search_empty_query

### 다음 추천
- `/audit` — 코드 리뷰
```

---

## 현재 커버리지 갭 (우선순위)

| 우선순위 | 영역 | 설명 | 테스트 수 |
|---------|------|------|----------|
| 1 | API 엔드포인트 | companies/search, /{id}, comparisons CRUD | 0 |
| 2 | 인증 플로우 | register → login → token 사용 → 401 | 기본만 |
| 3 | 비즈니스 로직 | 초과근무 계산, 복지 합산, 시급 환산 | 0 |
| 4 | 에러 핸들링 | 잘못된 입력, 존재하지 않는 리소스 | 0 |
| 5 | 캐시 무효화 | 데이터 변경 후 캐시 갱신 확인 | 0 |

## 주의사항

- `raise_server_exceptions=False` — 서버 에러도 HTTP 응답으로 받음
- DB 연결 필요 테스트는 현재 환경에서 실패할 수 있음 — DB 불필요 테스트 우선
- `import main`이 DB 풀 초기화 시도 — TestClient는 lifespan 자동 처리
- 테스트 함수는 반드시 `test_` 접두사 (커스텀 러너가 자동 수집)
