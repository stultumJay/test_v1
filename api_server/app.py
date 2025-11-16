# api_server/app.py
"""
StockaDoodle API Server - Main Application Entry Point
Flask-based REST API with SQLAlchemy ORM
Open API (No Authentication/Authorization - RBAC handled by client)
"""

import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///stockadoodle.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import models to register with SQLAlchemy
    with app.app_context():
        from models import user, category, product, sale, retailer_metrics, product_log
        
        # Create all tables if they don't exist
        db.create_all()
        
        # Seed initial data if tables are empty
        _seed_initial_data()
    
    # Register blueprints
    from routes.users import bp as users_bp
    from routes.categories import bp as categories_bp
    from routes.products import bp as products_bp
    from routes.sales import bp as sales_bp
    from routes.logs import bp as logs_bp
    from routes.metrics import bp as metrics_bp
    from routes.dashboard import bp as dashboard_bp
    
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    app.register_blueprint(categories_bp, url_prefix='/api/v1/categories')
    app.register_blueprint(products_bp, url_prefix='/api/v1/products')
    app.register_blueprint(sales_bp, url_prefix='/api/v1/sales')
    app.register_blueprint(logs_bp, url_prefix='/api/v1/log')
    app.register_blueprint(metrics_bp, url_prefix='/api/v1/retailer')
    app.register_blueprint(dashboard_bp, url_prefix='/api/v1/dashboard')
    
    # Health check endpoint
    @app.route('/api/v1/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok', 'version': '1.0.0'}), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


def _seed_initial_data():
    """Seed initial data if database is empty"""
    from models.user import User
    from models.category import Category
    from models.retailer_metrics import RetailerMetrics
    import hashlib
    
    # Check if users exist
    if User.query.count() == 0:
        print("Seeding initial users...")
        
        # Create default users (passwords hashed with SHA256)
        users_data = [
            {
                'username': 'admin',
                'password': 'admin',  # Hash: 8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918
                'role': 'Admin',
                'email': 'admin@stockadoodle.com'
            },
            {
                'username': 'manager',
                'password': 'password',
                'role': 'Manager',
                'email': 'manager@stockadoodle.com'
            },
            {
                'username': 'retailer',
                'password': 'password',
                'role': 'Retailer',
                'email': 'retailer@stockadoodle.com'
            }
        ]
        
        for user_data in users_data:
            password_hash = hashlib.sha256(user_data['password'].encode()).hexdigest()
            user = User(
                username=user_data['username'],
                password_hash=password_hash,
                role=user_data['role'],
                email=user_data.get('email')
            )
            db.session.add(user)
            
            # Create metrics for retailers
            if user_data['role'] == 'Retailer':
                db.session.flush()  # Get user.id
                metrics = RetailerMetrics(retailer_id=user.id)
                db.session.add(metrics)
        
        db.session.commit()
        print(f"Created {len(users_data)} default users")
    
    # Check if categories exist
    if Category.query.count() == 0:
        print("Seeding initial categories...")
        categories = ["Meat", "Seafood", "Pantry Items", "Junk Food", "Pet Food (Wet & Dry)"]
        
        for cat_name in categories:
            category = Category(name=cat_name)
            db.session.add(category)
        
        db.session.commit()
        print(f"Created {len(categories)} categories")


# Create app instance for direct running
app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)