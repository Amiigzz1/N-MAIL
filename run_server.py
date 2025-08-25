#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
N-MAIL - نظام البريد الإلكتروني المؤقت المحلي
Local Temporary Email System

هذا الملف لتشغيل النظام بطريقة محسنة مع معالجة الأخطاء
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

def check_python_version():
    """التحقق من إصدار Python"""
    if sys.version_info < (3, 7):
        print("❌ خطأ: يتطلب Python 3.7 أو أحدث")
        print(f"الإصدار الحالي: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_requirements():
    """تثبيت المتطلبات"""
    print("📦 تثبيت المتطلبات...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ تم تثبيت جميع المتطلبات بنجاح")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في تثبيت المتطلبات: {e}")
        return False

def check_ports():
    """التحقق من توفر المنافذ"""
    import socket
    
    def is_port_available(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return True
            except OSError:
                return False
    
    # التحقق من منفذ Flask
    if not is_port_available(5000):
        print("⚠️  المنفذ 5000 مُستخدم، سيتم استخدام منفذ بديل")
    
    # العثور على منفذ متاح للـ SMTP
    smtp_port = 1025
    while smtp_port < 1125 and not is_port_available(smtp_port):
        smtp_port += 1
    
    print(f"🌐 منفذ الويب: 5000")
    print(f"📧 منفذ SMTP: {smtp_port}")
    return smtp_port

def start_server():
    """بدء تشغيل الخادم"""
    print("\n🚀 بدء تشغيل نظام N-MAIL...")
    print("=" * 50)
    
    # التحقق من Python
    if not check_python_version():
        return False
    
    # تثبيت المتطلبات
    if not install_requirements():
        return False
    
    # التحقق من المنافذ
    smtp_port = check_ports()
    
    # الانتقال إلى مجلد backend
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    print("\n🔗 روابط الوصول:")
    print(f"   الواجهة الرئيسية: http://localhost:5000")
    print(f"   API: http://localhost:5000/api/")
    print(f"   SMTP Server: localhost:{smtp_port}")
    print("\n💡 نصائح:")
    print("   - يمكنك فتح الرابط في المتصفح")
    print("   - استخدم Ctrl+C لإيقاف الخادم")
    print("   - البريد المؤقت صالح لمدة 24 ساعة")
    print("=" * 50)
    
    try:
        # تشغيل التطبيق
        os.environ['SMTP_PORT'] = str(smtp_port)
        subprocess.run([sys.executable, "app.py"], check=True)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  تم إيقاف الخادم بواسطة المستخدم")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ خطأ في تشغيل الخادم: {e}")
        return False
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print("🔷 N-MAIL - نظام البريد الإلكتروني المؤقت المحلي")
    print("   Local Temporary Email System")
    print("   Version 1.0.0\n")
    
    try:
        start_server()
    except Exception as e:
        print(f"❌ خطأ في تشغيل النظام: {e}")
        sys.exit(1)
    
    print("\n👋 شكراً لاستخدام N-MAIL!")

if __name__ == "__main__":
    main()
