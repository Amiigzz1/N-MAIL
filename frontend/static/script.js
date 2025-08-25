class TempMailApp {
    constructor() {
        this.currentEmail = null;
        this.currentAccount = null;
        this.refreshInterval = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadStoredEmail();
        this.loadServerInfo();
    }

    bindEvents() {
        // أحداث توليد البريد الإلكتروني
        document.getElementById('generation-method').addEventListener('change', (e) => {
            this.toggleCustomPrefix(e.target.value === 'custom');
        });

        document.getElementById('generate-btn').addEventListener('click', () => {
            this.generateEmail();
        });

        // أحداث البريد الحالي
        document.getElementById('copy-email-btn').addEventListener('click', () => {
            this.copyEmail();
        });

        document.getElementById('refresh-emails-btn').addEventListener('click', () => {
            this.refreshEmails();
        });

        document.getElementById('new-email-btn').addEventListener('click', () => {
            this.newEmail();
        });

        // أحداث النافذة المنبثقة
        document.getElementById('close-modal-btn').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('email-modal').addEventListener('click', (e) => {
            if (e.target.id === 'email-modal') {
                this.closeModal();
            }
        });

        // أحداث إرسال الرسائل
        document.getElementById('send-email-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendEmail();
        });

        // أحداث لوحة المفاتيح
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    toggleCustomPrefix(show) {
        const customPrefixGroup = document.getElementById('custom-prefix-group');
        customPrefixGroup.style.display = show ? 'block' : 'none';
    }

    async generateEmail() {
        const method = document.getElementById('generation-method').value;
        const prefix = document.getElementById('custom-prefix').value;

        const requestData = { method };
        if (method === 'custom' && prefix) {
            requestData.prefix = prefix;
        }

        this.showLoading();

        try {
            const response = await fetch('/api/generate-email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            const data = await response.json();

            if (data.success) {
                this.currentEmail = data.email;
                this.currentAccount = { id: data.account_id };
                this.saveEmailToStorage();
                this.displayCurrentEmail();
                this.startAutoRefresh();
                this.showNotification('تم إنشاء البريد الإلكتروني بنجاح!', 'success');
            } else {
                this.showNotification(data.message || 'فشل في إنشاء البريد الإلكتروني', 'error');
            }
        } catch (error) {
            console.error('Error generating email:', error);
            this.showNotification('حدث خطأ أثناء إنشاء البريد الإلكتروني', 'error');
        } finally {
            this.hideLoading();
        }
    }

    displayCurrentEmail() {
        if (!this.currentEmail) return;

        document.getElementById('current-email-address').textContent = this.currentEmail;
        document.getElementById('current-email-section').style.display = 'block';
        document.getElementById('email-list-section').style.display = 'block';

        // إخفاء قسم التوليد
        document.querySelector('.email-generator').style.display = 'none';

        this.refreshEmails();
    }

    async refreshEmails() {
        if (!this.currentEmail) return;

        try {
            const response = await fetch(`/api/emails/${encodeURIComponent(this.currentEmail)}`);
            const data = await response.json();

            if (data.success) {
                this.currentAccount = data.account;
                this.displayEmails(data.emails);
                this.updateAccountInfo();
            } else {
                this.showNotification(data.message || 'فشل في تحديث الرسائل', 'error');
            }
        } catch (error) {
            console.error('Error refreshing emails:', error);
            this.showNotification('حدث خطأ أثناء تحديث الرسائل', 'error');
        }
    }

    displayEmails(emails) {
        const container = document.getElementById('emails-container');

        if (emails.length === 0) {
            container.innerHTML = `
                <div class="no-emails">
                    <i class="fas fa-inbox"></i>
                    <p>لا توجد رسائل بعد</p>
                    <small>سيتم عرض الرسائل الجديدة هنا تلقائياً</small>
                </div>
            `;
            return;
        }

        container.innerHTML = emails.map(email => `
            <div class="email-item ${email.is_read ? '' : 'unread'}" onclick="tempMailApp.openEmail(${email.id})">
                <div class="email-header">
                    <span class="email-sender">${this.escapeHtml(email.sender)}</span>
                    <span class="email-date">${this.formatDate(email.received_at)}</span>
                </div>
                <div class="email-subject">${this.escapeHtml(email.subject || 'بدون موضوع')}</div>
                <div class="email-preview">${this.escapeHtml(this.getEmailPreview(email.body))}</div>
            </div>
        `).join('');
    }

    async openEmail(emailId) {
        this.showLoading();

        try {
            const response = await fetch(`/api/email/${emailId}/${encodeURIComponent(this.currentEmail)}`);
            const data = await response.json();

            if (data.success) {
                this.displayEmailModal(data.email);
            } else {
                this.showNotification(data.message || 'فشل في فتح الرسالة', 'error');
            }
        } catch (error) {
            console.error('Error opening email:', error);
            this.showNotification('حدث خطأ أثناء فتح الرسالة', 'error');
        } finally {
            this.hideLoading();
        }
    }

    displayEmailModal(email) {
        document.getElementById('email-subject').textContent = email.subject || 'بدون موضوع';
        document.getElementById('email-sender').textContent = email.sender;
        document.getElementById('email-recipient').textContent = email.recipient;
        document.getElementById('email-date').textContent = this.formatDate(email.received_at);

        // عرض محتوى الرسالة
        const bodyElement = document.getElementById('email-body');
        if (email.html_body) {
            bodyElement.innerHTML = email.html_body;
        } else {
            bodyElement.innerHTML = `<pre>${this.escapeHtml(email.body)}</pre>`;
        }

        document.getElementById('email-modal').style.display = 'block';

        // تحديث قائمة الرسائل لإظهار أن الرسالة تم قراءتها
        setTimeout(() => this.refreshEmails(), 500);
    }

    closeModal() {
        document.getElementById('email-modal').style.display = 'none';
    }

    async sendEmail() {
        const sender = document.getElementById('sender-email').value;
        const recipient = document.getElementById('recipient-email').value;
        const subject = document.getElementById('email-subject-input').value;
        const body = document.getElementById('email-body-input').value;

        if (!sender || !recipient || !subject || !body) {
            this.showNotification('يرجى ملء جميع الحقول المطلوبة', 'error');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch('/api/send-email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sender,
                    recipient,
                    subject,
                    body
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('تم إرسال الرسالة بنجاح!', 'success');
                document.getElementById('send-email-form').reset();
            } else {
                this.showNotification(data.message || 'فشل في إرسال الرسالة', 'error');
            }
        } catch (error) {
            console.error('Error sending email:', error);
            this.showNotification('حدث خطأ أثناء إرسال الرسالة', 'error');
        } finally {
            this.hideLoading();
        }
    }

    copyEmail() {
        if (!this.currentEmail) return;

        navigator.clipboard.writeText(this.currentEmail).then(() => {
            this.showNotification('تم نسخ البريد الإلكتروني!', 'success');
        }).catch(() => {
            // fallback للمتصفحات القديمة
            const textArea = document.createElement('textarea');
            textArea.value = this.currentEmail;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            this.showNotification('تم نسخ البريد الإلكتروني!', 'success');
        });
    }

    newEmail() {
        this.currentEmail = null;
        this.currentAccount = null;
        this.clearStoredEmail();
        this.stopAutoRefresh();

        document.getElementById('current-email-section').style.display = 'none';
        document.getElementById('email-list-section').style.display = 'none';
        document.querySelector('.email-generator').style.display = 'block';
    }

    updateAccountInfo() {
        if (!this.currentAccount) return;

        if (this.currentAccount.created_at) {
            document.getElementById('created-at').textContent = this.formatDate(this.currentAccount.created_at);
        }
        if (this.currentAccount.expires_at) {
            document.getElementById('expires-at').textContent = this.formatDate(this.currentAccount.expires_at);
        }
    }

    startAutoRefresh() {
        this.stopAutoRefresh();
        this.refreshInterval = setInterval(() => {
            this.refreshEmails();
        }, 10000); // تحديث كل 10 ثوان
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    saveEmailToStorage() {
        if (this.currentEmail) {
            localStorage.setItem('tempmail_current_email', this.currentEmail);
        }
    }

    loadStoredEmail() {
        const storedEmail = localStorage.getItem('tempmail_current_email');
        if (storedEmail) {
            this.currentEmail = storedEmail;
            this.displayCurrentEmail();
            this.startAutoRefresh();
        }
    }

    clearStoredEmail() {
        localStorage.removeItem('tempmail_current_email');
    }

    showLoading() {
        document.getElementById('loading').style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }

    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.classList.add('show');

        setTimeout(() => {
            notification.classList.remove('show');
        }, 5000);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (minutes < 1) {
            return 'الآن';
        } else if (minutes < 60) {
            return `منذ ${minutes} دقيقة`;
        } else if (hours < 24) {
            return `منذ ${hours} ساعة`;
        } else if (days < 7) {
            return `منذ ${days} يوم`;
        } else {
            return date.toLocaleDateString('ar-SA', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }

    getEmailPreview(body, maxLength = 100) {
        if (!body) return 'لا يوجد محتوى';
        return body.length > maxLength ? body.substring(0, maxLength) + '...' : body;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async loadServerInfo() {
        try {
            const response = await fetch('/api/server-info');
            const data = await response.json();
            
            if (data) {
                // عرض معلومات الخادم في الواجهة
                const serverInfo = document.createElement('div');
                serverInfo.className = 'server-info';
                serverInfo.innerHTML = `
                    <small class="text-muted">
                        SMTP Server: ${data.smtp_host}:${data.smtp_port} | 
                        Status: ${data.status}
                    </small>
                `;
                
                const container = document.querySelector('.container');
                if (container) {
                    container.appendChild(serverInfo);
                }
            }
        } catch (error) {
            console.log('Could not load server info:', error);
        }
    }
}

// تشغيل التطبيق عند تحميل الصفحة
let tempMailApp;
document.addEventListener('DOMContentLoaded', () => {
    tempMailApp = new TempMailApp();
});
