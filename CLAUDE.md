# CLAUDE.md

## Project Overview

**직장 선택 OS (Job Choice OS)** — A Korean-language full-stack web application for comparing job offers across multiple criteria including compensation, work-life balance, job security, career growth, benefits, and company brand value.

- **Frontend**: Vanilla HTML/CSS/JavaScript SPA (`index.html`)
- **Backend**: Python FastAPI REST API with MySQL
- **Infra**: Oracle Cloud (OCI) Terraform IaC — Always Free ARM
- **Language**: Korean UI with English variable/function names

## File Structure

```
/
├── index.html                    # Frontend SPA (HTML + CSS + JS)
├── CLAUDE.md                     # This file
├── server/
│   ├── main.py                   # FastAPI entry point
│   ├── config.py                 # Environment variables (DB, JWT)
│   ├── database.py               # Async MySQL pool (aiomysql)
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Env template
│   ├── models/                   # Pydantic request/response models
│   │   ├── user.py               # RegisterReq, LoginReq, TokenResp
│   │   ├── company.py            # CompanyBrief, Benefit, CompanyDetail
│   │   ├── profiler.py           # Job, JobGroup, Profile, ProfilerResultReq
│   │   └── comparison.py         # ComparisonReq, ComparisonResp
│   ├── routers/                  # API endpoint handlers
│   │   ├── auth.py               # POST /register, /login
│   │   ├── companies.py          # GET /search, /{id}
│   │   ├── reference.py          # GET /all (cached reference data)
│   │   ├── profiler.py           # GET /jobs, /questions, /profiles; POST /results
│   │   └── comparisons.py        # POST/GET comparisons (user history)
│   ├── services/                 # Business logic
│   │   ├── auth_service.py       # Password hashing, JWT creation
│   │   └── cache.py              # In-memory TTL cache (1hr)
│   ├── middleware/
│   │   └── auth_middleware.py    # JWT Bearer token validation
│   ├── seed/
│   │   ├── schema.sql            # MySQL DDL (all tables)
│   │   └── seed.py               # Initial data population
│   └── deploy/
│       ├── nginx.conf            # Nginx reverse proxy + SSL
│       ├── jobchoice.service     # systemd service unit
│       └── my.cnf                # MySQL config (6GB RAM optimized)
└── infra/                        # Terraform IaC for OCI (Always Free)
    ├── provider.tf               # OCI provider config
    ├── variables.tf              # Variable declarations
    ├── network.tf                # VCN, subnet, security list
    ├── compute.tf                # ARM instance (VM.Standard.A1.Flex)
    ├── outputs.tf                # Public IP, SSH command
    └── terraform.tfvars.example  # Example variables
```

## Tech Stack

### Frontend
| Layer | Technology |
|-------|-----------|
| Language | Vanilla JavaScript (ES6+), HTML5, CSS3 |
| Build | None — direct browser execution |
| Fonts | Pretendard (Korean), JetBrains Mono (CDN) |
| HTTP | Fetch API → `/api/v1/*` |
| Auth storage | `localStorage` (`jc_token`) |

### Backend
| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.115.6 |
| Runtime | Python 3.11+ (async) |
| DB driver | aiomysql 0.2.0 (async pool, 2–10 conn) |
| Database | MySQL 8.0+ (utf8mb4) |
| Auth | JWT HS256 (24hr expiry) via python-jose |
| Password | bcrypt via passlib |
| Validation | Pydantic 2.10.4 |
| Server | Uvicorn (ASGI) |

### Infrastructure (Oracle Cloud — Always Free)
| Component | Config |
|-----------|--------|
| Compute | VM.Standard.A1.Flex (ARM), 2 OCPU, 12GB RAM |
| Region | ap-chuncheon-1 (춘천) |
| Network | VCN 10.0.0.0/16, public subnet 10.0.1.0/24 |
| Storage | 50GB boot volume (Always Free 최대 200GB) |
| Security | SSH restricted, HTTP/HTTPS open, MySQL blocked externally |
| Reverse proxy | Nginx (SSL via Let's Encrypt) |
| Process mgmt | systemd (auto-restart on failure) |

## Running the App

### Frontend only (offline mode)
Open `index.html` in a browser. Hardcoded data serves as fallback.

### Full stack (local)
```bash
# 1. MySQL setup
mysql -u root -e "CREATE DATABASE jobchoice CHARACTER SET utf8mb4;"
mysql -u root jobchoice < server/seed/schema.sql
python server/seed/seed.py

# 2. Backend
cd server
cp .env.example .env  # edit DB credentials, JWT_SECRET
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 3. Frontend
# Open index.html or serve via nginx
```

### Production deployment
```
Internet → Nginx (:443 SSL) ─┬─ /          → index.html (static)
                              └─ /api/v1/   → Uvicorn (:8000) → MySQL (:3306)
```

## API Endpoints

### Public
- `GET  /api/v1/health` — Health check
- `POST /api/v1/auth/register` — Create account (email, password, name)
- `POST /api/v1/auth/login` — Login → JWT token
- `GET  /api/v1/reference/all` — All companies, benefits, profiles, jobs, questions (1hr cache)
- `GET  /api/v1/companies/search?q=` — Company search (LIKE)
- `GET  /api/v1/companies/{id}` — Company detail
- `GET  /api/v1/profiler/jobs` — Job groups + jobs
- `GET  /api/v1/profiler/questions?scenario=` — Profiler questions
- `GET  /api/v1/profiler/profiles` — Career profiles

### Auth required (Bearer token)
- `POST /api/v1/profiler/results` — Save profiler result
- `POST /api/v1/comparisons` — Save comparison
- `GET  /api/v1/comparisons` — List user's comparisons
- `GET  /api/v1/comparisons/{id}` — Get specific comparison

## Database Schema

| Category | Tables |
|----------|--------|
| Reference | `company_types`, `companies`, `company_aliases`, `company_benefits`, `benefit_presets` |
| Profiler | `profiles`, `profile_job_fits`, `job_groups`, `jobs`, `profiler_questions`, `question_scenarios` |
| User | `users`, `profiler_results`, `comparisons` |

## Frontend Code Organization

Sections in `index.html` delimited by ASCII comment headers:

```
// ━━ LANDING ━━       Landing page styles and layout
// ━━ SHARED ━━        Shared CSS utilities
// ━━ PROFILER ━━      Career value assessment questionnaire
// ━━ SEARCH ━━        Company search and selection
// ━━ BENEFITS ━━      Benefits configuration and calculation
// ━━ WORK STYLE ━━    Work arrangement (overtime, remote, flex)
// ━━ PRIORITY ━━      Priority and sacrifice selection
// ━━ COMPARE ENGINE ━━ Core comparison and report generation
// ━━ INIT ━━          Application initialization
```

Structure within `index.html`:
1. `<head>` — Meta tags, CDN font links, `<style>` block with all CSS
2. `<body>` — HTML markup for all screens (landing, profiler, input, report)
3. `<script>` — All JavaScript at the bottom

## Naming Conventions

### Frontend
| Type | Convention | Examples |
|------|-----------|----------|
| Variables | camelCase (abbreviated) | `pfJob`, `wsState`, `curPri`, `benS` |
| Functions | camelCase | `doSearch()`, `compare()`, `calc()`, `renderBen()` |
| Constants | UPPER_SNAKE_CASE | `DIMS`, `OT_HRS`, `DB`, `PRIORITIES` |
| CSS classes | kebab-case (abbreviated) | `.pf-intro`, `.ws-btn`, `.vs-card` |
| DOM IDs | camelCase or short codes | `sA`, `sB`, `tA`, `tB`, `blA`, `blB` |

Side convention: `a` = current job (현직), `b` = new job offer (이직처).

### Backend
| Type | Convention | Examples |
|------|-----------|----------|
| Files/modules | snake_case | `auth_service.py`, `auth_middleware.py` |
| Classes | PascalCase | `RegisterReq`, `CompanyBrief`, `TokenResp` |
| Functions | snake_case | `init_pool()`, `fetch_all()`, `create_token()` |
| Config | UPPER_SNAKE_CASE | `DB_HOST`, `JWT_SECRET`, `JWT_EXPIRE_HOURS` |

## Key Frontend Functions

- `compare()` — Main report generation (~300 lines). Verdict cards, salary, hourly value, WLB, 3-year projection, bottom line.
- `calc()` — Real-time summary triggered on input change.
- `doSearch(s)` / `selComp(s, id)` — Company search/selection.
- `renderBen(s)` — Benefits list rendering.
- `setWS(s, key, val)` — Work style state update.
- `getWSHours(s)` / `getOTPay(s)` — Weekly hours and overtime pay calc.
- `go(screenId)` — SPA screen navigation.
- `apiFetch(path, opts)` — API client with JWT auth header.

## Key Backend Patterns

- **Stateless API** — No sessions, JWT-only auth.
- **Connection pool** — aiomysql async pool (2–10 connections, autocommit).
- **Raw SQL** — No ORM. `database.fetch_all()`, `fetch_one()`, `execute()`.
- **In-memory cache** — 1hr TTL for `/reference/all` (companies, benefits, profiles, questions).
- **Progressive enhancement** — Frontend works offline with hardcoded data, enhanced when API is available.

## Styling

- CSS custom properties (dark theme): `--bg-0` through `--bg-4`, `--t1` through `--t4`
- Color accents: `--blue`, `--amber`, `--green`, `--red`, `--purple`, `--gold` (each with `-d` dim variant)
- Responsive: `@media(max-width:480px)`
- Animations: `fadeUp`, `slideUp` with `cubic-bezier` easing

## Development Guidelines

- **Frontend**: All frontend code stays in `index.html`. Compact/minified style — match existing density.
- **Backend**: Follow existing module structure (`routers/`, `models/`, `services/`). Raw SQL, no ORM.
- **Korean UI text**: All user-facing strings are in Korean. Code in English.
- **Frontend state is global**: `wsState`, `benS`, `matched`, `curPri`, `curSacrifice`, `pfResult`, `AUTH_TOKEN`.
- **DOM updates via innerHTML**: Build HTML strings, assign to `innerHTML`. Inline `onclick` handlers.
- **Side pattern**: Functions take `s` parameter (`'a'` or `'b'`). DOM IDs: `sA`/`sB`, `tA`/`tB`.
- **No test framework**: Verify manually in browser / API client.
- **Bug fix comments**: Annotated with `// [FIX]`.

## Database Conventions

- **No ENUM** — 모든 컬럼은 `VARCHAR`로 선언. 허용 값은 `COMMENT`에 명시. ENUM은 스키마 변경 시 ALTER TABLE 필요하므로 사용 금지.
- **모든 컬럼에 COMMENT 필수** — 한국어로 컬럼 용도, 단위, 허용 값 범위를 기재. 예: `COMMENT '기업유형 (large, startup, mid, foreign, public, freelance)'`
- **FK 참조 대상은 COMMENT에 명시** — 예: `COMMENT '사용자 FK (users.id)'`
- **금액 단위는 만원** — 별도 표기 없으면 만원 기준. COMMENT에 `(만원)` 명시.

## Common Pitfalls

- Variable shadowing in `compare()` (~300 lines with many locals)
- `compare()` validates inputs at top — new comparison logic needs null/undefined checks
- Benefits use both `val` (numeric) and `checked` (boolean) — check both when summing
- Overtime pay differs between `'inclusive'` (포괄임금) and `'separate'` (비포괄) wage types
- Company type (`large`, `startup`, `mid`, `foreign`, `public`, `freelance`) affects stability scores, growth rates, benefit presets
- Backend SQL uses `%s` placeholders (aiomysql) — never use f-strings for queries
- JWT token stored in `localStorage` as `jc_token` — frontend reads on init

## Agent Team

프로젝트 전용 에이전트 팀 (`.claude/skills/`). 각 스킬은 `/명령어`로 호출합니다.

| 스킬 | 역할 | 호출 예시 |
|------|------|----------|
| `/team-status` | 프로젝트 현황 + 다음 작업 추천 | `/team-status` |
| `/fe` | 프론트엔드 (index.html) 개발 | `/fe OT 계산 UI 구현` |
| `/be` | 백엔드 (FastAPI) + DB (MySQL) | `/be 비밀번호 재설정 API` |
| `/test` | 테스트 작성 + 실행 | `/test auth` |
| `/audit` | 코드 리뷰 + 보안 점검 | `/audit` 또는 `/audit full` |
| `/batch-benefits` | 복지 데이터 배치 현황 | `/batch-benefits` |
| `/deploy` | 인프라 + 배포 관리 | `/deploy nginx 보안 헤더` |
| `/debug` | 체계적 디버깅 (4단계 프로세스) | `/debug` |
| `/verify` | 완료 전 검증 게이트 | `/verify` |
| `/research-benefits` | 회사 복지 웹 조사 → DB | `/research-benefits 카카오` |
| `/parse-benefits` | 복지 텍스트 → SQL 변환 | `/parse-benefits SK하이닉스` |

### 권장 워크플로우

```
기능 개발: /be {API} → /fe {UI} → /verify → /test → /audit
버그 수정: /debug → 수정 → /verify → /audit
데이터 수집: /batch-benefits → /parse-benefits 또는 /research-benefits (반복)
배포 전: /test → /audit full → /verify → /deploy
```

CLAUDE.md의 Agent Team 테이블은 사용자 안내용입니다. 실제 구현은:
- **Agents** (`.claude/agents/*.md`): `fe`, `be`, `test`, `audit`, `team-status`, `deploy` — 자율 실행, 독립 컨텍스트
- **Skills** (`.claude/skills/*/SKILL.md`): `debug`, `verify`, `batch-benefits`, `research-benefits`, `parse-benefits` — 사용자 확인 필요

### Hooks (자동 협업)

- **SessionStart**: 세션 시작 시 `<project-status>` 태그로 프로젝트 상태 자동 주입 (브랜치, 최근 커밋, 복지 데이터 진행률)
- **PostToolUse(Edit|Write)**: 파일 수정 후 `<next-step>` 태그로 다음 단계 자동 제안

Hooks가 `<next-step>` 태그를 주입하면, 해당 제안을 사용자에게 안내한다.
