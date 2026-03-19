-- Update popular_cases with detailed points and view counts
-- Run: mysql -u root jobchoice < server/seed/update_popular.sql
SET NAMES utf8mb4;

DELETE FROM popular_cases;

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
