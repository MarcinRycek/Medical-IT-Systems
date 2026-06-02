import smtplib
from email.mime.text import MIMEText

SMTP_SERVER = "poczta.interia.pl"
SMTP_PORT = 465
SENDER_EMAIL = "medex@pol.hub.pl"
SENDER_PASSWORD = "MedexPol6767"


def send_email(to_email, subject, body):
    if not to_email:
        return False

    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Błąd podczas wysyłania e-maila: {e}")
        return False