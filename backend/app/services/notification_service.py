"""
Notification service. Currently implements EMAIL via SMTP.

Designed so additional channels (WhatsApp, SMS, browser push) can be added
later as new send_* functions / classes implementing the same interface
without touching the callers.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings


class NotificationChannel:
    def send(self, subject: str, body: str) -> bool:
        raise NotImplementedError


class EmailNotificationChannel(NotificationChannel):
    def send(self, subject: str, body: str) -> bool:
        if not (settings.SMTP_HOST and settings.SMTP_USERNAME and settings.ALERT_EMAIL):
            print("[notification_service] SMTP not configured; skipping email send.")
            return False

        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_USERNAME
        msg["To"] = settings.ALERT_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            if settings.SMTP_USE_TLS:
                context = ssl.create_default_context()
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    server.starttls(context=context)
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    server.sendmail(settings.SMTP_USERNAME, [settings.ALERT_EMAIL], msg.as_string())
            else:
                with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    server.sendmail(settings.SMTP_USERNAME, [settings.ALERT_EMAIL], msg.as_string())
            return True
        except Exception as exc:
            print(f"[notification_service] Failed to send email: {exc}")
            return False


def send_unauthorized_expansion_email(image_date: str, expansion_area_ha: float) -> bool:
    subject = "\U0001F6A8 Potential Unauthorized Quarry Expansion Detected"
    body = (
        "Quarry Monitoring Alert\n\n"
        f"Date: {image_date}\n\n"
        "Potential new excavation detected outside the permitted boundary.\n\n"
        f"Expansion area: {expansion_area_ha} ha\n\n"
        "Please open the monitoring dashboard for map details."
    )
    channel = EmailNotificationChannel()
    return channel.send(subject, body)
