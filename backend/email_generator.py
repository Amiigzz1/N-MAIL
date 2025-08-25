import random
import string
from datetime import datetime

class TempEmailGenerator:
    """مولد عناوين البريد الإلكتروني المؤقت"""
    
    def __init__(self):
        self.domains = [
            "tempmail.local",
            "temp.local", 
            "disposable.local",
            "10min.local",
            "throwaway.local"
        ]
        
        self.adjectives = [
            "quick", "fast", "temp", "rapid", "swift", "brief", "short",
            "instant", "flash", "speedy", "hasty", "urgent", "express"
        ]
        
        self.nouns = [
            "mail", "email", "message", "letter", "post", "note", 
            "inbox", "box", "account", "address", "user", "temp"
        ]
    
    def generate_random_string(self, length=8):
        """توليد نص عشوائي"""
        letters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(letters) for _ in range(length))
    
    def generate_word_based_email(self):
        """توليد بريد إلكتروني بناءً على كلمات"""
        adjective = random.choice(self.adjectives)
        noun = random.choice(self.nouns)
        number = random.randint(100, 9999)
        domain = random.choice(self.domains)
        
        username = f"{adjective}{noun}{number}"
        return f"{username}@{domain}"
    
    def generate_random_email(self, length=10):
        """توليد بريد إلكتروني عشوائي"""
        username = self.generate_random_string(length)
        domain = random.choice(self.domains)
        return f"{username}@{domain}"
    
    def generate_timestamped_email(self):
        """توليد بريد إلكتروني يحتوي على الوقت"""
        timestamp = datetime.now().strftime("%H%M%S")
        random_part = self.generate_random_string(5)
        domain = random.choice(self.domains)
        
        username = f"temp{timestamp}{random_part}"
        return f"{username}@{domain}"
    
    def generate_custom_email(self, prefix="", suffix=""):
        """توليد بريد إلكتروني مخصص"""
        if not prefix:
            prefix = "temp"
        
        middle = self.generate_random_string(6)
        domain = random.choice(self.domains)
        
        if suffix:
            username = f"{prefix}{middle}{suffix}"
        else:
            username = f"{prefix}{middle}"
            
        return f"{username}@{domain}"
    
    def generate_multiple_emails(self, count=5, method="random"):
        """توليد عدة عناوين بريد إلكتروني"""
        emails = []
        
        for _ in range(count):
            if method == "random":
                email = self.generate_random_email()
            elif method == "word_based":
                email = self.generate_word_based_email()
            elif method == "timestamped":
                email = self.generate_timestamped_email()
            else:
                email = self.generate_random_email()
            
            emails.append(email)
        
        return emails
    
    def is_valid_temp_domain(self, email):
        """التحقق من أن النطاق صالح للبريد المؤقت"""
        if "@" not in email:
            return False
        
        domain = email.split("@")[1]
        return domain in self.domains
    
    def get_available_domains(self):
        """الحصول على قائمة النطاقات المتاحة"""
        return self.domains.copy()

# للاختبار
if __name__ == "__main__":
    generator = TempEmailGenerator()
    
    print("عناوين بريد إلكتروني عشوائية:")
    for i in range(5):
        print(f"{i+1}. {generator.generate_random_email()}")
    
    print("\nعناوين بريد إلكتروني بناءً على كلمات:")
    for i in range(5):
        print(f"{i+1}. {generator.generate_word_based_email()}")
    
    print("\nعناوين بريد إلكتروني بالوقت:")
    for i in range(3):
        print(f"{i+1}. {generator.generate_timestamped_email()}")
    
    print(f"\nالنطاقات المتاحة: {generator.get_available_domains()}")
