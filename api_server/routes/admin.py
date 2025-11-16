"""
Admin routes for activity logs and system monitoring
Already implemented in previous artifact
"""
from flask import Blueprint, request, jsonify
from models.api_activity_log import APIActivityLog
from sqlalchemy import func
from app import db

bp = Blueprint('admin', __name__)

@bp.route('/activity_logs', methods=['GET'])
def get_activity_logs():
    """
    GET /api/v1/admin/activity_logs
    Query params:
        - method: Filter by HTTP method (POST, PUT, DELETE)
        - target: Filter by target entity (user, product, category, sale)
        - source: Filter by source (Desktop App, API, Postman)
        - user_id: Filter by user ID
        - start_date: Filter by start date (ISO format)
        - end_date: Filter by end date (ISO format)
        - limit: Max results (default 100)
        - offset: Pagination offset (default 0)
    """
    # Build query with filters
    query = APIActivityLog.query
    
    # Method filter
    method = request.args.get('method')
    if method:
        query = query.filter(APIActivityLog.method == method.upper())
    
    # Target filter
    target = request.args.get('target')
    if target:
        query = query.filter(APIActivityLog.target_entity == target)
    
    # Source filter
    source = request.args.get('source')
    if source:
        query = query.filter(APIActivityLog.source == source)
    
    # User filter
    user_id = request.args.get('user_id', type=int)
    if user_id:
        query = query.filter(APIActivityLog.user_id == user_id)
    
    # Date range filter
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date:
        from dateutil import parser
        try:
            query = query.filter(APIActivityLog.timestamp >= parser.parse(start_date))
        except:
            pass
    if end_date:
        from dateutil import parser
        try:
            query = query.filter(APIActivityLog.timestamp <= parser.parse(end_date))
        except:
            pass
    
    # Pagination
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Ensure reasonable limits
    limit = min(limit, 1000)  # Max 1000 per request
    
    # Order by most recent first
    query = query.order_by(APIActivityLog.timestamp.desc())
    
    # Execute query
    total = query.count()
    logs = query.offset(offset).limit(limit).all()
    
    return jsonify({
        'total': total,
        'offset': offset,
        'limit': limit,
        'count': len(logs),
        'logs': [log.to_dict() for log in logs]
    }), 200


@bp.route('/activity_logs/summary', methods=['GET'])
def activity_logs_summary():
    """
    GET /api/v1/admin/activity_logs/summary
    Returns summary statistics about API activity
    """
    # Total logs
    total_logs = APIActivityLog.query.count()
    
    # Logs by method
    by_method = db.session.query(
        APIActivityLog.method,
        func.count(APIActivityLog.id)
    ).group_by(APIActivityLog.method).all()
    
    # Logs by source
    by_source = db.session.query(
        APIActivityLog.source,
        func.count(APIActivityLog.id)
    ).group_by(APIActivityLog.source).all()
    
    # Logs by target entity
    by_entity = db.session.query(
        APIActivityLog.target_entity,
        func.count(APIActivityLog.id)
    ).filter(APIActivityLog.target_entity.isnot(None)).group_by(APIActivityLog.target_entity).all()
    
    # Recent activity (last 24 hours)
    from datetime import datetime, timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_count = APIActivityLog.query.filter(
        APIActivityLog.timestamp >= yesterday
    ).count()
    
    return jsonify({
        'total_logs': total_logs,
        'recent_24h': recent_count,
        'by_method': dict(by_method),
        'by_source': dict(by_source),
        'by_entity': dict(by_entity)
    }), 200