#!/bin/bash
# KOSPI 시가총액 상위 기업 복지 페이지 스크래핑 명령어
# Usage: 개별 라인을 복사하여 터미널에서 실행
# 생성일: 2026-03-26

# ━━ KOSPI TOP 100 (우선주/중복 제외) ━━

server/tools/.venv/bin/python server/tools/scrape_benefits.py "삼성전자" --url "https://www.samsung-dxrecruit.com/benefit" --raw-only
# SK하이닉스: talent.skhynix.com 타임아웃 시 아래 대체 URL 사용
# 대체: server/tools/.venv/bin/python server/tools/scrape_benefits.py "SK하이닉스" --url "https://recruit.skhynix.com/servlet/reco_welfare.view" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "SK하이닉스" --url "https://talent.skhynix.com/hub/ko/culture/welfare" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "LG에너지솔루션" --url "https://www.lgensol.com/kr/career-recruit" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "삼성바이오로직스" --url "https://samsungbiologics.com/careers/apply/how-to-apply" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "현대자동차" --url "https://talent.hyundai.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "HD현대중공업" --url "https://recruit.hd.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "SK스퀘어" --url "https://www.skcareers.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "한화에어로스페이스" --url "https://www.hanwhaaerospace.com/kor/careers/recruit.do" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "두산에너빌리티" --url "https://career.doosan.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "KB금융" --url "https://careers.kbfg.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "기아" --url "https://talent.hyundai.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "셀트리온" --url "https://recruit.celltrion.com/celltrion.html" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "삼성물산" --url "https://www.samsungcnt.com/about-us/careers.do" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "NAVER" --url "https://recruit.navercorp.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "신한지주" --url "https://shinhan.recruiter.co.kr/career/home" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "한화오션" --url "https://www.hanwhain.com/web/apply/notification/list.do" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "현대모비스" --url "https://careers.mobis.com/life" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "삼성생명" --url "https://www.samsungcareers.com/subsid/detail/E11" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "한국전력" --url "https://recruit.kepco.co.kr:444/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "HD한국조선해양" --url "https://recruit.hd.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "HD현대일렉트릭" --url "https://recruit.hd.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "카카오" --url "https://careers.kakao.com/jobs" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "하나금융지주" --url "https://recruit.hanafn.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "POSCO홀딩스" --url "https://recruit.posco.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "고려아연" --url "https://careers.koreazinc.co.kr/recruit/announce" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "알테오젠" --url "https://www.alteogen.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "LG화학" --url "https://careers.lg.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "삼성화재" --url "https://www.samsungcareers.com/subsid/detail/E21" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "삼성SDI" --url "https://www.samsungsdi.co.kr/career/benefit.html" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "삼성중공업" --url "https://www.samsungcareers.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "우리금융지주" --url "https://www.woorifg.com/kor/recruit/recruit-announcement/list.do" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "현대로템" --url "https://hyundai-rotem.recruiter.co.kr/career/home" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "메리츠금융지주" --url "https://www.meritzfire.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "HMM" --url "https://hmm21.recruiter.co.kr/career/home" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "삼성전기" --url "https://www.sem-recruit.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "SK" --url "https://www.skcareers.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "SK이노베이션" --url "https://recruit.skinnovation.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "KT&G" --url "https://ktng.recruiter.co.kr/career/home" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "IBK기업은행" --url "https://www.ibk.co.kr/engage/recruitListEngage.ibk" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "포스코퓨처엠" --url "https://www.poscofuturem.com/recruitment/recruitment.do" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "효성중공업" --url "https://www.hyosungheavyindustries.com/kr/company/recruitment/personnel-system" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "LG전자" --url "https://www.lge.co.kr/company/recruit/hr" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "HD현대" --url "https://recruit.hd.com/kr/mainLayout/benefit" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "에코프로비엠" --url "https://www.jobkorea.co.kr/company/43761900/recruit" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "하이브" --url "https://careers.hybecorp.com/ko/home" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "LS ELECTRIC" --url "https://www.incruit.com/company/172828/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "현대글로비스" --url "https://www.glovis.net/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "삼성SDS" --url "https://www.samsungcareers.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "KT" --url "https://recruit.kt.com/life" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "미래에셋증권" --url "https://career.miraeasset.com/recruit01" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "두산" --url "https://career.doosan.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "LG" --url "https://careers.lg.com/" --raw-only
# TODO: 에코프로 — KOSDAQ 중복, KOSDAQ 파일에서 처리
server/tools/.venv/bin/python server/tools/scrape_benefits.py "한미반도체" --url "https://www.hanmisemi.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "크래프톤" --url "https://www.krafton.com/en/careers/jobs/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "SK텔레콤" --url "https://careers.sktelecom.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "한국항공우주산업" --url "https://koreaaero-recruit.careerlink.kr/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "에이비엘바이오" --url "https://www.ablbio.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "카카오뱅크" --url "https://recruit.kakaobank.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "한화시스템" --url "https://www.hanwhasystems-recruit.co.kr/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "SK바이오팜" --url "https://www.skbp.com/kor/recruit/careers.do" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "S-Oil" --url "https://s-oil.recruiter.co.kr/career/home" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "DB손해보험" --url "https://www.catch.co.kr/Comp/RecruitInfo/870099" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "삼양식품" --url "https://www.samyangfoods.com/kor/recruit/list.do" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "LIG넥스원" --url "https://lignex1.recruiter.co.kr/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "레인보우로보틱스" --url "https://www.rainbow-robotics.com/recruit" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "현대오토에버" --url "https://career.hyundai-autoever.com/ko/home" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "한국금융지주" --url "https://www.knfinancial.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "유한양행" --url "https://www.incruit.com/company/205403/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "이수페타시스" --url "https://recruit.isu.co.kr/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "포스코인터내셔널" --url "https://recruit.posco.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "HD현대마린솔루션" --url "https://recruit.hd.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "에이피알" --url "https://apr-careers.com/recruit" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "대한항공" --url "https://koreanair.recruiter.co.kr/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "한진칼" --url "https://koreanair.recruiter.co.kr/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "현대건설" --url "https://recruit.hdec.co.kr/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "키움증권" --url "https://www.kiwoom.com/h/ir/recruit/VProcessView" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "NH투자증권" --url "https://nhqv.recruiter.co.kr/career/home" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "한국타이어앤테크놀로지" --url "https://www.jobkorea.co.kr/company/1747282/recruit" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "아모레퍼시픽" --url "https://www.jobkorea.co.kr/recruit/co_read/recruit/c/26930965" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "삼성증권" --url "https://www.samsungcareers.com/" --raw-only
# TODO: HLB — KOSDAQ 중복, KOSDAQ 파일에서 처리
server/tools/.venv/bin/python server/tools/scrape_benefits.py "카카오페이" --url "https://kakaopay.career.greetinghr.com/ko/main" --raw-only
# TODO: 코오롱티슈진 — KOSDAQ 중복, KOSDAQ 파일에서 처리
server/tools/.venv/bin/python server/tools/scrape_benefits.py "삼성카드" --url "https://www.samsungcareers.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "LG이노텍" --url "https://careers.lg.com/" --raw-only
# TODO: 리가켐바이오 — KOSDAQ 중복, KOSDAQ 파일에서 처리
server/tools/.venv/bin/python server/tools/scrape_benefits.py "LS" --url "https://recruit.isu.co.kr/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "LG유플러스" --url "https://careers.lg.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "코웨이" --url "https://www.coway.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "한화" --url "https://www.hanwhain.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "LG씨엔에스" --url "https://www.lgcns.com/" --raw-only
# TODO: 펩트론 — KOSDAQ 중복, KOSDAQ 파일에서 처리
server/tools/.venv/bin/python server/tools/scrape_benefits.py "LG디스플레이" --url "https://careers.lg.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "한미약품" --url "https://www.hanmi.co.kr/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "두산밥캣" --url "https://career.doosan.com/" --raw-only
# TODO: 삼천당제약 — KOSDAQ 중복, KOSDAQ 파일에서 처리
server/tools/.venv/bin/python server/tools/scrape_benefits.py "삼성에피스홀딩스" --url "https://www.samsungcareers.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "현대제철" --url "https://talent.hyundai.com/" --raw-only
server/tools/.venv/bin/python server/tools/scrape_benefits.py "롯데케미칼" --url "https://www.lottechem.com/" --raw-only
