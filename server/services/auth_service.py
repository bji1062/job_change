import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
import config
import database

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def create_token(mbr_id: int, role_cd: str = "user", cev: int | None = None) -> str:
    """
    cev (company-email-verified): 인증된 회사의 comp_id 정수.
    - 미인증: None
    - 인증 완료: 해당 회사의 comp_id (int)
    bool 인자는 받지 않음 — 회사 식별 없이 '인증만 했다'는 의미는 권한 검증에 부적합.
    """
    if isinstance(cev, bool):
        raise TypeError("cev must be int (comp_id) or None, not bool")
    exp = datetime.now(timezone.utc) + timedelta(hours=config.JWT_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": str(mbr_id), "role_cd": role_cd, "cev": cev, "exp": exp},
        config.JWT_SECRET,
        algorithm="HS256",
    )


def decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
        return int(payload["sub"])
    except Exception:
        return None


def decode_token_full(token: str) -> dict | None:
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return None


async def find_or_create_social_user(
    provider_cd: str, provider_user_id: str, email_addr: str | None, social_nm: str | None,
    email_verified: bool = False
) -> dict:
    """소셜 로그인 사용자 조회 또는 생성. 반환: {mbr_id, email_addr, mbr_nm, role_cd, comp_email_vrfc_yn}"""
    # 1. TSOCIAL_ACCOUNT에서 기존 연동 조회
    sa = await database.fetch_one(
        "SELECT MBR_ID AS mbr_id FROM TSOCIAL_ACCOUNT WHERE PROVIDER_CD=%s AND PROVIDER_USER_ID=%s",
        (provider_cd, provider_user_id),
    )
    if sa:
        user = await database.fetch_one(
            """SELECT MBR_ID AS mbr_id, EMAIL_ADDR AS email_addr, MBR_NM AS mbr_nm,
                      ROLE_CD AS role_cd, COMP_EMAIL_VRFC_YN AS comp_email_vrfc_yn,
                      VRFC_COMP_ID AS vrfc_comp_id
               FROM TMEMBER WHERE MBR_ID=%s""",
            (sa["mbr_id"],),
        )
        if user:
            return {
                "mbr_id": user["mbr_id"],
                "email_addr": user["email_addr"],
                "mbr_nm": user["mbr_nm"],
                "role_cd": user.get("role_cd") or "user",
                "comp_email_vrfc_yn": user.get("comp_email_vrfc_yn", "N"),
                "vrfc_comp_id": user.get("vrfc_comp_id"),
            }

    # 2. 이메일로 기존 사용자 조회 (이메일이 검증된 경우만 자동 연동)
    if email_addr and email_verified:
        user = await database.fetch_one(
            """SELECT MBR_ID AS mbr_id, EMAIL_ADDR AS email_addr, MBR_NM AS mbr_nm,
                      ROLE_CD AS role_cd, COMP_EMAIL_VRFC_YN AS comp_email_vrfc_yn,
                      VRFC_COMP_ID AS vrfc_comp_id
               FROM TMEMBER WHERE EMAIL_ADDR=%s""",
            (email_addr,),
        )
        if user:
            # TSOCIAL_ACCOUNT 연동 추가
            await database.execute(
                "INSERT INTO TSOCIAL_ACCOUNT (MBR_ID, PROVIDER_CD, PROVIDER_USER_ID, EMAIL_ADDR, SOCIAL_NM) VALUES (%s,%s,%s,%s,%s)",
                (user["mbr_id"], provider_cd, provider_user_id, email_addr, social_nm),
            )
            return {
                "mbr_id": user["mbr_id"],
                "email_addr": user["email_addr"],
                "mbr_nm": user["mbr_nm"],
                "role_cd": user.get("role_cd") or "user",
                "comp_email_vrfc_yn": user.get("comp_email_vrfc_yn", "N"),
                "vrfc_comp_id": user.get("vrfc_comp_id"),
            }

    # 3. 신규 사용자 생성
    use_email = email_addr or f"{provider_cd}_{provider_user_id}@social.local"
    mbr_id = await database.execute(
        "INSERT INTO TMEMBER (EMAIL_ADDR, PWD_HASH_VAL, MBR_NM, LOGIN_PROVIDER_CD) VALUES (%s, NULL, %s, %s)",
        (use_email, social_nm, provider_cd),
    )
    await database.execute(
        "INSERT INTO TSOCIAL_ACCOUNT (MBR_ID, PROVIDER_CD, PROVIDER_USER_ID, EMAIL_ADDR, SOCIAL_NM) VALUES (%s,%s,%s,%s,%s)",
        (mbr_id, provider_cd, provider_user_id, email_addr, social_nm),
    )
    return {
        "mbr_id": mbr_id,
        "email_addr": use_email,
        "mbr_nm": social_nm,
        "role_cd": "user",
        "comp_email_vrfc_yn": "N",
        "vrfc_comp_id": None,
    }


def is_company_email(email_addr: str) -> bool:
    """개인 이메일 도메인이 아니면 회사 이메일로 판단"""
    domain = email_addr.rsplit("@", 1)[-1].lower()
    return domain not in config.PERSONAL_DOMAINS


async def send_verification_email(to_email: str, token: str) -> None:
    """회사 이메일 인증 메일 발송. SMTP_USER가 비어있으면 스킵 (개발 환경)."""
    if not config.SMTP_USER:
        return

    verify_link = f"{config.OAUTH_REDIRECT_BASE}/?verify_email={token}"
    subject = "[직장선택OS] 회사 이메일 인증"
    html_body = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
        <h2>회사 이메일 인증</h2>
        <p>아래 버튼을 클릭하여 이메일 인증을 완료해주세요.</p>
        <a href="{verify_link}"
           style="display:inline-block; padding:12px 24px; background:#4A9B8E;
                  color:#fff; text-decoration:none; border-radius:8px; margin:16px 0;">
           이메일 인증하기
        </a>
        <p style="color:#888; font-size:13px;">이 링크는 24시간 동안 유효합니다.</p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.SMTP_FROM or config.SMTP_USER
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    def _send():
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASS)
            server.send_message(msg)

    await asyncio.to_thread(_send)
