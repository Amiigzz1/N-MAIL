from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import threading
import time
from datetime import datetime

from database import DatabaseManager
from email_generator import TempEmailGenerator
from email_sender import EmailSender
from smtp_server import SMTPServer

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend/static')
CORS(app)

# إعداد قاعدة البيانات والخدمات
db_manager = DatabaseManager()
email_generator = TempEmailGenerator()

# بدء خادم SMTP في thread منفصل
smtp_server = SMTPServer()
smtp_server.start()

# إعداد email_sender مع المنفذ الصحيح
email_sender = EmailSender(smtp_port=smtp_server.port)

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html')

@app.route('/api/generate-email', methods=['POST'])
def generate_email():
    """API لتوليد بريد إلكتروني مؤقت جديد"""
    try:
        data = request.get_json() or {}
        method = data.get('method', 'random')
        prefix = data.get('prefix', '')
        
        # توليد بريد إلكتروني جديد
        if method == 'word_based':
            new_email = email_generator.generate_word_based_email()
        elif method == 'timestamped':
            new_email = email_generator.generate_timestamped_email()
        elif method == 'custom' and prefix:
            new_email = email_generator.generate_custom_email(prefix=prefix)
        else:
            new_email = email_generator.generate_random_email()
        
        # إنشاء الحساب في قاعدة البيانات
        account_id = db_manager.create_temp_account(new_email)
        
        if account_id:
            # إرسال رسالة ترحيب
            email_sender.send_welcome_email(new_email)
            
            return jsonify({
                'success': True,
                'email': new_email,
                'account_id': account_id,
                'message': 'تم إنشاء البريد الإلكتروني المؤقت بنجاح'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'فشل في إنشاء البريد الإلكتروني'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500

@app.route('/api/emails/<email_address>', methods=['GET'])
def get_emails(email_address):
    """API للحصول على رسائل حساب معين"""
    try:
        # التحقق من وجود الحساب
        account = db_manager.get_temp_account(email_address)
        if not account:
            return jsonify({
                'success': False,
                'message': 'الحساب غير موجود أو منتهي الصلاحية'
            }), 404
        
        # الحصول على الرسائل
        emails = db_manager.get_emails(account['id'])
        
        return jsonify({
            'success': True,
            'emails': emails,
            'account': {
                'email': account['email'],
                'created_at': account['created_at'],
                'expires_at': account['expires_at']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500

@app.route('/api/email/<int:email_id>/<email_address>', methods=['GET'])
def get_email_details(email_id, email_address):
    """API للحصول على تفاصيل رسالة محددة"""
    try:
        # التحقق من وجود الحساب
        account = db_manager.get_temp_account(email_address)
        if not account:
            return jsonify({
                'success': False,
                'message': 'الحساب غير موجود أو منتهي الصلاحية'
            }), 404
        
        # الحصول على تفاصيل الرسالة
        email_details = db_manager.get_email(email_id, account['id'])
        if not email_details:
            return jsonify({
                'success': False,
                'message': 'الرسالة غير موجودة'
            }), 404
        
        # تحديد الرسالة كمقروءة
        db_manager.mark_email_as_read(email_id)
        
        return jsonify({
            'success': True,
            'email': email_details
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500

@app.route('/api/send-email', methods=['POST'])
def send_email():
    """API لإرسال رسالة إلكترونية"""
    try:
        data = request.get_json()
        
        sender = data.get('sender')
        recipient = data.get('recipient')
        subject = data.get('subject', 'No Subject')
        body = data.get('body', '')
        html_body = data.get('html_body')
        
        if not sender or not recipient:
            return jsonify({
                'success': False,
                'message': 'يجب تحديد المرسل والمستلم'
            }), 400
        
        # إرسال الرسالة
        success = email_sender.send_email(sender, recipient, subject, body, html_body)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'تم إرسال الرسالة بنجاح'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'فشل في إرسال الرسالة'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500

@app.route('/api/domains', methods=['GET'])
def get_domains():
    """API للحصول على النطاقات المتاحة"""
    try:
        domains = email_generator.get_available_domains()
        return jsonify({
            'success': True,
            'domains': domains
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500

@app.route('/api/cleanup', methods=['POST'])
def cleanup_database():
    """API لتنظيف قاعدة البيانات"""
    try:
        db_manager.cleanup_database()
        return jsonify({
            'success': True,
            'message': 'تم تنظيف قاعدة البيانات بنجاح'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 500

# تنظيف دوري لقاعدة البيانات
@app.route('/api/server-info', methods=['GET'])
def get_server_info():
    """API للحصول على معلومات الخادم"""
    return jsonify({
        'smtp_host': smtp_server.host,
        'smtp_port': smtp_server.port,
        'web_host': '0.0.0.0',
        'web_port': 5000,
        'status': 'running'
    })

def periodic_cleanup():
    """تنظيف دوري لقاعدة البيانات كل ساعة"""
    while True:
        time.sleep(3600)  # انتظار ساعة واحدة
        try:
            db_manager.cleanup_database()
            print("تم تنظيف قاعدة البيانات بنجاح")
        except Exception as e:
            print(f"خطأ في تنظيف قاعدة البيانات: {str(e)}")

# بدء thread التنظيف الدوري
cleanup_thread = threading.Thread(target=periodic_cleanup)
cleanup_thread.daemon = True
cleanup_thread.start()

if __name__ == '__main__':
    print("بدء تشغيل خادم Temp Mail...")
    print(f"SMTP Server: {smtp_server.host}:{smtp_server.port}")
    print("Web Server: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
