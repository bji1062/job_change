-- Migration: Landing page social feed tables
SET NAMES utf8mb4;

-- 1) comparison_feed — 비교 결과 피드
CREATE TABLE IF NOT EXISTS comparison_feed (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  comparison_id BIGINT NOT NULL,
  job_category VARCHAR(30),
  company_a_display VARCHAR(100),
  type_a VARCHAR(20) NOT NULL,
  company_b_display VARCHAR(100),
  type_b VARCHAR(20) NOT NULL,
  headline VARCHAR(300) NOT NULL,
  detail VARCHAR(500),
  metric_val VARCHAR(30),
  metric_label VARCHAR(30),
  metric_type ENUM('up','down','neu') DEFAULT 'neu',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (comparison_id) REFERENCES comparisons(id) ON DELETE CASCADE,
  INDEX idx_feed_created (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2) daily_stats — 일별 통계
CREATE TABLE IF NOT EXISTS daily_stats (
  stat_date DATE PRIMARY KEY,
  comparison_count INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3) popular_cases — 인기 비교 사례
CREATE TABLE IF NOT EXISTS popular_cases (
  id INT AUTO_INCREMENT PRIMARY KEY,
  case_type ENUM('company','scenario') NOT NULL,
  title_a VARCHAR(50) NOT NULL,
  type_a VARCHAR(20) NOT NULL,
  sub_a VARCHAR(30),
  title_b VARCHAR(50) NOT NULL,
  type_b VARCHAR(20) NOT NULL,
  sub_b VARCHAR(30),
  points JSON,
  view_count INT DEFAULT 0,
  comparison_count INT DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_active_count (is_active, comparison_count DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4) 초기 시드 데이터
INSERT INTO popular_cases (case_type, title_a, type_a, sub_a, title_b, type_b, sub_b, points) VALUES
('company', '쿠팡', 'large', '대기업', '네이버', 'large', '대기업',
 '["연봉 vs 복지 밸런스", "물류 vs IT 플랫폼", "성장 속도 비교"]'),
('company', '카카오', 'large', '대기업', '삼성전자', 'large', '대기업',
 '["IT 플랫폼 vs 제조 대기업", "자율 문화 vs 체계적 구조", "복지 패키지 비교"]'),
('scenario', '현직 유지', 'large', '안정성', '이직처', 'startup', '성장성',
 '["현재 연봉 대비 인상률", "워라밸 변화 예측", "커리어 성장 기대치"]');
