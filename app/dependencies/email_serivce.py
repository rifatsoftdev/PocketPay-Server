import os, smtplib, dotenv
from email.mime.text import MIMEText

from app.constants.colors import AnsiColor



dotenv.load_dotenv()


class EmailSent:
    def __init__(self):
        self.EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
        self.EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
        self.SMTP_SERVER = os.getenv("SMTP_SERVER")
        self.SMTP_PORT = int(os.getenv("SMTP_PORT"))

        # print(f"{self.EMAIL_ADDRESS} {self.EMAIL_PASSWORD} {self.SMTP_SERVER} {self.SMTP_PORT}")

    # Send OTP via Email
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str
    ) -> bool:
        msg = MIMEText(body, 'html')
        msg['Subject'] = subject
        msg['From'] = self.EMAIL_ADDRESS
        msg['To'] = to_email

        try:
            with smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT) as server:
                server.starttls()
                server.login(self.EMAIL_ADDRESS, self.EMAIL_PASSWORD)
                server.sendmail(self.EMAIL_ADDRESS, to_email, msg.as_string())
            return True
        except Exception as e:
            print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
            return False