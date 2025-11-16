from flask import Blueprint, request, jsonify
from core.sales_manager import SalesManager
from models.sale import Sale
from app import db

bp = Blueprint('sales', __name__)

@bp.route('', methods=['POST'])
def record_sale():
    """POST /api/v1/sales - Record atomic sale"""
    data = request.get_json() or {}
    retailer_id = data.get('retailer_id')
    items = data.get('items')
    total_amount = data.get('total_amount')
    
    if not retailer_id or not items or total_amount is None:
        return jsonify({"error": "retailer_id, items, total_amount required"}), 400
    
    sale, err = SalesManager.record_atomic_sale(retailer_id, items, total_amount)
    if err:
        return jsonify({"error": err}), 400
    
    return jsonify(sale.to_dict()), 201

@bp.route('/<int:sale_id>', methods=['DELETE'])
def undo_sale(sale_id):
    """DELETE /api/v1/sales/<id> - Undo sale (restore stock)"""
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({"error": "Sale not found"}), 404
    
    # Restore stock
    import json
    from models.product import Product
    from models.retailer_metrics import RetailerMetrics
    
    try:
        items = json.loads(sale.sale_items_json)
        for it in items:
            pid = it.get('product_id')
            qty = int(it.get('quantity', 0))
            p = Product.query.get(pid)
            if p:
                p.stock_level += qty
        
        # Adjust metrics
        metrics = RetailerMetrics.query.filter_by(retailer_id=sale.retailer_id).first()
        if metrics:
            metrics.daily_quota_usd = max(0.0, (metrics.daily_quota_usd or 0.0) - (sale.total_amount or 0.0))
        
        db.session.delete(sale)
        db.session.commit()
        return jsonify({"message": "Sale undone"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/reports', methods=['GET'])
def sales_reports():
    """GET /api/v1/sales/reports?start=&end="""
    start = request.args.get('start')
    end = request.args.get('end')
    
    from dateutil import parser
    sd = parser.parse(start) if start else None
    ed = parser.parse(end) if end else None
    
    report = SalesManager.get_sales_report(sd, ed)
    return jsonify(report), 200
