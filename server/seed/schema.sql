-- Job Choice OS — MySQL Schema
-- UTF-8 Korean support
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- ━━ REFERENCE DATA ━━

CREATE TABLE IF NOT EXISTS company_types (
  id VARCHAR(20) PRIMARY KEY,
  label VARCHAR(20) NOT NULL,
  growth_rate DECIMAL(5,4) NOT NULL,
  growth_label VARCHAR(50) NOT NULL,
  stability_score TINYINT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS companies (
  id VARCHAR(30) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  type_id VARCHAR(20) NOT NULL,
  industry VARCHAR(50),
  logo VARCHAR(10),
  work_style JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (type_id) REFERENCES company_types(id),
  FULLTEXT INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS company_aliases (
  id INT AUTO_INCREMENT PRIMARY KEY,
  company_id VARCHAR(30) NOT NULL,
  alias VARCHAR(100) NOT NULL,
  FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
  INDEX idx_alias (alias)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS company_benefits (
  id INT AUTO_INCREMENT PRIMARY KEY,
  company_id VARCHAR(30) NOT NULL,
  ben_key VARCHAR(30) NOT NULL,
  name VARCHAR(100) NOT NULL,
  val INT DEFAULT 0,
  category VARCHAR(20) NOT NULL,
  badge VARCHAR(10) DEFAULT 'est',
  note VARCHAR(200),
  is_qualitative BOOLEAN DEFAULT FALSE,
  qual_text VARCHAR(500),
  sort_order SMALLINT DEFAULT 0,
  FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS benefit_presets (
  id INT AUTO_INCREMENT PRIMARY KEY,
  type_id VARCHAR(20) NOT NULL,
  ben_key VARCHAR(30) NOT NULL,
  name VARCHAR(100) NOT NULL,
  val INT DEFAULT 0,
  category VARCHAR(20) NOT NULL,
  badge VARCHAR(10) DEFAULT 'est',
  checked_default BOOLEAN DEFAULT TRUE,
  sort_order SMALLINT DEFAULT 0,
  FOREIGN KEY (type_id) REFERENCES company_types(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ━━ PROFILER DATA ━━

CREATE TABLE IF NOT EXISTS profiles (
  id VARCHAR(20) PRIMARY KEY,
  type_name VARCHAR(20) NOT NULL,
  description TEXT NOT NULL,
  map_priority VARCHAR(20) NOT NULL,
  vec JSON NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS profile_job_fits (
  id INT AUTO_INCREMENT PRIMARY KEY,
  profile_id VARCHAR(20) NOT NULL,
  scenario VARCHAR(20) NOT NULL,
  fit TEXT NOT NULL,
  caution TEXT NOT NULL,
  FOREIGN KEY (profile_id) REFERENCES profiles(id),
  UNIQUE INDEX idx_profile_scenario (profile_id, scenario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS job_groups (
  id INT AUTO_INCREMENT PRIMARY KEY,
  group_label VARCHAR(30) NOT NULL,
  color VARCHAR(10) NOT NULL,
  sort_order TINYINT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS jobs (
  id VARCHAR(30) PRIMARY KEY,
  group_id INT NOT NULL,
  label VARCHAR(30) NOT NULL,
  icon VARCHAR(10) NOT NULL,
  scenario VARCHAR(20) NOT NULL,
  sort_order TINYINT NOT NULL,
  FOREIGN KEY (group_id) REFERENCES job_groups(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS profiler_questions (
  id INT PRIMARY KEY,
  label VARCHAR(30) NOT NULL,
  option_a_title VARCHAR(50) NOT NULL,
  option_a_fx JSON NOT NULL,
  option_b_title VARCHAR(50) NOT NULL,
  option_b_fx JSON NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS question_scenarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  question_id INT NOT NULL,
  scenario VARCHAR(20) NOT NULL,
  desc_a TEXT NOT NULL,
  desc_b TEXT NOT NULL,
  FOREIGN KEY (question_id) REFERENCES profiler_questions(id),
  UNIQUE INDEX idx_q_scenario (question_id, scenario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ━━ USER DATA ━━

CREATE TABLE IF NOT EXISTS users (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS profiler_results (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  job_id VARCHAR(30),
  scores JSON NOT NULL,
  profile_id VARCHAR(20) NOT NULL,
  similarity DECIMAL(5,4) NOT NULL,
  answers JSON NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (profile_id) REFERENCES profiles(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS comparisons (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  company_a_name VARCHAR(100),
  type_a VARCHAR(20) NOT NULL,
  salary_a_min INT,
  salary_a_max INT,
  commute_a INT DEFAULT 0,
  work_style_a JSON,
  benefits_a JSON,
  company_b_name VARCHAR(100),
  type_b VARCHAR(20) NOT NULL,
  salary_rate INT,
  commute_b INT DEFAULT 0,
  work_style_b JSON,
  benefits_b JSON,
  priority_key VARCHAR(20) NOT NULL,
  sacrifice_key VARCHAR(20),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
