---
name: batch-benefits
description: 복지 데이터 배치 처리 — 미처리 회사 현황 파악 및 순차 처리 안내
user-invocable: true
---

# /batch-benefits — 복지 데이터 배치 처리

사용자가 `/batch-benefits` 를 실행하면 아래 단계를 수행합니다.

## 실행 단계

### 1단계: 처리 현황 파악

다음을 **병렬**로 수집합니다:

1. `Glob "server/seed/benefit/*.sql"` → 이미 SQL 생성된 회사 목록
2. `Glob "server/seed/benefit/*.txt"` → 스크래핑 완료, 파싱 대기 회사 목록
3. `Read server/tools/scrape_benefits.py` 26-42행 → `KNOWN_IDS` 딕셔너리에서 전체 회사 목록

### 2단계: 분류

각 회사를 3가지 상태로 분류합니다:

| 상태 | 조건 | 다음 액션 |
|------|------|----------|
| ✅ 완료 | `.sql` 파일 존재 | 없음 |
| 📝 파싱 대기 | `.txt` 존재, `.sql` 없음 | `/parse-benefits {회사명}` |
| 🔍 조사 필요 | `.txt`도 `.sql`도 없음 | `/research-benefits {회사명}` |

### 3단계: 현황 리포트 출력

```
## 복지 데이터 배치 현황

| 상태 | 회사 수 |
|------|---------|
| ✅ 완료 | 1 (삼성전자) |
| 📝 파싱 대기 | 12 |
| 🔍 조사 필요 | 187 |
| **합계** | **200** |

### 📝 파싱 대기 (바로 처리 가능)
| # | 회사명 | ID | 명령어 |
|---|--------|-----|--------|
| 1 | SK하이닉스 | skhynix | `/parse-benefits SK하이닉스` |
| 2 | LG전자 | lg_elec | `/parse-benefits LG전자` |
| ... | ... | ... | ... |

### 🔍 조사 필요 (웹 검색 필요)
| # | 회사명 | ID | 명령어 |
|---|--------|-----|--------|
| 1 | 카카오 | kakao | `/research-benefits 카카오` |
| 2 | 네이버 | naver | `/research-benefits 네이버` |
| ... | ... | ... | ... |

### 다음 단계
파싱 대기 회사부터 처리하는 것이 효율적입니다.
위 명령어를 복사하여 실행하세요.
```

### 4단계: 사용자 선택 대기

AskUserQuestion으로 다음 질문:
- "파싱 대기 회사 {N}개를 순차 처리하시겠습니까?"
- 옵션: "네, 첫 번째부터 시작", "특정 회사 선택", "나중에"

사용자가 "네"를 선택하면:
- 첫 번째 파싱 대기 회사의 `/parse-benefits {회사명}` 명령어를 출력
- **주의**: 이 스킬은 다른 스킬을 직접 호출할 수 없습니다. 사용자가 명령어를 실행해야 합니다.

---

## 처리 워크플로우 (사용자 안내용)

```
/batch-benefits          → 현황 확인
/parse-benefits {회사A}  → .txt → .sql 생성 (파싱 대기)
/parse-benefits {회사B}  → .txt → .sql 생성
...
/research-benefits {회사C} → 웹 검색 → DB 저장 (조사 필요)
/batch-benefits          → 진행률 재확인
```

## 참조 파일

| 파일 | 역할 |
|------|------|
| `server/tools/scrape_benefits.py:26-42` | KNOWN_IDS — 회사명→ID 매핑 |
| `server/seed/benefit/*.sql` | 완료된 SQL 파일 |
| `server/seed/benefit/*.txt` | 스크래핑된 원본 텍스트 |
| `server/seed/benefit/삼성전자.sql` | SQL 출력 포맷 참조 (gold standard) |
