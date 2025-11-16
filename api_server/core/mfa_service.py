"""  
MFA Service for StockaDoodle  
Handles email-based two-factor authentication for admin/manager roles  
"""  
  
import random  
import string  
import smtplib  
from datetime import datetime, timedelta  
from typing import Dict, Optional  
  
class MFAService:  
    """Singleton service for MFA code generation and verification"""  
    _instance = None  
    _active_mfa_codes: Dict[str, Dict] = {}  # {username: {'code': str, 'expiry': datetime}}  
      
    def __new__(cls):  
        if cls._instance is None:  
            cls._instance = super(MFAService, cls).__new__(cls)  
        return cls._instance  
      
    def generate_mfa_code(self, length: int = 6) -> str:  
        """Generate random alphanumeric MFA code"""  
        characters = string.ascii_uppercase + string.digits  
        return ''.join(random.choice(characters) for _ in range(length))  
      
    def _send_email(self, receiver_email: str, subject: str, body: str,   
                    smtp_server: str, smtp_port: int,   
                    smtp_username: str, smtp_password: str) -> bool:  
        """Send email via SMTP"""  
        sender_email = smtp_username  
          
        # Prepare message  
        message = f"From: {sender_email}\nTo: {receiver_email}\nSubject: {subject}\n\n{body}"  
          
        try:  
            server = smtplib.SMTP(smtp_server, smtp_port)  
            server.starttls()  
            server.login(smtp_username, smtp_password)  
            server.sendmail(sender_email, receiver_email, message)  
            server.quit()  
            print(f"MFA email sent to {receiver_email}")  
            return True  
        except Exception as e:  
            print(f"Failed to send MFA email: {e}")  
            return False  
      
    def send_mfa_code(self, user_email: str, username: str,   
                      smtp_config: Dict) -> bool:  
        """  
        Generate and send MFA code to user's email  
          
        Args:  
            user_email: Recipient email address  
            username: Username for personalization  
            smtp_config: Dict with keys: server, port, username, password,   
                        code_length, expiry_minutes  
        """  
        code = self.generate_mfa_code(smtp_config.get('code_length', 6))  
        expiry_minutes = smtp_config.get('expiry_minutes', 5)  
        expiry_time = datetime.now() + timedelta(minutes=expiry_minutes)  
          
        # Store code  
        self._active_mfa_codes[username] = {  
            'code': code,  
            'expiry': expiry_time  
        }  
          
        # Email content  
        subject = "Your StockaDoodle Login Code"  
        body = f"""Dear {username},  
  
Your Multi-Factor Authentication (MFA) code for logging into StockaDoodle is:  
  
{code}  
  
This code is valid for {expiry_minutes} minutes. Please enter it to complete your login.  
  
If you did not request this code, please ignore this email.  
  
Sincerely,  
StockaDoodle Team  
"""  
          
        return self._send_email(  
            receiver_email=user_email,  
            subject=subject,  
            body=body,  
            smtp_server=smtp_config['server'],  
            smtp_port=smtp_config['port'],  
            smtp_username=smtp_config['username'],  
            smtp_password=smtp_config['password']  
        )  
      
    def verify_mfa_code(self, username: str, entered_code: str) -> bool:  
        """Verify MFA code for username"""  
        if username not in self._active_mfa_codes:  
            print(f"No MFA code for {username}")  
            return False  
          
        stored_info = self._active_mfa_codes[username]  
        stored_code = stored_info['code']  
        expiry_time = stored_info['expiry']  
          
        # Check expiry  
        if datetime.now() > expiry_time:  
            del self._active_mfa_codes[username]  
            print(f"MFA code expired for {username}")  
            return False  
          
        # Verify code  
        if entered_code == stored_code:  
            del self._active_mfa_codes[username]  
            print(f"MFA code verified for {username}")  
            return True  
        else:  
            print(f"Invalid MFA code for {username}")  
            return False