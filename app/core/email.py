import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_otp_email(to_email: str, otp: str) -> bool:
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = "Your Password Reset OTP — Team Task Manager"

        html_content = f"""
        <html>
            <body>
                <h2>Password Reset OTP</h2>
                <p>Your OTP is: <strong>{otp}</strong></p>
                <p>This OTP is valid for 10 minutes.</p>
                <p>If you did not request this, please ignore this email.</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        logging.error(f"Failed to send OTP email: {e}")
        return False
