# api_server/routes/auth.py  
"""  
Authentication routes for MFA  
"""  
  
from flask import Blueprint, request, jsonify  
import os  
from core.mfa_service import MFAService  
from models.user import User  
  
bp = Blueprint('auth', __name__)  
mfa_service = MFAService()  
  
@bp.route('/mfa/send', methods=['POST'])  
def send_mfa_code():  
    """  
    POST /api/v1/auth/mfa/send  
    Send MFA code to user's email  
    Body: {username: str, email: str}  
    """  
    data = request.get_json() or {}  
    username = data.get('username')  
    email = data.get('email')  
      
    if not username or not email:  
        return jsonify({'error': 'Username and email required'}), 400  
      
    # Verify user exists and has admin/manager role  
    user = User.query.filter_by(username=username).first()  
    if not user or user.role not in ['Admin', 'Manager']:  
        return jsonify({'error': 'MFA not required for this user'}), 403  
      
    # SMTP configuration from environment  
    smtp_config = {  
        'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),  
        'port': int(os.getenv('SMTP_PORT', '587')),  
        'username': os.getenv('SMTP_USERNAME'),  
        'password': os.getenv('SMTP_PASSWORD'),  
        'code_length': int(os.getenv('MFA_CODE_LENGTH', '6')),  
        'expiry_minutes': int(os.getenv('MFA_CODE_EXPIRY_MINUTES', '5'))  
    }  
      
    # Validate SMTP credentials  
    if not smtp_config['username'] or not smtp_config['password']:  
        return jsonify({'error': 'SMTP not configured'}), 500  
      
    # Send MFA code  
    success = mfa_service.send_mfa_code(email, username, smtp_config)  
      
    if success:  
        return jsonify({'message': 'MFA code sent', 'expires_in_minutes': smtp_config['expiry_minutes']}), 200  
    else:  
        return jsonify({'error': 'Failed to send MFA code'}), 500  
  
  
@bp.route('/mfa/verify', methods=['POST'])  
def verify_mfa_code():  
    """  
    POST /api/v1/auth/mfa/verify  
    Verify MFA code  
    Body: {username: str, code: str}  
    """  
    data = request.get_json() or {}  
    username = data.get('username')  
    code = data.get('code')  
      
    if not username or not code:  
        return jsonify({'error': 'Username and code required'}), 400  
      
    # Verify code  
    is_valid = mfa_service.verify_mfa_code(username, code)  
      
    if is_valid:  
        return jsonify({'message': 'MFA code verified', 'valid': True}), 200  
    else:  
        return jsonify({'error': 'Invalid or expired code', 'valid': False}), 401