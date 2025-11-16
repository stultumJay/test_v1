from flask import Blueprint, request, jsonify
from models.product_log import ProductLog
from models.product import Product
from models.api_activity_log import APIActivityLog
from app import db

bp = Blueprint('logs', __name__)

@bp.route('/product/<int:product_id>', methods=['GET'])
def logs_for_product(product_id):
    """GET /api/v1/log/product/<id>"""
    logs = ProductLog.query.filter_by(product_id=product_id).order_by(ProductLog.log_time.desc()).all()
    return jsonify([l.to_dict() for l in logs]), 200

@bp.route('/user/<int:user_id>', methods=['GET'])
def logs_for_user(user_id):
    """GET /api/v1/log/user/<id>"""
    logs = ProductLog.query.filter_by(user_id=user_id).order_by(ProductLog.log_time.desc()).all()
    return jsonify([l.to_dict() for l in logs]), 200

@bp.route('/dispose', methods=['POST'])
def dispose_product():
    """POST /api/v1/log/dispose - Atomic disposal"""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    user_id = data.get('user_id')
    qty = int(data.get('quantity', 0))
    notes = data.get('notes')
    
    if not product_id or not user_id or qty <= 0:
        return jsonify({"error": "product_id, user_id, quantity required"}), 400
    
    try:
        p = Product.query.get(product_id)
        if not p:
            return jsonify({"error": "Product not found"}), 404
        
        p.stock_level = max(0, p.stock_level - qty)
        
        log = ProductLog(
            product_id=product_id,
            user_id=user_id,
            action_type='Dispose',
            notes=notes
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(log.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route('/desktop', methods=['POST'])
def log_desktop_action():
    """
    POST /api/v1/log/desktop - Log desktop application activity
    Receives activity logs from desktop app for centralized audit
    """
    data = request.get_json() or {}
    
    # Extract fields
    user_id = data.get('user_id')
    action_type = data.get('action_type')
    target_entity = data.get('target_entity')
    
    if not action_type:
        return jsonify({"error": "action_type required"}), 400
    
    try:
        # Create activity log entry
        log = APIActivityLog(
            method='DESKTOP',  # Special method for desktop actions
            path='/desktop/action',
            json_payload=str(data),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            status_code=200,
            target_entity=target_entity,
            source='Desktop App',
            user_id=user_id
        )
        
        db.session.add(log)
        db.session.commit()
        
        return jsonify({"message": "Desktop action logged", "log_id": log.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500