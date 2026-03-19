-- Job Choice OS — Seed Data
-- Usage: mysql -u root jobchoice < seed.sql
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- ━━ 1. COMPANY TYPES ━━
INSERT IGNORE INTO company_types (id, label, growth_rate, growth_label, stability_score) VALUES
('large', '대기업', 0.04, '대기업 평균 4%', 90),
('mid', '중견기업', 0.027, '중견기업 평균 2.7%', 70),
('public', '공기업', 0.03, '공기업 평균 3%', 95),
('startup', '스타트업', 0.10, '스타트업 평균 10%', 30),
('foreign', '외국계', 0.05, '외국계 평균 5%', 60),
('freelance', '프리랜서', 0.02, '프리랜서 평균 2%', 20);

-- ━━ 2. BENEFIT PRESETS ━━
INSERT INTO benefit_presets (type_id, ben_key, name, val, category, badge, checked_default, sort_order) VALUES
('large', 'meal', '식대 지원', 180, 'money', 'est', TRUE, 0),
('large', 'transport', '교통비/주차비', 120, 'money', 'est', TRUE, 1),
('large', 'welfare', '복지포인트/선택복지', 200, 'money', 'est', TRUE, 2),
('large', 'bonus', '성과급/인센티브', 300, 'money', 'est', FALSE, 3),
('large', 'health', '건강검진 (본인+가족)', 100, 'health', 'est', TRUE, 4),
('large', 'housing', '사내대출 이자절감', 200, 'housing', 'est', TRUE, 5),
('large', 'child_edu', '자녀 학자금', 300, 'family', 'est', FALSE, 6),
('large', 'event', '경조사 지원', 50, 'money', 'est', TRUE, 7),
('mid', 'meal', '식대 지원', 150, 'money', 'est', TRUE, 0),
('mid', 'transport', '교통비', 60, 'money', 'est', TRUE, 1),
('mid', 'health', '건강검진', 50, 'health', 'est', TRUE, 2),
('mid', 'event', '경조사 지원', 30, 'money', 'est', TRUE, 3),
('public', 'meal', '식대 지원', 180, 'money', 'est', TRUE, 0),
('public', 'transport', '교통비', 120, 'money', 'est', TRUE, 1),
('public', 'welfare', '복지포인트/선택복지', 250, 'money', 'est', TRUE, 2),
('public', 'health', '건강검진', 80, 'health', 'est', TRUE, 3),
('public', 'housing', '사내대출 이자절감', 250, 'housing', 'est', TRUE, 4),
('public', 'child_edu', '자녀 학자금', 400, 'family', 'est', FALSE, 5),
('public', 'edu', '교육비/자기개발비', 100, 'edu', 'est', TRUE, 6),
('public', 'event', '경조사 지원', 50, 'money', 'est', TRUE, 7),
('startup', 'meal', '식대 지원', 180, 'money', 'est', TRUE, 0),
('startup', 'stock', '스톡옵션/RSU 기대값', 500, 'money', 'est', FALSE, 1),
('foreign', 'meal', '식대 지원', 180, 'money', 'est', TRUE, 0),
('foreign', 'transport', '교통비', 100, 'money', 'est', TRUE, 1),
('foreign', 'welfare', '복지포인트', 150, 'money', 'est', TRUE, 2),
('foreign', 'bonus', '성과급/인센티브', 500, 'money', 'est', FALSE, 3),
('foreign', 'health', '건강검진', 150, 'health', 'est', TRUE, 4),
('foreign', 'edu', '교육비 (도서, 세미나)', 200, 'edu', 'est', TRUE, 5);

-- ━━ 3. COMPANIES ━━
INSERT IGNORE INTO companies (id, name, type_id, industry, logo, work_style) VALUES
('cj', 'CJ그룹', 'large', '식품/유통/엔터', 'CJ', '{"remote": false, "flex": false, "unlimitedPTO": false, "refreshLeave": "3·5·7·10년 근속 시 2주 유급", "overtime": "일반적 대기업 수준"}'),
('toss', '토스 (비바리퍼블리카)', 'startup', '핀테크', 'T', '{"remote": true, "flex": true, "unlimitedPTO": true, "refreshLeave": "3년마다 1개월 유급", "overtime": "자율 (성과 중심)"}');

-- ━━ 4. COMPANY ALIASES ━━
INSERT INTO company_aliases (company_id, alias) VALUES
('cj', 'CJ'), ('cj', 'cj'), ('cj', '씨제이'), ('cj', 'CJ제일제당'), ('cj', 'CJ올리브영'), ('cj', 'CJ ENM'),
('toss', '토스'), ('toss', 'toss'), ('toss', 'Toss'), ('toss', '비바리퍼블리카'), ('toss', '비바');

-- ━━ 5. COMPANY BENEFITS ━━
INSERT INTO company_benefits (company_id, ben_key, name, val, category, badge, note, is_qualitative, qual_text, sort_order) VALUES
('cj', 'meal', '구내식당 (아침·점심·저녁 100%)', 432, 'money', 'auto', '일 18,000원 × 240일', FALSE, NULL, 0),
('cj', 'cafe_point', '카페테리아 포인트', 200, 'money', 'auto', NULL, FALSE, NULL, 1),
('cj', 'commute_sup', '출퇴근 셔틀 + 야근택시', 120, 'money', 'est', NULL, FALSE, NULL, 2),
('cj', 'event', '경조사 지원', 50, 'money', 'est', NULL, FALSE, NULL, 3),
('cj', 'health', '건강검진 (본인+가족)', 100, 'health', 'auto', NULL, FALSE, NULL, 4),
('cj', 'medical', '의료비 지원', 100, 'health', 'est', NULL, FALSE, NULL, 5),
('cj', 'fitness', '피트니스 지원', 60, 'health', 'est', NULL, FALSE, NULL, 6),
('cj', 'housing', '주택대부 이자절감', 200, 'housing', 'est', NULL, FALSE, NULL, 7),
('cj', 'resort', '프리미엄 숙소 할인', 50, 'housing', 'est', NULL, FALSE, NULL, 8),
('cj', 'lang', '어학시험 응시료', 15, 'edu', 'auto', NULL, FALSE, NULL, 9),
('cj', 'child_edu', '자녀 학자금', 300, 'family', 'auto', '초·중·고·대학', FALSE, NULL, 10),
('cj', 'parenting', '임신·출산·육아 지원', 0, 'family', 'auto', NULL, TRUE, '키즈빌 운영, 배우자 출산휴가, 최대 2년 육아휴직', 11),
('cj', 'wedding', '결혼 혜택', 0, 'family', 'auto', NULL, TRUE, '웨딩카 제공, 사내 인재원 웨딩홀 대관', 12),
('cj', 'discount', '계열사 40% 할인', 100, 'life', 'est', '올리브영, CGV 등', FALSE, NULL, 13),
('cj', 'tving', '티빙 이용권', 17, 'life', 'auto', NULL, FALSE, NULL, 14),
('cj', 'travel', '여행 지원', 80, 'life', 'est', NULL, FALSE, NULL, 15),
('cj', 'club', '사내 동호회', 30, 'life', 'est', NULL, FALSE, NULL, 16),
('cj', 'creative_leave', '창의휴가 (근속 시 2주 유급)', 0, 'leave', 'auto', NULL, TRUE, '3·5·7·10년 근속 시 2주간 유급 휴가', 17),
('toss', 'meal', '법인카드 식사 (점심+저녁 100%)', 432, 'money', 'auto', '일 18,000원 × 240일', FALSE, NULL, 0),
('toss', 'fitness_comm', '체력단련비+통신비 (매월)', 120, 'money', 'auto', NULL, FALSE, NULL, 1),
('toss', 'insurance', '직장 단체보험 (가족 포함)', 150, 'health', 'auto', NULL, FALSE, NULL, 2),
('toss', 'salon', '사내 헤어살롱', 30, 'health', 'est', NULL, FALSE, NULL, 3),
('toss', 'cafe', '사내 카페 무료', 60, 'health', 'est', NULL, FALSE, NULL, 4),
('toss', 'housing', '주택자금 무이자 1억', 350, 'housing', 'auto', '시중 3.5% 기준 이자절감', FALSE, NULL, 5),
('toss', 'edu', '업무 교육비 100%', 100, 'edu', 'auto', '도서, 세미나 무제한', FALSE, NULL, 6),
('toss', 'hardware', '최고급 장비 제공', 100, 'edu', 'est', NULL, FALSE, NULL, 7),
('toss', 'flex', '유연 출퇴근+원격근무', 0, 'leave', 'auto', NULL, TRUE, '유연한 출퇴근 시간, 원격 근무 가능', 8),
('toss', 'unlimited_pto', '자율 휴가 (승인 불필요)', 0, 'leave', 'auto', NULL, TRUE, '별도 승인 없는 자율 휴가', 9),
('toss', 'refresh', '리프레시 휴가 (3년마다 1개월)', 0, 'leave', 'auto', NULL, TRUE, '근속 3년마다 1개월 유급 휴가', 10);

-- ━━ 6. PROFILES ━━
INSERT IGNORE INTO profiles (id, type_name, description, map_priority, vec) VALUES
('explorer', '탐험가형', '돈과 안정성을 기꺼이 포기하더라도 배움과 자유를 택합니다.', 'growth', '{"compensation": -0.3, "security": -0.6, "growth": 0.9, "autonomy": 0.8, "impact": 0, "flexibility": 0.4}'),
('architect', '건축가형', '전문적 깊이와 조직적 영향력을 동시에 추구합니다.', 'growth', '{"compensation": 0, "security": -0.1, "growth": 0.8, "autonomy": 0.2, "impact": 0.8, "flexibility": 0}'),
('fortress', '요새형', '예측 가능한 보상과 안정성을 최우선으로 합니다.', 'stability', '{"compensation": 0.7, "security": 0.9, "growth": -0.3, "autonomy": -0.3, "impact": 0, "flexibility": -0.5}'),
('conqueror', '정복자형', '높은 보상과 강한 영향력을 함께 추구합니다.', 'salary', '{"compensation": 0.9, "security": -0.2, "growth": 0.1, "autonomy": 0, "impact": 0.8, "flexibility": -0.2}'),
('nomad', '유목민형', '어떤 것에도 묶이지 않는 것을 최고의 가치로 봅니다.', 'wlb', '{"compensation": -0.4, "security": -0.5, "growth": 0.2, "autonomy": 0.8, "impact": -0.3, "flexibility": 0.9}'),
('gardener', '정원사형', '안전한 환경 안에서 꾸준히 성장하는 것을 선호합니다.', 'benefits', '{"compensation": 0.1, "security": 0.7, "growth": 0.7, "autonomy": -0.1, "impact": 0, "flexibility": -0.2}'),
('sovereign', '주권자형', '자기 방식대로 일하면서 의미 있는 결정을 내리고 싶어합니다.', 'wlb', '{"compensation": 0.2, "security": -0.3, "growth": 0.1, "autonomy": 0.9, "impact": 0.5, "flexibility": 0.3}'),
('strategist', '전략가형', '어떤 한 축에 올인하지 않고 최적의 포지션을 계산합니다.', 'growth', '{"compensation": 0.5, "security": 0.2, "growth": 0.3, "autonomy": 0, "impact": 0.6, "flexibility": 0.5}');

-- ━━ 7. PROFILE JOB FITS ━━
INSERT IGNORE INTO profile_job_fits (profile_id, scenario, fit, caution) VALUES
-- explorer
('explorer', 'tech', '스타트업 초기 멤버, 프리랜서 개발자', '안정성을 경시하면 생애 주기 변화에서 급격한 스트레스를 받을 수 있습니다.'),
('explorer', 'planning', '신규 서비스 0→1 기획, 스타트업 첫 PM', '탐험을 위한 이직이 잦으면 런칭→성장까지의 결과물을 증명하기 어렵습니다.'),
('explorer', 'marketing', '그로스 마케팅 초기 셋업, 스타트업 마케팅 1호', '너무 자주 이동하면 캠페인 성과를 끝까지 증명하기 어렵습니다.'),
('explorer', 'sales', '신규 시장 개척 영업, 스타트업 첫 세일즈', '고객 관계는 시간이 걸립니다. 너무 빨리 떠나면 네트워크가 쌓이지 않습니다.'),
('explorer', 'design', '브랜딩 에이전시, 프리랜서 디자이너', '포트폴리오 다양성은 좋지만, 깊이 있는 프로젝트 하나가 더 강력합니다.'),
('explorer', 'corporate', '스타트업 경영지원 1호, 신규 법인 셋업', '경영지원은 신뢰와 안정이 핵심입니다. 잦은 이동은 신뢰를 쌓기 어렵게 만듭니다.'),
-- architect
('architect', 'tech', '기술 리드, CTO, 플랫폼 아키텍트', '기술과 경영 두 축을 동시에 추구하면 중간에 빠질 위험이 있습니다.'),
('architect', 'planning', 'CPO, 프로덕트 전략가, 서비스 아키텍트', '기획 깊이와 조직 영향력 사이에서 시기별로 비중을 조절해야 합니다.'),
('architect', 'marketing', 'CMO, 브랜드 전략가, 마케팅 디렉터', '전략과 실행을 동시에 잡으려면 위임 능력이 핵심입니다.'),
('architect', 'sales', '영업 디렉터, 전략 파트너십, 사업개발 리더', '영업 현장과 전략 사이에서 균형을 잃으면 둘 다 약해집니다.'),
('architect', 'design', 'CDO, 디자인 시스템 리드, UX 디렉터', '디자인 실무에서 멀어지면 팀의 신뢰를 잃을 수 있습니다.'),
('architect', 'corporate', 'CFO, CHRO, 경영전략 임원', '실무 감각을 잃으면 현장과 괴리된 의사결정을 하게 됩니다.'),
-- fortress
('fortress', 'tech', '대기업 전문가 트랙, 공공기관 IT, 금융권 개발', '안정성에 과도하게 최적화하면 기술 트렌드 변화에 적응력이 약해집니다.'),
('fortress', 'planning', '대기업 서비스기획, 공공 SI 기획, 금융권 PM', '안정적 환경에서 혁신적 기획 역량이 정체될 수 있습니다.'),
('fortress', 'marketing', '대기업 브랜드 마케팅, 공기업 홍보', '안정적이지만 퍼포먼스 마케팅 역량이 약해질 수 있습니다.'),
('fortress', 'sales', '대기업 기존 고객 관리, 공공 입찰 영업', '신규 개척 역량이 약해지면 시장 변화에 취약해집니다.'),
('fortress', 'design', '대기업 인하우스, 공공기관 디자인', '외부 트렌드와 단절되면 디자인 감각이 정체됩니다.'),
('fortress', 'corporate', '대기업 재무/인사, 공기업 경영지원', '한 회사에 오래 있으면 외부 시장가치를 모르게 됩니다.'),
-- conqueror
('conqueror', 'tech', '빅테크 시니어, 핀테크 리드, 높은 RSU 제공 기업', '보상에 집중하면 기술적 깊이가 약해질 수 있습니다.'),
('conqueror', 'planning', '빅테크 PM, 전략 컨설팅, VC/PE 투자심사역', '보상과 타이틀에 집착하면 실질적 기획 역량이 정체됩니다.'),
('conqueror', 'marketing', '퍼포먼스 에이전시 임원, 빅테크 마케팅 리드', '매출 기여만 추구하면 브랜드 역량이 약해집니다.'),
('conqueror', 'sales', '엔터프라이즈 세일즈, 투자 세일즈, 고연봉 영업직', '단기 실적 추구가 장기 고객 관계를 해칠 수 있습니다.'),
('conqueror', 'design', '빅테크 디자인 리드, 에이전시 CD', '보상 중심 이동은 포트폴리오의 일관성을 해칩니다.'),
('conqueror', 'corporate', '경영 컨설팅, 투자은행, CFO 트랙', '보상과 직급에만 집중하면 실무 역량이 약해집니다.'),
-- nomad
('nomad', 'tech', '디지털 노마드 개발자, 프리랜서, 오픈소스 컨트리뷰터', '유연성 자체가 목적이 되면 깊이도 영향력도 쌓이지 않습니다.'),
('nomad', 'planning', '프리랜서 PM/기획 컨설턴트, 멀티 프로젝트', '프로덕트의 성장을 끝까지 보지 못하면 기획 역량이 제한됩니다.'),
('nomad', 'marketing', '프리랜서 마케터, 포트폴리오 커리어', '브랜드 마케팅은 시간이 걸립니다. 짧은 프로젝트만으론 한계가 있습니다.'),
('nomad', 'sales', '독립 에이전트, 프리랜서 세일즈 컨설턴트', '영업은 관계 비즈니스입니다. 유목 생활이 네트워크 구축을 방해할 수 있습니다.'),
('nomad', 'design', '프리랜서 디자이너, 디지털 노마드', '클라이언트 의존도가 높으면 진정한 자유가 아닙니다.'),
('nomad', 'corporate', '프리랜서 회계사, 독립 HR 컨설턴트', '경영지원은 조직 맥락을 깊이 아는 것이 핵심인데, 짧은 관여로는 어렵습니다.'),
-- gardener
('gardener', 'tech', '대기업 R&D, 사내 기술 리더, 내부 이동 활용', '외부 시장 가치를 점검하지 않으면 사내에서만 통하는 전문가가 됩니다.'),
('gardener', 'planning', '대기업 기획실, 안정적 서비스의 지속적 개선', '새로운 시장/서비스 경험 없이는 기획 역량에 한계가 옵니다.'),
('gardener', 'marketing', '대기업 브랜드팀, 안정적 마케팅 조직', '같은 브랜드만 오래 하면 새 도전에 대한 감각이 둔해집니다.'),
('gardener', 'sales', '대기업 핵심 고객 관리, 장기 파트너십 영업', '신규 개척 없이 관리만 하면 영업 근육이 약해집니다.'),
('gardener', 'design', '대기업 디자인센터, 디자인 시스템 장기 운영', '같은 가이드라인 안에서만 작업하면 창의성이 정체됩니다.'),
('gardener', 'corporate', '대기업 재무/인사 전문가, 장기 근속', '한 회사에 최적화되면 이직 시 적응이 어렵습니다.'),
-- sovereign
('sovereign', 'tech', '창업, 소규모 팀 리더, 독립 컨설턴트', '모든 것을 직접 통제하려는 성향이 위임 실패와 번아웃으로 이어질 수 있습니다.'),
('sovereign', 'planning', '1인 PM, 사내 벤처, 독립 프로덕트 컨설팅', '혼자 결정하는 습관이 팀 협업을 어렵게 만들 수 있습니다.'),
('sovereign', 'marketing', '1인 마케팅 에이전시, 사내 벤처 마케팅 리드', '혼자서 다 하려다 전문성 깊이가 얕아질 수 있습니다.'),
('sovereign', 'sales', '독립 세일즈 에이전트, 소규모 팀 영업 리더', '영업은 조직 지원이 중요합니다. 혼자 다 하면 스케일이 안 됩니다.'),
('sovereign', 'design', '1인 디자인 스튜디오, 사내 벤처 디자인 리드', '클라이언트 관리와 디자인을 동시에 하면 둘 다 약해질 수 있습니다.'),
('sovereign', 'corporate', '소규모 법인 CFO, 스타트업 COO', '경영지원을 혼자 맡으면 전문 분야의 깊이가 얕아집니다.'),
-- strategist
('strategist', 'tech', 'PM, 전략 기획, 매니지먼트 트랙', '균형 추구가 어느 것도 강하지 않은 상태로 이어질 수 있습니다.'),
('strategist', 'planning', '전략 기획, 사업개발, PM → 경영 트랙', '다방면에 관심이 분산되면 전문성이 약해집니다.'),
('strategist', 'marketing', '마케팅 전략가, 브랜드+퍼포먼스 양쪽 경험', '다 잘하려다 아무것도 깊지 않을 수 있습니다.'),
('strategist', 'sales', '전략 영업, 사업개발, 파트너십 매니저', '너무 전략적으로만 접근하면 현장 감각을 잃습니다.'),
('strategist', 'design', 'UX 전략가, 디자인+기획 겸직', '디자인과 전략 사이에서 정체성이 모호해질 수 있습니다.'),
('strategist', 'corporate', '전략기획실, 경영진 보좌, MBA 트랙', '전략만 하고 실행을 안 하면 신뢰를 잃습니다.');

-- ━━ 8. JOB GROUPS & JOBS ━━
-- job_groups uses AUTO_INCREMENT, so we use variables to capture IDs

INSERT INTO job_groups (group_label, color, sort_order) VALUES ('기술', '#4b8df8', 0);
SET @g_tech = LAST_INSERT_ID();
INSERT IGNORE INTO jobs (id, group_id, label, icon, scenario, sort_order) VALUES
('dev', @g_tech, '개발', '💻', 'tech', 0),
('devops', @g_tech, 'DevOps/인프라', '🛠️', 'tech', 1),
('security', @g_tech, '보안', '🔐', 'tech', 2),
('data', @g_tech, '데이터 분석', '📊', 'tech', 3),
('ai', @g_tech, 'AI / ML', '🤖', 'tech', 4);

INSERT INTO job_groups (group_label, color, sort_order) VALUES ('디자인', '#e85d9a', 1);
SET @g_design = LAST_INSERT_ID();
INSERT IGNORE INTO jobs (id, group_id, label, icon, scenario, sort_order) VALUES
('uxui', @g_design, 'UX/UI 디자인', '🎨', 'design', 0),
('graphic', @g_design, '그래픽/영상', '🎬', 'design', 1);

INSERT INTO job_groups (group_label, color, sort_order) VALUES ('비즈니스', '#f0a030', 2);
SET @g_biz = LAST_INSERT_ID();
INSERT IGNORE INTO jobs (id, group_id, label, icon, scenario, sort_order) VALUES
('pm', @g_biz, '서비스기획/PM', '📋', 'planning', 0),
('po', @g_biz, '프로덕트 오너', '📦', 'planning', 1),
('marketing', @g_biz, '마케팅', '📢', 'marketing', 2),
('content', @g_biz, '콘텐츠/에디터', '✍️', 'marketing', 3),
('sales', @g_biz, '영업/세일즈', '🤝', 'sales', 4),
('cs', @g_biz, '고객성공(CS/CX)', '📞', 'sales', 5);

INSERT INTO job_groups (group_label, color, sort_order) VALUES ('경영', '#34c77b', 3);
SET @g_mgmt = LAST_INSERT_ID();
INSERT IGNORE INTO jobs (id, group_id, label, icon, scenario, sort_order) VALUES
('finance', @g_mgmt, '재무/회계', '💰', 'corporate', 0),
('hr', @g_mgmt, '인사(HR)', '👤', 'corporate', 1),
('legal', @g_mgmt, '총무/법무', '📑', 'corporate', 2);

INSERT INTO job_groups (group_label, color, sort_order) VALUES ('산업/연구', '#8b6cf6', 4);
SET @g_ind = LAST_INSERT_ID();
INSERT IGNORE INTO jobs (id, group_id, label, icon, scenario, sort_order) VALUES
('manufacturing', @g_ind, '생산/제조/품질', '🏭', 'corporate', 0),
('logistics', @g_ind, '물류/SCM', '🚛', 'corporate', 1),
('md', @g_ind, 'MD/바잉', '🏪', 'sales', 2),
('rnd', @g_ind, '연구/R&D', '🔬', 'tech', 3);

-- ━━ 9. PROFILER QUESTIONS ━━
INSERT IGNORE INTO profiler_questions (id, label, option_a_title, option_a_fx, option_b_title, option_b_fx) VALUES
(1, '보상 vs 성장', '연봉 40% 인상', '{"compensation": 0.9, "security": 0.2, "growth": -0.5, "autonomy": 0, "impact": -0.1, "flexibility": -0.1}', '연봉 동결', '{"compensation": -0.4, "security": -0.2, "growth": 0.9, "autonomy": 0.3, "impact": 0.1, "flexibility": 0.2}'),
(2, '안정성 vs 자율성', '대기업 정규직', '{"compensation": 0.3, "security": 0.9, "growth": -0.1, "autonomy": -0.7, "impact": 0.1, "flexibility": -0.3}', '계약직 1년 갱신', '{"compensation": -0.1, "security": -0.7, "growth": 0.1, "autonomy": 0.9, "impact": -0.1, "flexibility": 0.4}'),
(3, '영향력 vs 보상', '연봉 30% 인상', '{"compensation": 0.8, "security": 0.2, "growth": 0.1, "autonomy": -0.1, "impact": -0.6, "flexibility": 0}', '연봉 10% 삭감', '{"compensation": -0.5, "security": -0.1, "growth": 0.3, "autonomy": 0.2, "impact": 0.9, "flexibility": 0}'),
(4, '유연성 vs 안정성', '업계 1위 대기업', '{"compensation": 0.3, "security": 0.9, "growth": -0.2, "autonomy": -0.2, "impact": 0.2, "flexibility": -0.8}', '중견 회사', '{"compensation": -0.1, "security": -0.5, "growth": 0.3, "autonomy": 0.1, "impact": -0.1, "flexibility": 0.9}'),
(5, '성장 vs 자율성', '업계 최고 전문가에게 직접 배움', '{"compensation": 0, "security": 0.1, "growth": 0.9, "autonomy": -0.7, "impact": 0, "flexibility": -0.1}', '혼자 맡아서 자유롭게 진행', '{"compensation": 0, "security": -0.2, "growth": 0.2, "autonomy": 0.9, "impact": 0.2, "flexibility": 0.3}'),
(6, '보상 vs 유연성', '연봉 50% 인상', '{"compensation": 1, "security": 0.3, "growth": -0.1, "autonomy": -0.5, "impact": 0.1, "flexibility": -0.9}', '연봉 동결', '{"compensation": -0.3, "security": -0.1, "growth": 0.1, "autonomy": 0.4, "impact": 0, "flexibility": 0.9}'),
(7, '영향력 vs 성장', '리더 포지션', '{"compensation": 0.3, "security": 0.1, "growth": -0.4, "autonomy": 0.1, "impact": 0.9, "flexibility": -0.2}', '실무 전문가', '{"compensation": -0.1, "security": 0.1, "growth": 0.9, "autonomy": 0.2, "impact": -0.4, "flexibility": 0.2}'),
(8, '안정성 vs 보상', '공공기관급 안정성', '{"compensation": -0.5, "security": 1, "growth": -0.3, "autonomy": -0.2, "impact": -0.1, "flexibility": -0.3}', '초기 스타트업', '{"compensation": 0.8, "security": -0.9, "growth": 0.5, "autonomy": 0.2, "impact": 0.3, "flexibility": -0.1}'),
(9, '자율성 vs 영향력', '완전 자율 근무', '{"compensation": 0, "security": 0, "growth": 0.1, "autonomy": 0.9, "impact": -0.6, "flexibility": 0.3}', '출근 필수, 회의 빡빡', '{"compensation": 0.1, "security": 0.2, "growth": 0.2, "autonomy": -0.7, "impact": 0.9, "flexibility": -0.2}'),
(10, '성장 vs 안정성', '검증된 환경, 안정 운영', '{"compensation": 0.2, "security": 0.9, "growth": -0.6, "autonomy": -0.1, "impact": 0, "flexibility": -0.3}', '초기 스타트업', '{"compensation": -0.2, "security": -0.8, "growth": 0.9, "autonomy": 0.3, "impact": 0.2, "flexibility": 0.1}'),
(11, '유연성 vs 영향력', '업계 인정받는 포지션', '{"compensation": 0.2, "security": 0.3, "growth": 0.1, "autonomy": -0.1, "impact": 0.9, "flexibility": -0.7}', '무명이지만 범용적 역할', '{"compensation": -0.1, "security": -0.1, "growth": 0.3, "autonomy": 0.2, "impact": -0.5, "flexibility": 0.9}'),
(12, '보상 vs 자율성', '연봉 35% 인상', '{"compensation": 0.85, "security": 0.2, "growth": 0, "autonomy": -0.8, "impact": 0.1, "flexibility": -0.3}', '현재 연봉 유지', '{"compensation": -0.2, "security": 0, "growth": 0.1, "autonomy": 0.9, "impact": -0.1, "flexibility": 0.4}');

-- ━━ 10. QUESTION SCENARIOS ━━
-- tech
INSERT IGNORE INTO question_scenarios (question_id, scenario, desc_a, desc_b) VALUES
(1, 'tech', '기존과 동일한 기술 스택 유지', '한 번도 다뤄보지 않은 기술 스택을 처음부터 구축'),
(2, 'tech', '명확한 R&R, 매년 3~5% 인상. 출퇴근 고정, 재택 불가', '완전 원격, 업무 시간 자율, 프로젝트 선택권'),
(3, 'tech', '실무 개발자. 의사결정 참여 없음', '5인 팀 리드. 기술 선택, 채용, 아키텍처 직접 결정'),
(4, 'tech', '10년 안정적. 독자 플랫폼이라 이직 시 기술 전환 어려움', '3년 후 존속 불확실. 시장 범용 기술로 어디든 이직 가능'),
(5, 'tech', '그 사람의 방식을 따라야 하고, 자기 코드 스타일 불가', '사내에 배울 시니어 없음. 독학으로 해결'),
(6, 'tech', '3년 의무 근속. 중도 퇴사 시 위약금', '아무 구속 없음. 6개월마다 커리어 방향 재조정 가능'),
(7, 'tech', 'CTO 타이틀. 경영진 회의, 컨퍼런스 발표. 70%가 매니지먼트', '시니어 엔지니어. 최신 기술을 매일 다루고 깊이가 쌓임'),
(8, 'tech', '구조조정 가능성 제로. 연봉은 업계 평균의 80%', '2년 내 인수 또는 폐업 반반. 성공 시 스톡옵션으로 연봉 5배'),
(9, 'tech', '재택, 자기 일정, 프로젝트 선택. 조직 의사결정에 영향력 없음', '일정 자율 없음. 대신 팀 리드로서 조직 방향에 직접 영향'),
(10, 'tech', '새로 배울 건 적지만 실수할 일도 없음. 5년 후 같은 자리 보장', '3개월마다 기술 스택 변경. 성장은 폭발적이지만 회사가 망하면 처음부터'),
(11, 'tech', '컨퍼런스 초청, 네임밸류 높음. 다른 방향 전환은 어려움', '시장 인지도 없음. 경험이 3~4개 다른 직군으로 전환 가능'),
(12, 'tech', '주 5일 출근, 야근 빈번, 휴가 사용 자유롭지 않음', '주 4일 근무, 완전 원격, 업무 시간 자율 선택'),
-- planning
(1, 'planning', '기존과 동일한 서비스 운영 업무', '한 번도 해보지 않은 신규 서비스를 0→1로 기획'),
(2, 'planning', '명확한 R&R, 매년 3~5% 인상. 출퇴근 고정, 재택 불가', '완전 원격, 업무 시간 자율, 프로젝트 선택권'),
(3, 'planning', '기획 실무만 담당. 전략 회의 참여 없음', '프로덕트 리드. 로드맵, 우선순위, KPI 직접 결정'),
(4, 'planning', '10년 안정적. 자체 프로세스라 이직 시 경험 전환 어려움', '3년 후 존속 불확실. 범용적 기획 방법론으로 어디든 이직 가능'),
(5, 'planning', '업계 최고 PO에게 직접 배움. 그 사람의 프레임워크만 사용', '사내에 배울 사람 없음. 나만의 기획 프레임을 직접 구축'),
(6, 'planning', '3년 의무 근속. 중도 퇴사 시 위약금', '아무 구속 없음. 6개월마다 커리어 방향 재조정 가능'),
(7, 'planning', 'CPO 타이틀. 경영진 보고, 외부 발표. 70%가 매니지먼트', '실무 기획자. 매일 사용자 리서치하고 PRD 직접 작성'),
(8, 'planning', '구조조정 가능성 제로. 연봉은 업계 평균의 80%', '2년 내 인수 또는 폐업 반반. 성공 시 스톡옵션으로 연봉 5배'),
(9, 'planning', '재택, 자기 일정, 프로젝트 선택. 조직 의사결정에 영향력 없음', '일정 자율 없음. 대신 팀 리드로서 프로덕트 방향에 직접 영향'),
(10, 'planning', '안정적인 서비스 유지보수. 5년 후 같은 자리 보장', '3개월마다 피봇. 성장은 폭발적이지만 회사가 망하면 처음부터'),
(11, 'planning', '업계에서 인정받는 PM. 다른 분야 전환은 어려움', '시장 인지도 없음. 경험이 마케팅·영업·전략 등으로 전환 가능'),
(12, 'planning', '주 5일 출근, 야근 빈번, 휴가 사용 자유롭지 않음', '주 4일 근무, 완전 원격, 업무 시간 자율 선택'),
-- marketing
(1, 'marketing', '기존과 동일한 캠페인 반복 운영', '한 번도 해보지 않은 신규 채널/시장을 처음부터 개척'),
(2, 'marketing', '명확한 R&R, 매년 3~5% 인상. 출퇴근 고정, 재택 불가', '완전 원격, 업무 시간 자율, 프로젝트 선택권'),
(3, 'marketing', '실행 담당자. 전략 회의 참여 없음', '마케팅 팀 리드. 예산 배분, 채널 선택, KPI 직접 결정'),
(4, 'marketing', '10년 안정적. 자체 플랫폼 마케팅이라 범용 경험 부족', '3년 후 존속 불확실. 다양한 채널 경험으로 어디든 이직 가능'),
(5, 'marketing', '업계 최고 CMO에게 직접 배움. 그 사람의 방식만 따라야 함', '사내에 배울 사람 없음. 나만의 마케팅 전략을 직접 구축'),
(6, 'marketing', '3년 의무 근속. 중도 퇴사 시 위약금', '아무 구속 없음. 6개월마다 커리어 방향 재조정 가능'),
(7, 'marketing', 'CMO 타이틀. 경영진 보고, 외부 강연. 70%가 매니지먼트', '퍼포먼스 마케터. 매일 데이터 보고 캠페인 최적화. 깊이가 쌓임'),
(8, 'marketing', '구조조정 가능성 제로. 연봉은 업계 평균의 80%', '2년 내 인수 또는 폐업 반반. 성공 시 스톡옵션으로 연봉 5배'),
(9, 'marketing', '재택, 자기 일정, 프로젝트 선택. 조직 의사결정에 영향력 없음', '일정 자율 없음. 대신 팀 리드로서 브랜드 방향에 직접 영향'),
(10, 'marketing', '안정적인 브랜드 유지. 5년 후 같은 자리 보장', '매달 새 캠페인. 성장은 폭발적이지만 회사가 망하면 포트폴리오만 남음'),
(11, 'marketing', '업계에서 인정받는 마케터. 다른 분야 전환은 어려움', '시장 인지도 없음. 경험이 기획·영업·콘텐츠로 전환 가능'),
(12, 'marketing', '주 5일 출근, 야근 빈번, 휴가 사용 자유롭지 않음', '주 4일 근무, 완전 원격, 업무 시간 자율 선택'),
-- sales
(1, 'sales', '기존 고객 관리 위주의 안정적 영업', '신규 시장 개척. 고객 베이스를 처음부터 구축'),
(2, 'sales', '명확한 R&R, 매년 3~5% 인상. 출퇴근 고정, 재택 불가', '완전 자율, 성과만 내면 시간과 장소 자유'),
(3, 'sales', '담당 고객만 관리. 영업 전략 참여 없음', '영업팀 리드. 타겟 시장, 가격 정책, 파이프라인 직접 결정'),
(4, 'sales', '10년 안정적. 특정 산업 영업이라 다른 업종 전환 어려움', '3년 후 존속 불확실. 다양한 산업 경험으로 어디든 이직 가능'),
(5, 'sales', '업계 최고 영업 리더에게 직접 배움. 그 사람의 방식만 따름', '사내에 배울 사람 없음. 나만의 영업 프로세스를 직접 구축'),
(6, 'sales', '3년 의무 근속. 중도 퇴사 시 위약금', '아무 구속 없음. 6개월마다 커리어 방향 재조정 가능'),
(7, 'sales', '영업본부장. 경영진 보고, 핵심 고객 미팅. 70%가 매니지먼트', '탑세일즈. 매일 현장에서 딜 클로징. 실력이 직접 쌓임'),
(8, 'sales', '구조조정 가능성 제로. 연봉은 업계 평균의 80%', '2년 내 인수 또는 폐업 반반. 성공 시 인센티브로 연봉 5배'),
(9, 'sales', '재택, 자기 일정, 고객 선택. 조직 의사결정에 영향력 없음', '일정 자율 없음. 대신 팀 리드로서 영업 전략에 직접 영향'),
(10, 'sales', '기존 거래처 유지. 5년 후 같은 자리 보장', '매달 새 고객 발굴. 성장은 폭발적이지만 파이프라인이 끊기면 처음부터'),
(11, 'sales', '업계에서 인정받는 영업 전문가. 다른 직군 전환은 어려움', '시장 인지도 없음. 경험이 마케팅·사업개발·컨설팅으로 전환 가능'),
(12, 'sales', '주 5일 출근, 야근 빈번, 휴가 사용 자유롭지 않음', '주 4일 근무, 완전 원격, 업무 시간 자율 선택'),
-- design
(1, 'design', '기존과 동일한 디자인 시스템 유지 운영', '한 번도 해보지 않은 브랜딩을 처음부터 구축'),
(2, 'design', '명확한 R&R, 매년 3~5% 인상. 출퇴근 고정, 재택 불가', '완전 원격, 업무 시간 자율, 프로젝트 선택권'),
(3, 'design', '시안 제작만 담당. 방향성 결정 없음', '디자인 리드. 브랜딩, UX 방향, 디자인 시스템 직접 결정'),
(4, 'design', '10년 안정적. 자체 디자인 가이드라 이직 시 포트폴리오 약함', '3년 후 존속 불확실. 다양한 프로젝트로 포트폴리오 풍부'),
(5, 'design', '업계 최고 디자이너에게 직접 배움. 그 사람의 스타일만 따름', '사내에 배울 사람 없음. 나만의 디자인 철학을 직접 구축'),
(6, 'design', '3년 의무 근속. 중도 퇴사 시 위약금', '아무 구속 없음. 6개월마다 커리어 방향 재조정 가능'),
(7, 'design', 'CDO 타이틀. 경영진 보고, 외부 강연. 70%가 매니지먼트', '시니어 디자이너. 매일 직접 디자인하고 깊이가 쌓임'),
(8, 'design', '구조조정 가능성 제로. 연봉은 업계 평균의 80%', '2년 내 인수 또는 폐업 반반. 성공 시 스톡옵션으로 연봉 5배'),
(9, 'design', '재택, 자기 일정, 프로젝트 선택. 조직 의사결정에 영향력 없음', '일정 자율 없음. 대신 리드로서 제품 디자인 방향에 직접 영향'),
(10, 'design', '안정적인 유지보수 디자인. 5년 후 같은 자리 보장', '매달 새 프로젝트. 성장은 폭발적이지만 회사가 망하면 포트폴리오만 남음'),
(11, 'design', '업계에서 인정받는 디자이너. 다른 분야 전환은 어려움', '시장 인지도 없음. 경험이 기획·마케팅·프론트엔드로 전환 가능'),
(12, 'design', '주 5일 출근, 야근 빈번, 휴가 사용 자유롭지 않음', '주 4일 근무, 완전 원격, 업무 시간 자율 선택'),
-- corporate
(1, 'corporate', '기존과 동일한 프로세스 운영', '전사 시스템을 새로 설계. ERP 도입부터 직접 주도'),
(2, 'corporate', '명확한 R&R, 매년 3~5% 인상. 출퇴근 고정, 재택 불가', '완전 원격, 업무 시간 자율, 프로젝트 선택권'),
(3, 'corporate', '실무 담당자. 경영 의사결정 참여 없음', '팀 리드. 예산, 인력, 프로세스 직접 결정'),
(4, 'corporate', '10년 안정적. 특정 산업 경험이라 다른 업종 전환 어려움', '3년 후 존속 불확실. 범용적 경험으로 어디든 이직 가능'),
(5, 'corporate', '업계 최고 임원에게 직접 배움. 그 사람의 방식만 따름', '사내에 배울 사람 없음. 나만의 프로세스를 직접 구축'),
(6, 'corporate', '3년 의무 근속. 중도 퇴사 시 위약금', '아무 구속 없음. 6개월마다 커리어 방향 재조정 가능'),
(7, 'corporate', '임원 타이틀. 이사회 보고, 전사 의사결정. 70%가 매니지먼트', '실무 전문가. 매일 직접 분석하고 보고서 작성. 전문성이 쌓임'),
(8, 'corporate', '구조조정 가능성 제로. 연봉은 업계 평균의 80%', '2년 내 인수 또는 폐업 반반. 성공 시 스톡옵션으로 연봉 5배'),
(9, 'corporate', '재택, 자기 일정, 프로젝트 선택. 조직 의사결정에 영향력 없음', '일정 자율 없음. 대신 팀 리드로서 조직 운영에 직접 영향'),
(10, 'corporate', '안정적인 운영 업무. 5년 후 같은 자리 보장', '매달 새 과제. 성장은 폭발적이지만 회사가 망하면 처음부터'),
(11, 'corporate', '업계에서 인정받는 전문가. 다른 분야 전환은 어려움', '시장 인지도 없음. 경험이 컨설팅·기획·운영 등으로 전환 가능'),
(12, 'corporate', '주 5일 출근, 야근 빈번, 휴가 사용 자유롭지 않음', '주 4일 근무, 완전 원격, 업무 시간 자율 선택');
