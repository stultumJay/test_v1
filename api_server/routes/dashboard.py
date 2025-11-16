from flask import Blueprint, jsonify
from models.user import User
from models.product import Product
from models.sale import Sale

bp = Blueprint('dashboard', __name__)

@bp.route('/admin', methods=['GET'])
def admin_dashboard():
    """GET /api/v1/dashboard/admin"""
    return jsonify({
        'total_users': User.query.count(),
        'total_products': Product.query.count(),
        'total_sales': Sale.query.count()
    }), 200

@bp.route('/manager', methods=['GET'])
def manager_dashboard():
    """GET /api/v1/dashboard/manager"""
    low_stock = Product.query.filter(Product.stock_level < Product.min_stock_level).count()
    expiring = Product.query.filter(Product.expiration_date.isnot(None)).count()
    return jsonify({
        'low_stock_count': low_stock,
        'expiring_count': expiring
    }), 200

@bp.route('/retailer/<int:user_id>', methods=['GET'])
def retailer_dashboard(user_id):
    """GET /api/v1/dashboard/retailer/<id>"""
    from models.retailer_metrics import RetailerMetrics
    m = RetailerMetrics.query.filter_by(retailer_id=user_id).first()
    return jsonify(m.to_dict() if m else {}), 200
