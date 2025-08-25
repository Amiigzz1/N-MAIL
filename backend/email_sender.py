import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

class EmailSender:
    """فئة لإرسال الرسائل الإلكترونية"""
    
    def __init__(self, smtp_host='localhost', smtp_port=1025, use_tls=False, username=None, password=None):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.use_tls = use_tls
        self.username = username
        self.password = password
    
    def send_email(self, sender_email, recipient_email, subject, body, html_body=None):
        """إرسال رسالة إلكترونية"""
        try:
            # إنشاء الرسالة
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = sender_email
            message["To"] = recipient_email
            
            # إضافة النص العادي
            text_part = MIMEText(body, "plain", "utf-8")
            message.attach(text_part)
            
            # إضافة HTML إذا كان متوفراً
            if html_body:
                html_part = MIMEText(html_body, "html", "utf-8")
                message.attach(html_part)
            
            # إرسال الرسالة
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                
                if self.username and self.password:
                    server.login(self.username, self.password)
                
                server.send_message(message)
                logger.info(f"Email sent successfully from {sender_email} to {recipient_email}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def send_welcome_email(self, temp_email):
        """إرسال رسالة ترحيب للحساب المؤقت الجديد"""
        subject = "مرحباً بك في Temp Mail"
        body = f"""
مرحباً بك!

تم إنشاء حسابك المؤقت بنجاح: {temp_email}

يمكنك الآن استقبال الرسائل على هذا العنوان.
سيبقى هذا الحساب نشطاً لمدة 24 ساعة.

شكراً لاستخدامك خدمة Temp Mail المحلية.
        """
        
        html_body = f"""
        <html>
        <body>
            <h2>مرحباً بك!</h2>
            <p>تم إنشاء حسابك المؤقت بنجاح: <strong>{temp_email}</strong></p>
            <p>يمكنك الآن استقبال الرسائل على هذا العنوان.</p>
            <p>سيبقى هذا الحساب نشطاً لمدة 24 ساعة.</p>
            <p>شكراً لاستخدامك خدمة Temp Mail المحلية.</p>
        </body>
        </html>
        """
        
        return self.send_email(
            "noreply@tempmail.local",
            temp_email,
            subject,
            body,
            html_body
        )
