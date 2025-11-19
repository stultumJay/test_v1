from flask import Blueprint, request, jsonify
from app import db
from models.product import Product
from models.category import Category
from utils.validators import validate_product_data, validate_or_400
from core.activity_logger import ActivityLogger  
import base64

bp = Blueprint('products', __name__)

@bp.route('', methods=['GET'])
def list_products():
    """GET /api/v1/products?category_id=&search=&page=&per_page="""
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search')
    include_image = request.args.get('include_image', 'false').lower() == 'true'
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(per_page, 100)  # Max 100 per page
    
    q = Product.query
    if category_id:
        q = q.filter(Product.category_id == category_id)
    if search:
        q = q.filter(Product.name.ilike(f"%{search}%"))
    
    # Execute with pagination
    total = q.count()
    prods = q.offset((page - 1) * per_page).limit(per_page).all()
    
    return jsonify({
        'products': [p.to_dict(include_image=include_image) for p in prods],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }), 200

@bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """GET /api/v1/products/<id>"""
    p = Product.query.get(product_id)
    if not p:
        return jsonify({"error": "Product not found"}), 404
    
    include_image = request.args.get('include_image', 'false').lower() == 'true'
    return jsonify(p.to_dict(include_image=include_image)), 200

@bp.route('', methods=['POST'])
def create_product():
    """POST /api/v1/products"""
    data = request.get_json() or {}
    
    # Validate input
    error_resp, status = validate_or_400(validate_product_data, data, is_update=False)
    if error_resp:
        return error_resp, status
    
    # Verify category exists if provided
    if data.get('category_id'):
        if not Category.query.get(data['category_id']):
            return jsonify({"error": "Category not found"}), 404
    
    # Handle image Base64
    image_blob = None
    if data.get('image_base64'):
        try:
            image_blob = base64.b64decode(data['image_base64'])
        except Exception:
            return jsonify({"error": "Invalid image_base64"}), 400
    
    try:
        p = Product(
            name=data['name'],
            brand=data.get('brand'),
            price=float(data['price']),
            category_id=data.get('category_id'),
            stock_level=int(data.get('stock_level', 0)),
            min_stock_level=int(data.get('min_stock_level', 10)),
            expiration_date=data.get('expiration_date'),
            image_blob=image_blob
        )
        
        db.session.add(p)
        db.session.commit()
        return jsonify(p.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """PUT /api/v1/products/<id>"""
    data = request.get_json() or {}
    p = Product.query.get(product_id)
    if not p:
        return jsonify({"error": "Product not found"}), 404
    
    # Validate input
    error_resp, status = validate_or_400(validate_product_data, data, is_update=True)
    if error_resp:
        return error_resp, status
    
    # Verify category exists if being updated
    if 'category_id' in data and data['category_id']:
        if not Category.query.get(data['category_id']):
            return jsonify({"error": "Category not found"}), 404
    
    try:
        if 'name' in data:
            p.name = data['name']
        if 'brand' in data:
            p.brand = data['brand']
        if 'price' in data:
            p.price = float(data['price'])
        if 'stock_level' in data:
            p.stock_level = int(data['stock_level'])
        if 'min_stock_level' in data:
            p.min_stock_level = int(data['min_stock_level'])
        if 'expiration_date' in data:
            p.expiration_date = data['expiration_date']
        if 'category_id' in data:
            p.category_id = data['category_id']
        if 'image_base64' in data:
            try:
                p.image_blob = base64.b64decode(data['image_base64']) if data['image_base64'] else None
            except Exception:
                return jsonify({"error": "Invalid image_base64"}), 400
        
        db.session.commit()
        return jsonify(p.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/<int:product_id>', methods=['DELETE'])  
def delete_product(product_id):  
    product = Product.query.get(product_id)  
    if not product:  
        return jsonify({"error": "Product not found"}), 404  
      
    # Log the deletion  
    ActivityLogger.log_product_action(  
        product_id=product_id,  
        user_id=None,  # No user in open API  
        action_type="DELETE",  
        notes=f"Product '{product.name}' deleted via API",  
        source="API"  
    )  
      
    db.session.delete(product)  
    db.session.commit()  
      
    return jsonify({"message": "Product deleted"}), 200