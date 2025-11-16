from flask import Blueprint, request, jsonify
from app import db
from models.category import Category

bp = Blueprint('categories', __name__)

@bp.route('', methods=['GET'])
def list_categories():
    """GET /api/v1/categories"""
    cats = Category.query.all()
    return jsonify([c.to_dict() for c in cats]), 200

@bp.route('', methods=['POST'])
def create_category():
    """POST /api/v1/categories"""
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return jsonify({"error": "name required"}), 400
    
    if Category.query.filter_by(name=name).first():
        return jsonify({"error": "Category already exists"}), 400
    
    cat = Category(name=name)
    db.session.add(cat)
    db.session.commit()
    return jsonify(cat.to_dict()), 201

@bp.route('/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    """PUT /api/v1/categories/<id>"""
    data = request.get_json() or {}
    cat = Category.query.get(cat_id)
    if not cat:
        return jsonify({"error": "Category not found"}), 404
    
    if 'name' in data:
        cat.name = data['name']
    
    db.session.commit()
    return jsonify(cat.to_dict()), 200

@bp.route('/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    """DELETE /api/v1/categories/<id>"""
    cat = Category.query.get(cat_id)
    if not cat:
        return jsonify({"error": "Category not found"}), 404
    
    db.session.delete(cat)
    db.session.commit()
    return jsonify({"message": "Category deleted"}), 200