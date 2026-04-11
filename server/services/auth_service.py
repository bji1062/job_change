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


def create_token(user_id: int, role: str = "user", cev: bool = False) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=config.JWT_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": str(user_id), "role": role, "cev": cev, "exp": exp},
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
    provider: str, provider_id: str, email: str | None, name: str | None,
    email_verified: bool = False
) -> dict:
    """소셜 로그인 사용자 조회 또는 생성. 반환: {id, email, name, role, company_email_verification_yn}"""
    # 1. TSOCIAL_ACCOUNT에서 기존 연동 조회
    sa = await database.fetch_one(
        "SELECT MBR_ID AS user_id FROM TSOCIAL_ACCOUNT WHERE PROVIDER_CD=%s AND PROVIDER_USER_ID=%s",
        (provider, provider_id),
    )
    if sa:
        user = await database.fetch_one(
            "SELECT MBR_ID AS id, EMAIL_ADDR AS email, MBR_NM AS name, ROLE_CD AS role, COMP_EMAIL_VRFC_YN AS company_email_verification_yn FROM TMEMBER WHERE MBR_ID=%s",
            (sa["user_id"],),
        )
        if user:
            return {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "role": user.get("role") or "user",
                "company_email_verification_yn": user.get("company_email_verification_yn", "N"),
            }

    # 2. 이메일로 기존 사용자 조회 (이메일이 검증된 경우만 자동 연동)
    if email and email_verified:
        user = await database.fetch_one(
            "SELECT MBR_ID AS id, EMAIL_ADDR AS email, MBR_NM AS name, ROLE_CD AS role, COMP_EMAIL_VRFC_YN AS company_email_verification_yn FROM TMEMBER WHERE EMAIL_ADDR=%s",
            (email,),
        )
        if user:
            # TSOCIAL_ACCOUNT 연동 추가
            await database.execute(
                "INSERT INTO TSOCIAL_ACCOUNT (MBR_ID, PROVIDER_CD, PROVIDER_USER_ID, EMAIL_ADDR, SOCIAL_NM) VALUES (%s,%s,%s,%s,%s)",
                (user["id"], provider, provider_id, email, name),
            )
            return {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "role": user.get("role") or "user",
                "company_email_verification_yn": user.get("company_email_verification_yn", "N"),
            }

    # 3. 신규 사용자 생성
    use_email = email or f"{provider}_{provider_id}@social.local"
    user_id = await database.execute(
        "INSERT INTO TMEMBER (EMAIL_ADDR, PWD_HASH_VAL, MBR_NM, LOGIN_PROVIDER_CD) VALUES (%s, NULL, %s, %s)",
        (use_email, name, provider),
    )
    await database.execute(
        "INSERT INTO TSOCIAL_ACCOUNT (MBR_ID, PROVIDER_CD, PROVIDER_USER_ID, EMAIL_ADDR, SOCIAL_NM) VALUES (%s,%s,%s,%s,%s)",
        (user_id, provider, provider_id, email, name),
    )
    return {
        "id": user_id,
        "email": use_email,
        "name": name,
        "role": "user",
        "company_email_verification_yn": "N",
    }


def is_company_email(email: str) -> bool:
    """개인 이메일 도메인이 아니면 회사 이메일로 판단"""
    domain = email.rsplit("@", 1)[-1].lower()
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
