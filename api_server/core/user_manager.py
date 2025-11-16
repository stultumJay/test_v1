# api_server/core/user_manager.py
import hashlib
from app import db
from models.user import User
from models.retailer_metrics import RetailerMetrics

# Simple SHA256 hashing (for demo only). Replace with bcrypt/argon2 in production.
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(stored_hash: str, provided_password: str) -> bool:
    return stored_hash == hash_password(provided_password)

class UserManager:
    @staticmethod
    def create_user(username, password, role='Retailer', profile_pic_blob=None):
        if User.query.filter_by(username=username).first():
            return None, "Username already exists."

        hashed = hash_password(password)
        u = User(username=username, password_hash=hashed, role=role, profile_pic_blob=profile_pic_blob)
        db.session.add(u)
        db.session.flush()  # get id
        if role == 'Retailer':
            metrics = RetailerMetrics(retailer_id=u.id)
            db.session.add(metrics)
        db.session.commit()
        return u, None

    @staticmethod
    def authenticate_user(username, password):
        user = User.query.filter_by(username=username, is_active=True).first()
        if not user:
            return None
        if verify_password(user.password_hash, password):
            return user
        return None

    @staticmethod
    def list_users():
        return User.query.all()

    @staticmethod
    def get_user(user_id):
        return User.query.get(user_id)

    @staticmethod
    def update_user(user_id, **kwargs):
        user = User.query.get(user_id)
        if not user:
            return None, "User not found"
        if 'username' in kwargs:
            user.username = kwargs['username']
        if 'role' in kwargs:
            user.role = kwargs['role']
        if 'is_active' in kwargs:
            user.is_active = bool(kwargs['is_active'])
        if 'password' in kwargs and kwargs['password']:
            user.password_hash = hash_password(kwargs['password'])
        if 'profile_pic_blob' in kwargs:
            user.profile_pic_blob = kwargs['profile_pic_blob']
        db.session.commit()
        return user, None

    @staticmethod
    def delete_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return False, "User not found"
        db.session.delete(user)
        db.session.commit()
        return True, None
