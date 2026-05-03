import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Send an email using SMTP configuration from settings.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        html_content (str): HTML content of the email
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(html_content, 'html'))
        
        # Use configurable SMTP settings
        if settings.SMTP_SSL:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            if settings.SMTP_TLS:
                server.starttls()
        
        server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

def send_test_email_to_user() -> bool:
    """
    Send a test email to parthlad0007@gmail.com
    """
    subject = "Test Email from Task Manager"
    html_content = """
    <html>
        <body>
            <h2>Test Email</h2>
            <p>This is a test email sent from your Task Manager application.</p>
            <p>If you received this, the SMTP configuration is working correctly!</p>
        </body>
    </html>
    """
    return send_email("parthlad0007@gmail.com", subject, html_content)

def send_otp_email(to_email: str, otp: str) -> bool:
    subject = "Your Password Reset OTP — Team Task Manager"
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
    return send_email(to_email, subject, html_content)
