from flask import Blueprint, jsonify
from models.retailer_metrics import RetailerMetrics

bp = Blueprint('metrics', __name__)

@bp.route('/<int:user_id>', methods=['GET'])
def retailer_metrics(user_id):
    """GET /api/v1/retailer/<id>"""
    m = RetailerMetrics.query.filter_by(retailer_id=user_id).first()
    if not m:
        return jsonify({"error": "Metrics not found"}), 404
    return jsonify(m.to_dict()), 200

@bp.route('/leaderboard', methods=['GET'])
def leaderboard():
    """GET /api/v1/retailer/leaderboard"""
    top = RetailerMetrics.query.order_by(RetailerMetrics.daily_quota_usd.desc()).limit(10).all()
    return jsonify([m.to_dict() for m in top]), 200