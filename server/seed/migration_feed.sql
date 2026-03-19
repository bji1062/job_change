-- Migration: Landing page social feed tables
SET NAMES utf8mb4;

-- 1) comparison_feed — 비교 결과 피드
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

-- 2) daily_stats — 일별 통계
CREATE TABLE IF NOT EXISTS daily_stats (
  stat_date DATE PRIMARY KEY COMMENT '통계 날짜',
  comparison_count INT DEFAULT 0 COMMENT '해당일 비교 실행 횟수'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3) popular_cases — 인기 비교 사례
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

-- 4) 초기 시드 데이터
INSERT INTO popular_cases (case_type, title_a, type_a, sub_a, title_b, type_b, sub_b, points, view_count, comparison_count) VALUES
('company', '쿠팡', 'large', '대기업', '네이버', 'large', '대기업',
 '["<strong>연봉</strong>은 쿠팡이 높지만 포괄임금 + 야근 많음으로 시간당 가치는 역전될 수 있음","<strong>워라밸</strong>은 네이버가 우세 · 재택·유연근무 실사용률 높음","<strong>3년 성장</strong>은 비슷한 수준 — 직무에 따라 갈림"]', 12341, 847),
('company', '카카오', 'large', '대기업', '삼성전자', 'large', '대기업',
 '["<strong>IT 플랫폼</strong> vs 제조 대기업 — 문화 차이 큼","<strong>자율 문화</strong> vs 체계적 구조 · 성향에 따라 선택","<strong>복지</strong> 패키지는 삼성이 종합적으로 우세"]', 9823, 623),
('scenario', '현직 유지', 'large', '안정성', '이직처', 'startup', '성장성',
 '["현재 <strong>연봉 대비 인상률</strong> 비교","<strong>워라밸</strong> 변화 예측","<strong>커리어 성장</strong> 기대치 분석"]', 8456, 512),
('company', '토스', 'startup', '핀테크', '카카오뱅크', 'large', '인터넷은행',
 '["<strong>성장성</strong>은 토스가 빠르지만 리스크도 큼","<strong>안정성</strong>은 카카오뱅크(은행 라이선스)가 우세","<strong>보상 구조</strong> 스톡옵션 vs 안정 연봉 차이"]', 5432, 298),
('scenario', '현직', 'mid', '중견기업', '이직처', 'foreign', '외국계',
 '["<strong>연봉 점프</strong> 가능성 높음 · 30%+ 인상 사례 다수","<strong>문화 적응</strong> 비용 고려 필요","<strong>장기 커리어</strong> 관점에서 비교"]', 4567, 267);
