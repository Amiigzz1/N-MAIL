import asyncio
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP as Server
import threading
import logging
import socket
from database import DatabaseManager

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TempMailSMTPHandler:
    """معالج خادم SMTP لاستقبال الرسائل"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        """التحقق من وجود المستلم"""
        logger.info(f"Checking recipient: {address}")
        
        # التحقق من وجود الحساب المؤقت
        account = self.db_manager.get_temp_account(address)
        if account:
            envelope.rcpt_tos.append(address)
            return '250 OK'
        else:
            logger.warning(f"Recipient not found: {address}")
            return '550 No such user here'
    
    async def handle_DATA(self, server, session, envelope):
        """معالجة بيانات الرسالة"""
        logger.info(f"Receiving message from {envelope.mail_from} to {envelope.rcpt_tos}")
        
        try:
            # تحليل الرسالة
            message = email.message_from_bytes(envelope.content)
            
            # استخراج تفاصيل الرسالة
            sender = envelope.mail_from
            subject = message.get('Subject', 'No Subject')
            
            # استخراج محتوى الرسالة
            body = ""
            html_body = None
            
            if message.is_multipart():
                for part in message.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    elif content_type == "text/html":
                        html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                body = message.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            # حفظ الرسالة لكل مستلم
            for recipient in envelope.rcpt_tos:
                account = self.db_manager.get_temp_account(recipient)
                if account:
                    email_id = self.db_manager.save_email(
                        account['id'], sender, recipient, subject, body, html_body
                    )
                    logger.info(f"Email saved with ID: {email_id}")
            
            return '250 Message accepted for delivery'
            
        except Exception as e:
            logger.error(f"Error processing email: {str(e)}")
            return '451 Error processing message'

class SMTPServer:
    """خادم SMTP لاستقبال الرسائل"""
    
    def __init__(self, host='localhost', port=1025):
        self.host = host
        self.port = self.find_available_port(port)
        self.db_manager = DatabaseManager()
        self.handler = TempMailSMTPHandler(self.db_manager)
        self.controller = None
        self.thread = None
    
    def find_available_port(self, start_port):
        """العثور على منفذ متاح"""
        port = start_port
        while port < start_port + 100:  # البحث في 100 منفذ
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host, port))
                    return port
            except OSError:
                port += 1
        raise RuntimeError("No available port found")
    
    def start(self):
        """بدء خادم SMTP"""
        logger.info(f"Starting SMTP server on {self.host}:{self.port}")
        
        try:
            self.controller = Controller(
                self.handler,
                hostname=self.host,
                port=self.port
            )
            
            # تشغيل الخادم في thread منفصل
            self.thread = threading.Thread(target=self._run_server)
            self.thread.daemon = True
            self.thread.start()
            
            logger.info(f"SMTP server started successfully on port {self.port}")
            
        except Exception as e:
            logger.error(f"Failed to start SMTP server: {str(e)}")
            # محاولة إيجاد منفذ آخر
            self.port = self.find_available_port(self.port + 1)
            logger.info(f"Trying alternative port: {self.port}")
            self.start()
    
    def _run_server(self):
        """تشغيل الخادم"""
        self.controller.start()
    
    def stop(self):
        """إيقاف خادم SMTP"""
        if self.controller:
            self.controller.stop()
            logger.info("SMTP server stopped")

# للاختبار المحلي
if __name__ == "__main__":
    server = SMTPServer()
    server.start()
    
    try:
        # إبقاء الخادم يعمل
        while True:
            asyncio.sleep(1)
    except KeyboardInterrupt:
        server.stop()
