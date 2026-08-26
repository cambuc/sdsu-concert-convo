import os
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"


def _load_env_file(path: Path = ENV_PATH):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


class SMTPClient:
    def __init__(self, host: str, port: int):
        _load_env_file()

        username = os.environ.get("SMTP_USERNAME")
        password = os.environ.get("SMTP_APP_PASSWORD")
        if not username or not password:
            raise FileNotFoundError(
                f"Missing SMTP_USERNAME / SMTP_APP_PASSWORD. Copy {PROJECT_ROOT / '.env.example'} "
                f"to {ENV_PATH} and fill in your credentials. See README.md for how to "
                "generate a Gmail App Password."
            )

        self.sender_address = username
        self._connection = smtplib.SMTP(host, port, timeout=30)
        self._connection.starttls()
        self._connection.login(username, password)

    def send(self, to_address: str, subject: str, body: str, sender_name: str = ""):
        message = MIMEText(body, "plain")
        message["to"] = to_address
        message["subject"] = subject
        if sender_name:
            message["from"] = f"{sender_name} <{self.sender_address}>"
        else:
            message["from"] = self.sender_address

        self._connection.sendmail(
            self.sender_address, [to_address], message.as_string()
        )

    def close(self):
        try:
            self._connection.quit()
        except smtplib.SMTPException:
            pass
