import sqlite3
from datetime import datetime, timedelta
import os

class DatabaseManager:
    def __init__(self, db_path="database/tempmail.db"):
        self.db_path = db_path
        self.ensure_database_exists()
        self.create_tables()
    
    def ensure_database_exists(self):
        """تأكد من وجود مجلد قاعدة البيانات"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self):
        """إنشاء اتصال بقاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_tables(self):
        """إنشاء جداول قاعدة البيانات"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # جدول الحسابات المؤقتة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temp_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # جدول الرسائل
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                temp_account_id INTEGER,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                subject TEXT,
                body TEXT,
                html_body TEXT,
                received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                FOREIGN KEY (temp_account_id) REFERENCES temp_accounts (id)
            )
        ''')
        
        # جدول المرفقات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id INTEGER,
                filename TEXT NOT NULL,
                content_type TEXT,
                data BLOB,
                FOREIGN KEY (email_id) REFERENCES emails (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_temp_account(self, email, password=None, expires_in_hours=24):
        """إنشاء حساب مؤقت جديد"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        try:
            cursor.execute('''
                INSERT INTO temp_accounts (email, password, expires_at)
                VALUES (?, ?, ?)
            ''', (email, password, expires_at))
            
            account_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return account_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def get_temp_account(self, email):
        """الحصول على حساب مؤقت"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM temp_accounts 
            WHERE email = ? AND is_active = 1 AND expires_at > datetime('now')
        ''', (email,))
        
        account = cursor.fetchone()
        conn.close()
        return dict(account) if account else None
    
    def save_email(self, temp_account_id, sender, recipient, subject, body, html_body=None):
        """حفظ رسالة جديدة"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO emails (temp_account_id, sender, recipient, subject, body, html_body)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (temp_account_id, sender, recipient, subject, body, html_body))
        
        email_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return email_id
    
    def get_emails(self, temp_account_id):
        """الحصول على جميع رسائل الحساب المؤقت"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM emails 
            WHERE temp_account_id = ? 
            ORDER BY received_at DESC
        ''', (temp_account_id,))
        
        emails = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return emails
    
    def get_email(self, email_id, temp_account_id):
        """الحصول على رسالة محددة"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM emails 
            WHERE id = ? AND temp_account_id = ?
        ''', (email_id, temp_account_id))
        
        email = cursor.fetchone()
        conn.close()
        return dict(email) if email else None
    
    def mark_email_as_read(self, email_id):
        """تحديد الرسالة كمقروءة"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE emails SET is_read = 1 WHERE id = ?
        ''', (email_id,))
        
        conn.commit()
        conn.close()
    
    def delete_expired_accounts(self):
        """حذف الحسابات المنتهية الصلاحية"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM temp_accounts 
            WHERE expires_at < datetime('now')
        ''')
        
        conn.commit()
        conn.close()
    
    def cleanup_database(self):
        """تنظيف قاعدة البيانات من البيانات القديمة"""
        self.delete_expired_accounts()
