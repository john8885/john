"""이메일 / 메시지 발송"""
import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD

logger = logging.getLogger(__name__)


def send_email(
    to: list[str],
    subject: str,
    body_html: str,
    attachments: list[str] | None = None,
    cc: list[str] | None = None,
) -> bool:
    """HTML 이메일 발송. 성공 시 True."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)

    msg.attach(MIMEText(body_html, "html", "utf-8"))

    for path_str in (attachments or []):
        path = Path(path_str)
        part = MIMEBase("application", "octet-stream")
        part.set_payload(path.read_bytes())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{path.name}"')
        msg.attach(part)

    recipients = to + (cc or [])
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, recipients, msg.as_string())
        logger.info("Email sent to %s", recipients)
        return True
    except Exception as e:
        logger.error("Email send failed: %s", e)
        return False


def send_bulk_email(
    recipients: list[dict],  # [{"email": "...", "name": "...", ...}]
    subject_template: str,
    body_template: str,
) -> dict:
    """개인화 대량 메일 발송. subject/body 안에 {name} 등 변수 사용 가능."""
    results = {"success": 0, "fail": 0, "failed_emails": []}
    for r in recipients:
        subject = subject_template.format(**r)
        body = body_template.format(**r)
        ok = send_email([r["email"]], subject, body)
        if ok:
            results["success"] += 1
        else:
            results["fail"] += 1
            results["failed_emails"].append(r["email"])
    logger.info("Bulk email: %d success, %d fail", results["success"], results["fail"])
    return results


def render_newsletter(template_path: str, context: dict) -> str:
    """Jinja2 HTML 템플릿으로 뉴스레터 렌더링."""
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader(str(Path(template_path).parent)))
    tmpl = env.get_template(Path(template_path).name)
    return tmpl.render(**context)
