-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 삼성전자 복리후생 데이터
-- 출처: WebSearch 기반 수집 (2026-03-20)
-- badge: 'est' (추정치 — 공식 확인 시 'official'로 변경)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- 1) 회사 등록 (없는 경우)
INSERT IGNORE INTO companies (id, name, type_id, industry, logo, careers_benefit_url)
VALUES ('samsung', '삼성전자', 'large', '전자/반도체', 'S', 'https://www.samsung-dxrecruit.com/benefit');

-- 2) 기존 추정 데이터 삭제 (official 보존)
DELETE FROM company_benefits WHERE company_id = 'samsung' AND badge = 'est';

-- 3) 복리후생 INSERT
INSERT INTO company_benefits
  (company_id, ben_key, name, val, category, badge, note, is_qualitative, qual_text, sort_order)
VALUES
  -- ── 현금성 (money) ──
  ('samsung', 'welfare_point',   '맞춤형 복지포인트',           200, 'money', 'est', '건강/여행/공연/도서/교육 자율 사용', FALSE, NULL, 1),
  ('samsung', 'meal',            '구내식당 (한식/중식/일식/양식/인도식)', 432, 'money', 'est', '일 18,000원 × 240일 환산', FALSE, NULL, 2),
  ('samsung', 'product_discount','자사 제품 임직원가 구매',     100, 'money', 'est', '가전/모바일 할인', FALSE, NULL, 3),
  ('samsung', 'family_net',      '패밀리넷몰 포인트',           200, 'money', 'est', '2025년 전 직원 200만 포인트', FALSE, NULL, 4),
  ('samsung', 'stock',           '자사주 지급',                   0, 'money', 'est', NULL, TRUE, '전 직원 30주 지급 (2025년 기준)', 5),
  ('samsung', 'shift_pay',       '교대근무 수당',                 0, 'money', 'est', NULL, TRUE, '월 20일 근무 시 25만원 (2025년 신설)', 6),
  ('samsung', 'event',           '경조사 지원',                  50, 'money', 'est', '경조금 + 경조휴가', FALSE, NULL, 7),

  -- ── 건강/의료 (health) ──
  ('samsung', 'health_check',    '건강검진 (본인+가족)',        100, 'health', 'est', NULL, FALSE, NULL, 10),
  ('samsung', 'medical',         '의료비 지원 (본인+가족)',     100, 'health', 'est', NULL, FALSE, NULL, 11),
  ('samsung', 'clinic',          '사내 부속의원 (내과/치과/한의원)', 0, 'health', 'est', NULL, TRUE, '전문 진료 무료 운영', 12),
  ('samsung', 'pharmacy',        '사내 약국',                     0, 'health', 'est', NULL, TRUE, '사업장 내 약국 운영', 13),
  ('samsung', 'mental',          '심리상담센터',                   0, 'health', 'est', NULL, TRUE, '전문 심리상담 무료 제공', 14),
  ('samsung', 'physio',          '근골격센터',                     0, 'health', 'est', NULL, TRUE, '물리치료 등 근골격 관리', 15),

  -- ── 생활/여가 (life) ──
  ('samsung', 'commute',         '통근버스',                    120, 'life', 'est', '사업장별 통근버스 운영', FALSE, NULL, 20),
  ('samsung', 'waterpark',       '워터파크 무료 + 테마파크 할인', 50, 'life', 'est', NULL, FALSE, NULL, 21),
  ('samsung', 'resort',          '호텔/휴양지 숙박 지원',        50, 'life', 'est', NULL, FALSE, NULL, 22),
  ('samsung', 'library',         '사내 북카페/구독형 도서관',     0, 'life', 'est', NULL, TRUE, '도서 대출·반납, 온라인 구독형 도서관', 23),
  ('samsung', 'club',            '사내 동아리',                  30, 'life', 'est', '동아리 운영비 지원', FALSE, NULL, 24),

  -- ── 가족 (family) ──
  ('samsung', 'child_edu',       '자녀 학자금 지원',            300, 'family', 'est', '중·고·대학교', FALSE, NULL, 30),
  ('samsung', 'child_reemploy',  '3자녀 이상 정년 후 재고용',     0, 'family', 'est', NULL, TRUE, '2025년 제도화', 31),

  -- ── 휴가/근무 (leave) ──
  ('samsung', 'refresh',         '리프레시 휴가',                 0, 'leave', 'est', NULL, TRUE, '연 3일 추가 유급휴가', 40),
  ('samsung', 'dev_day',         'Development Day',               0, 'leave', 'est', NULL, TRUE, '월 중 자기개발 휴무일', 41),
  ('samsung', 'flex_work',       'Work Smart 유연근무',           0, 'leave', 'est', NULL, TRUE, '월 총 근무시간 내 출퇴근·일일 근무시간 자율 결정, 자율 근무존(카페형/도서관형/독서실형) + 사외 거점 오피스', 42);
