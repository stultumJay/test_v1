from flask import Blueprint, request, jsonify
from core.user_manager import UserManager

bp = Blueprint('users', __name__)

@bp.route('', methods=['GET'])
def list_users():
    """GET /api/v1/users - List all users"""
    users = UserManager.list_users()
    return jsonify([u.to_dict() for u in users]), 200

@bp.route('', methods=['POST'])
def create_user():
    """POST /api/v1/users - Create new user"""
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'Retailer')
    email = data.get('email')
    
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    
    user, err = UserManager.create_user(username, password, role, email)
    if err:
        return jsonify({"error": err}), 400
    
    return jsonify(user.to_dict()), 201

@bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """GET /api/v1/users/<id> - Get user by ID"""
    user = UserManager.get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200

@bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """PUT /api/v1/users/<id> - Update user"""
    data = request.get_json() or {}
    user, err = UserManager.update_user(user_id, **data)
    if err:
        return jsonify({"error": err}), 400
    return jsonify(user.to_dict()), 200

@bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """DELETE /api/v1/users/<id> - Delete user"""
    ok, err = UserManager.delete_user(user_id)
    if not ok:
        return jsonify({"error": err}), 400
    return jsonify({"message": "User deleted"}), 200

@bp.route('/auth/login', methods=['POST'])
def login():
    """POST /api/v1/users/auth/login - Authenticate user"""
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    user = UserManager.authenticate_user(username, password)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    
    return jsonify(user.to_dict()), 200