---
name: deploy
description: 인프라(Terraform) + 배포(Nginx/systemd) 관리 에이전트
user-invocable: true
---

# /deploy — 인프라 및 배포 관리

사용자가 `/deploy {작업 설명}` 을 실행하면 아래 단계를 수행합니다.

## 실행 단계

### 1단계: 모드 판별

| 호출 | 동작 |
|------|------|
| `/deploy` | 인프라 전체 현황 리포트 |
| `/deploy {작업}` | 해당 작업 수행 |

### 2단계a: 현황 리포트 (`/deploy` — 인자 없음)

다음을 **병렬**로 읽습니다:
1. `Glob "infra/*.tf"` → Terraform 파일 목록
2. `Read server/deploy/nginx.conf` → Nginx 설정
3. `Read server/deploy/jobchoice.service` → systemd 설정
4. `Read server/deploy/my.cnf` → MySQL 설정

리포트 형식:
```
## 인프라 현황
| 컴포넌트 | 상태 | 설정 |
|----------|------|------|
| Terraform | ✅ | ARM 2 OCPU, 12GB, 춘천 |
| Nginx | ⚠️ | SSL 있음, 보안 헤더 없음 |
| systemd | ✅ | 자동 재시작 설정됨 |
| MySQL | ✅ | 6GB RAM 최적화 |
```

### 2단계b: 작업 수행 (`/deploy {작업}`)

| 유형 | 키워드 | 대상 파일 |
|------|--------|----------|
| Terraform | infra, 서버, 네트워크, 보안그룹 | `infra/*.tf` |
| Nginx | nginx, SSL, 리버스프록시, 도메인 | `server/deploy/nginx.conf` |
| systemd | 서비스, 재시작, 로그 | `server/deploy/jobchoice.service` |
| MySQL | DB 설정, 튜닝, 백업 | `server/deploy/my.cnf` |
| 환경변수 | env, 설정 | `server/.env.example` |

변경 대상 파일을 **반드시** Read한 뒤 수정합니다.

### 4단계: 완료 출력

```
## 변경 완료
| 파일 | 변경 내용 |
|------|----------|
| server/deploy/nginx.conf | X-Frame-Options 헤더 추가 |

### 적용 방법
ssh ubuntu@{IP} "sudo nginx -t && sudo systemctl reload nginx"

### 다음 추천
- `/audit` — 변경 검증
```

---

## 인프라 현황

| 컴포넌트 | 설정 |
|----------|------|
| Compute | OCI VM.Standard.A1.Flex (ARM), 2 OCPU, 12GB RAM |
| Region | ap-chuncheon-1 (춘천) |
| Network | VCN 10.0.0.0/16, public subnet 10.0.1.0/24 |
| 보안 | SSH 제한, HTTP/HTTPS 개방, MySQL 외부 차단 |
| 배포 구조 | Nginx(:443) → static + proxy → Uvicorn(:8000) → MySQL(:3306) |

## 참조 파일

| 파일 | 내용 |
|------|------|
| `infra/provider.tf` | OCI 프로바이더 |
| `infra/variables.tf` | 변수 선언 |
| `infra/network.tf` | VCN, 서브넷, 보안 리스트 |
| `infra/compute.tf` | ARM 인스턴스 + 부트 볼륨 |
| `infra/outputs.tf` | Public IP, SSH 명령 |
| `server/deploy/nginx.conf` | 리버스 프록시 + SSL |
| `server/deploy/jobchoice.service` | systemd 서비스 |
| `server/deploy/my.cnf` | MySQL 튜닝 (6GB RAM) |

## 주의사항

- Terraform 변경은 **plan 먼저** — `terraform plan` 결과를 사용자에게 보여준 후 apply
- nginx 설정 변경 후 `nginx -t`로 문법 검증 필수
- SSL 인증서는 Let's Encrypt (자동 갱신 설정 확인)
- Always Free 제한: 2 OCPU, 12GB RAM, 200GB 스토리지
