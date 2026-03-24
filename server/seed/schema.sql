-- Job Choice OS — MySQL Schema
-- UTF-8 Korean support
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- ━━ REFERENCE DATA ━━

CREATE TABLE IF NOT EXISTS company_types (
  id VARCHAR(20) PRIMARY KEY COMMENT '기업유형 코드 (large, startup, mid, foreign, public, freelance)',
  label VARCHAR(20) NOT NULL COMMENT '표시 라벨 (대기업, 스타트업 등)',
  growth_rate DECIMAL(5,4) NOT NULL COMMENT '연평균 연봉 상승률 (0.0350 = 3.5%)',
  growth_label VARCHAR(50) NOT NULL COMMENT '성장률 설명 텍스트',
  stability_score TINYINT NOT NULL COMMENT '고용 안정성 점수 (1~10)'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS companies (
  id VARCHAR(30) PRIMARY KEY COMMENT '회사 고유 코드 (cj, toss 등)',
  name VARCHAR(100) NOT NULL COMMENT '회사 정식 명칭',
  type_id VARCHAR(20) NOT NULL COMMENT '기업유형 FK (company_types.id)',
  industry VARCHAR(50) COMMENT '산업 분류 (식품/유통, 핀테크 등)',
  logo VARCHAR(10) COMMENT '로고 약어 (CJ, T 등)',
  work_style JSON COMMENT '근무 형태 {remote, flex, unlimitedPTO, refreshLeave, overtime}',
  careers_benefit_url VARCHAR(500) COMMENT '채용 홈페이지 복지 페이지 URL',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '레코드 생성 시각',
  FOREIGN KEY (type_id) REFERENCES company_types(id),
  FULLTEXT INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS company_aliases (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '별칭 PK',
  company_id VARCHAR(30) NOT NULL COMMENT '회사 FK (companies.id)',
  alias VARCHAR(100) NOT NULL COMMENT '검색용 별칭 (CJ, 씨제이, cj 등)',
  FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
  INDEX idx_alias (alias)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS company_benefits (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '복지항목 PK',
  company_id VARCHAR(30) NOT NULL COMMENT '회사 FK (companies.id)',
  ben_key VARCHAR(30) NOT NULL COMMENT '복지 코드 (meal, fitness, housing 등)',
  name VARCHAR(100) NOT NULL COMMENT '복지 표시명 (식대, 헬스장 등)',
  val INT DEFAULT 0 COMMENT '연간 환산 금액 (만원)',
  category VARCHAR(20) NOT NULL COMMENT '복지 카테고리 (financial, work_env, wellness, time, growth, family, life)',
  badge VARCHAR(10) DEFAULT 'est' COMMENT '데이터 신뢰도 (est: 추정, official: 공식)',
  note VARCHAR(200) COMMENT '복지 상세 설명',
  is_qualitative BOOLEAN DEFAULT FALSE COMMENT '정성적 복지 여부 (TRUE: 금액 환산 불가)',
  qual_text VARCHAR(500) COMMENT '정성적 복지 상세 텍스트',
  sort_order SMALLINT DEFAULT 0 COMMENT '표시 정렬 순서',
  FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS benefit_presets (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '프리셋 PK',
  type_id VARCHAR(20) NOT NULL COMMENT '기업유형 FK (company_types.id)',
  ben_key VARCHAR(30) NOT NULL COMMENT '복지 코드',
  name VARCHAR(100) NOT NULL COMMENT '복지 표시명',
  val INT DEFAULT 0 COMMENT '연간 환산 금액 (만원)',
  category VARCHAR(20) NOT NULL COMMENT '복지 카테고리 (financial, work_env, wellness, time, growth, family, life)',
  badge VARCHAR(10) DEFAULT 'est' COMMENT '데이터 신뢰도 (est, official)',
  checked_default BOOLEAN DEFAULT TRUE COMMENT '기본 체크 상태',
  sort_order SMALLINT DEFAULT 0 COMMENT '표시 정렬 순서',
  FOREIGN KEY (type_id) REFERENCES company_types(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ━━ PROFILER DATA ━━

CREATE TABLE IF NOT EXISTS profiles (
  id VARCHAR(20) PRIMARY KEY COMMENT '프로필 코드 (balanced, growth_seeker 등)',
  type_name VARCHAR(20) NOT NULL COMMENT '프로필 유형명 (균형파, 성장파 등)',
  description TEXT NOT NULL COMMENT '프로필 상세 설명',
  map_priority VARCHAR(20) NOT NULL COMMENT '매핑 우선순위 키 (salary, wlb, benefits, brand)',
  vec JSON NOT NULL COMMENT '6차원 벡터 {compensation, security, growth, autonomy, impact, flexibility}'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS profile_job_fits (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '직무적합도 PK',
  profile_id VARCHAR(20) NOT NULL COMMENT '프로필 FK (profiles.id)',
  scenario VARCHAR(20) NOT NULL COMMENT '시나리오 코드 (tech, design, pm, biz 등)',
  fit TEXT NOT NULL COMMENT '적합한 점 설명',
  caution TEXT NOT NULL COMMENT '주의할 점 설명',
  FOREIGN KEY (profile_id) REFERENCES profiles(id),
  UNIQUE INDEX idx_profile_scenario (profile_id, scenario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS job_groups (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '직군 그룹 PK',
  group_label VARCHAR(30) NOT NULL COMMENT '그룹 표시명 (개발, 디자인, 기획 등)',
  color VARCHAR(10) NOT NULL COMMENT 'UI 색상 코드 (#4A9B8E 등)',
  sort_order TINYINT NOT NULL COMMENT '표시 정렬 순서'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS jobs (
  id VARCHAR(30) PRIMARY KEY COMMENT '직무 코드 (fe_dev, pm 등)',
  group_id INT NOT NULL COMMENT '직군 그룹 FK (job_groups.id)',
  label VARCHAR(30) NOT NULL COMMENT '직무 표시명 (프론트엔드, PM 등)',
  icon VARCHAR(10) NOT NULL COMMENT '직무 아이콘 이모지',
  scenario VARCHAR(20) NOT NULL COMMENT '시나리오 코드 (tech, design, pm, biz)',
  sort_order TINYINT NOT NULL COMMENT '표시 정렬 순서',
  FOREIGN KEY (group_id) REFERENCES job_groups(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS profiler_questions (
  id INT PRIMARY KEY COMMENT '질문 번호',
  label VARCHAR(30) NOT NULL COMMENT '질문 짧은 라벨',
  option_a_title VARCHAR(50) NOT NULL COMMENT '선택지 A 제목',
  option_a_fx JSON NOT NULL COMMENT '선택지 A 점수 효과 {dim: delta}',
  option_b_title VARCHAR(50) NOT NULL COMMENT '선택지 B 제목',
  option_b_fx JSON NOT NULL COMMENT '선택지 B 점수 효과 {dim: delta}'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS question_scenarios (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '시나리오별 질문 PK',
  question_id INT NOT NULL COMMENT '질문 FK (profiler_questions.id)',
  scenario VARCHAR(20) NOT NULL COMMENT '시나리오 코드 (tech, design, pm, biz)',
  desc_a TEXT NOT NULL COMMENT '선택지 A 시나리오별 상세 설명',
  desc_b TEXT NOT NULL COMMENT '선택지 B 시나리오별 상세 설명',
  FOREIGN KEY (question_id) REFERENCES profiler_questions(id),
  UNIQUE INDEX idx_q_scenario (question_id, scenario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ━━ USER DATA ━━

CREATE TABLE IF NOT EXISTS users (
  id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '사용자 PK',
  email VARCHAR(255) UNIQUE NOT NULL COMMENT '이메일 (로그인 ID)',
  password_hash VARCHAR(255) NOT NULL COMMENT 'bcrypt 해시된 비밀번호',
  name VARCHAR(50) COMMENT '사용자 표시 이름',
  job_id VARCHAR(30) COMMENT '선택한 직군 코드 (dev, pm, uxui 등)',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '가입 시각',
  INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS profiler_results (
  id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '프로파일러 결과 PK',
  user_id BIGINT NOT NULL COMMENT '사용자 FK (users.id)',
  job_id VARCHAR(30) COMMENT '선택한 직무 FK (jobs.id)',
  scores JSON NOT NULL COMMENT '6차원 점수 {compensation, security, growth, autonomy, impact, flexibility}',
  profile_id VARCHAR(20) NOT NULL COMMENT '매칭된 프로필 FK (profiles.id)',
  similarity DECIMAL(5,4) NOT NULL COMMENT '프로필 유사도 (0.0000~1.0000)',
  answers JSON NOT NULL COMMENT '사용자 답변 배열 [{q, choice}]',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '결과 생성 시각',
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (profile_id) REFERENCES profiles(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS comparisons (
  id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '비교 PK',
  user_id BIGINT NOT NULL COMMENT '사용자 FK (users.id)',
  company_a_name VARCHAR(100) COMMENT 'A측(현직) 회사명',
  type_a VARCHAR(20) NOT NULL COMMENT 'A측 기업유형 (large, startup, mid, foreign, public, freelance)',
  salary_a_min INT COMMENT 'A측 연봉 하한 (만원)',
  salary_a_max INT COMMENT 'A측 연봉 상한 (만원)',
  commute_a INT DEFAULT 0 COMMENT 'A측 편도 통근 시간 (분)',
  work_style_a JSON COMMENT 'A측 근무 형태 {ot, wage, remote, flex}',
  benefits_a JSON COMMENT 'A측 복리후생 배열 [{ben_key, name, val, cat, checked}]',
  company_b_name VARCHAR(100) COMMENT 'B측(이직처) 회사명',
  type_b VARCHAR(20) NOT NULL COMMENT 'B측 기업유형 (large, startup, mid, foreign, public, freelance)',
  salary_rate INT COMMENT '연봉 인상률 (%)',
  commute_b INT DEFAULT 0 COMMENT 'B측 편도 통근 시간 (분)',
  work_style_b JSON COMMENT 'B측 근무 형태 {ot, wage, remote, flex}',
  benefits_b JSON COMMENT 'B측 복리후생 배열',
  priority_key VARCHAR(20) NOT NULL COMMENT '최우선 기준 (salary, wlb, benefits, brand)',
  sacrifice_key VARCHAR(20) COMMENT '포기 가능 기준 (salary, wlb, benefits, brand)',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '비교 생성 시각',
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ━━ LANDING FEED DATA ━━

CREATE TABLE IF NOT EXISTS comparison_feed (
  id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '피드 PK',
  comparison_id BIGINT NOT NULL COMMENT '비교 FK (comparisons.id)',
  job_category VARCHAR(30) COMMENT '직무 카테고리 (개발자, PM, 디자이너 등)',
  company_a_display VARCHAR(100) COMMENT 'A측 표시용 회사명',
  type_a VARCHAR(20) NOT NULL COMMENT 'A측 기업유형 (large, startup, mid, foreign, public, freelance)',
  company_b_display VARCHAR(100) COMMENT 'B측 표시용 회사명',
  type_b VARCHAR(20) NOT NULL COMMENT 'B측 기업유형 (large, startup, mid, foreign, public, freelance)',
  headline VARCHAR(300) NOT NULL COMMENT '비교 결과 한줄 요약',
  detail VARCHAR(500) COMMENT '부가 설명 텍스트',
  metric_val VARCHAR(30) COMMENT '핵심 수치 (+18.4%, +1,240만 등)',
  metric_label VARCHAR(30) COMMENT '수치 라벨 (시간당 가치, 3년 복지 누적 등)',
  metric_type VARCHAR(10) DEFAULT 'neu' COMMENT '수치 방향 (up, down, neu)',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '피드 생성 시각',
  FOREIGN KEY (comparison_id) REFERENCES comparisons(id) ON DELETE CASCADE,
  INDEX idx_feed_created (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS daily_stats (
  stat_date DATE PRIMARY KEY COMMENT '통계 날짜',
  comparison_count INT DEFAULT 0 COMMENT '해당일 비교 실행 횟수'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS popular_cases (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '인기 사례 PK',
  case_type VARCHAR(20) NOT NULL COMMENT '사례 유형 (company, scenario)',
  title_a VARCHAR(50) NOT NULL COMMENT 'A측 제목 (회사명 또는 현직 유지)',
  type_a VARCHAR(20) NOT NULL COMMENT 'A측 기업유형 (large, startup, mid, foreign, public, freelance)',
  sub_a VARCHAR(30) COMMENT 'A측 부제 (대기업, 안정성 등)',
  title_b VARCHAR(50) NOT NULL COMMENT 'B측 제목',
  type_b VARCHAR(20) NOT NULL COMMENT 'B측 기업유형',
  sub_b VARCHAR(30) COMMENT 'B측 부제',
  points JSON COMMENT '비교 포인트 배열 ["포인트1", "포인트2", "포인트3"]',
  view_count INT DEFAULT 0 COMMENT '조회 수',
  comparison_count INT DEFAULT 0 COMMENT '비교 실행 수',
  is_active BOOLEAN DEFAULT TRUE COMMENT '활성 상태 (TRUE: 노출, FALSE: 숨김)',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '사례 생성 시각',
  INDEX idx_active_count (is_active, comparison_count DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
