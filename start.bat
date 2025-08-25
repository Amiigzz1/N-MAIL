@echo off
echo ========================================
echo   N-MAIL - نظام البريد الإلكتروني المؤقت
echo ========================================
echo.

echo تحقق من تثبيت Python...
python --version
if %errorlevel% neq 0 (
    echo خطأ: Python غير مثبت!
    echo يرجى تثبيت Python من python.org
    pause
    exit /b 1
)

echo.
echo تثبيت المتطلبات...
pip install -r requirements.txt

echo.
echo بدء تشغيل النظام...
echo خادم الويب: http://localhost:5000
echo خادم SMTP: localhost:1025
echo.
echo اضغط Ctrl+C لإيقاف الخادم
echo.

cd backend
python app.py

pause
