"""
Input validation utilities for API routes
Provides comprehensive validation for all entity types
"""
from datetime import datetime, date
from typing import Dict, List, Optional


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_product_data(data: Dict, is_update: bool = False) -> List[str]:
    """
    Validate product creation/update data
    
    Args:
        data: Product data dictionary
        is_update: If True, all fields are optional
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Name validation (required for creation)
    if not is_update:
        if not data.get('name'):
            errors.append("Product name is required")
        elif len(str(data.get('name'))) > 120:
            errors.append("Product name must be 120 characters or less")
    
    # Brand validation (optional but has max length)
    brand = data.get('brand')
    if brand and len(str(brand)) > 50:
        errors.append("Brand must be 50 characters or less")
    
    # Price validation
    price = data.get('price')
    if price is not None:
        try:
            price = float(price)
            if price < 0:
                errors.append("Price must be non-negative")
            if price > 999999.99:
                errors.append("Price must be less than $1,000,000")
        except (ValueError, TypeError):
            errors.append("Price must be a valid number")
    elif not is_update:
        errors.append("Price is required")
    
    # Stock level validation
    stock = data.get('stock_level')
    if stock is not None:
        try:
            stock = int(stock)
            if stock < 0:
                errors.append("Stock level must be non-negative")
            if stock > 999999:
                errors.append("Stock level must be less than 1,000,000")
        except (ValueError, TypeError):
            errors.append("Stock level must be a valid integer")
    
    # Min stock level validation
    min_stock = data.get('min_stock_level')
    if min_stock is not None:
        try:
            min_stock = int(min_stock)
            if min_stock < 0:
                errors.append("Minimum stock level must be non-negative")
            if min_stock > 1000:
                errors.append("Minimum stock level must be less than 1,000")
        except (ValueError, TypeError):
            errors.append("Minimum stock level must be a valid integer")
    
    # Expiration date validation
    exp_date = data.get('expiration_date')
    if exp_date:
        try:
            if isinstance(exp_date, str):
                datetime.fromisoformat(exp_date)
        except (ValueError, TypeError):
            errors.append("Expiration date must be in ISO format (YYYY-MM-DD)")
    
    # Category ID validation
    category_id = data.get('category_id')
    if category_id is not None:
        try:
            int(category_id)
        except (ValueError, TypeError):
            errors.append("Category ID must be a valid integer")
    
    return errors


def validate_user_data(data: Dict, is_update: bool = False) -> List[str]:
    """
    Validate user creation/update data
    
    Args:
        data: User data dictionary
        is_update: If True, all fields are optional
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Username validation
    if not is_update:
        if not data.get('username'):
            errors.append("Username is required")
    
    username = data.get('username')
    if username:
        if len(str(username)) < 3:
            errors.append("Username must be at least 3 characters")
        if len(str(username)) > 50:
            errors.append("Username must be 50 characters or less")
        if not str(username).replace('_', '').replace('-', '').isalnum():
            errors.append("Username can only contain letters, numbers, underscores, and hyphens")
    
    # Password validation (only for creation or if provided in update)
    password = data.get('password')
    if not is_update:
        if not password:
            errors.append("Password is required")
    
    if password:
        if len(str(password)) < 4:
            errors.append("Password must be at least 4 characters")
        if len(str(password)) > 128:
            errors.append("Password must be 128 characters or less")
    
    # Role validation
    role = data.get('role')
    if role:
        valid_roles = ['Admin', 'Manager', 'Retailer']
        if role not in valid_roles:
            errors.append(f"Role must be one of: {', '.join(valid_roles)}")
    elif not is_update:
        errors.append("Role is required")
    
    # Email validation
    email = data.get('email')
    if email:
        if '@' not in str(email) or '.' not in str(email):
            errors.append("Email must be a valid email address")
        if len(str(email)) > 120:
            errors.append("Email must be 120 characters or less")
    
    return errors


def validate_category_data(data: Dict, is_update: bool = False) -> List[str]:
    """
    Validate category creation/update data
    
    Args:
        data: Category data dictionary
        is_update: If True, all fields are optional
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Name validation
    if not is_update:
        if not data.get('name'):
            errors.append("Category name is required")
    
    name = data.get('name')
    if name:
        if len(str(name)) < 2:
            errors.append("Category name must be at least 2 characters")
        if len(str(name)) > 100:
            errors.append("Category name must be 100 characters or less")
    
    return errors


def validate_sale_data(data: Dict) -> List[str]:
    """
    Validate sale transaction data
    
    Args:
        data: Sale data dictionary
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Retailer ID validation
    retailer_id = data.get('retailer_id')
    if not retailer_id:
        errors.append("Retailer ID is required")
    else:
        try:
            int(retailer_id)
        except (ValueError, TypeError):
            errors.append("Retailer ID must be a valid integer")
    
    # Items validation
    items = data.get('items')
    if not items:
        errors.append("Items list is required")
    elif not isinstance(items, list):
        errors.append("Items must be a list")
    elif len(items) == 0:
        errors.append("Items list cannot be empty")
    else:
        # Validate each item
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"Item {i} must be a dictionary")
                continue
            
            # Product ID
            if 'product_id' not in item:
                errors.append(f"Item {i}: product_id is required")
            else:
                try:
                    int(item['product_id'])
                except (ValueError, TypeError):
                    errors.append(f"Item {i}: product_id must be a valid integer")
            
            # Quantity
            if 'quantity' not in item:
                errors.append(f"Item {i}: quantity is required")
            else:
                try:
                    qty = int(item['quantity'])
                    if qty <= 0:
                        errors.append(f"Item {i}: quantity must be positive")
                    if qty > 10000:
                        errors.append(f"Item {i}: quantity must be less than 10,000")
                except (ValueError, TypeError):
                    errors.append(f"Item {i}: quantity must be a valid integer")
            
            # Price
            if 'price' not in item:
                errors.append(f"Item {i}: price is required")
            else:
                try:
                    price = float(item['price'])
                    if price < 0:
                        errors.append(f"Item {i}: price must be non-negative")
                except (ValueError, TypeError):
                    errors.append(f"Item {i}: price must be a valid number")
    
    # Total amount validation
    total = data.get('total_amount')
    if total is None:
        errors.append("Total amount is required")
    else:
        try:
            total = float(total)
            if total < 0:
                errors.append("Total amount must be non-negative")
            if total > 9999999.99:
                errors.append("Total amount must be less than $10,000,000")
        except (ValueError, TypeError):
            errors.append("Total amount must be a valid number")
    
    return errors


def validate_disposal_data(data: Dict) -> List[str]:
    """
    Validate product disposal data
    
    Args:
        data: Disposal data dictionary
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Product ID validation
    product_id = data.get('product_id')
    if not product_id:
        errors.append("Product ID is required")
    else:
        try:
            int(product_id)
        except (ValueError, TypeError):
            errors.append("Product ID must be a valid integer")
    
    # User ID validation
    user_id = data.get('user_id')
    if not user_id:
        errors.append("User ID is required")
    else:
        try:
            int(user_id)
        except (ValueError, TypeError):
            errors.append("User ID must be a valid integer")
    
    # Quantity validation
    quantity = data.get('quantity')
    if not quantity:
        errors.append("Quantity is required")
    else:
        try:
            qty = int(quantity)
            if qty <= 0:
                errors.append("Quantity must be positive")
            if qty > 10000:
                errors.append("Quantity must be less than 10,000")
        except (ValueError, TypeError):
            errors.append("Quantity must be a valid integer")
    
    # Notes validation (optional but has max length)
    notes = data.get('notes')
    if notes and len(str(notes)) > 500:
        errors.append("Notes must be 500 characters or less")
    
    return errors


def validate_positive_integer(value, field_name: str, max_value: int = None) -> Optional[str]:
    """
    Helper to validate a positive integer field
    
    Args:
        value: Value to validate
        field_name: Name of field for error message
        max_value: Optional maximum allowed value
        
    Returns:
        Error message if invalid, None if valid
    """
    try:
        val = int(value)
        if val <= 0:
            return f"{field_name} must be positive"
        if max_value and val > max_value:
            return f"{field_name} must be less than {max_value:,}"
        return None
    except (ValueError, TypeError):
        return f"{field_name} must be a valid integer"


def validate_date_range(start_date: str, end_date: str) -> List[str]:
    """
    Validate date range for reports
    
    Args:
        start_date: Start date string (ISO format)
        end_date: End date string (ISO format)
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    if start_date:
        try:
            start = datetime.fromisoformat(start_date)
        except (ValueError, TypeError):
            errors.append("Start date must be in ISO format (YYYY-MM-DD)")
            start = None
    else:
        start = None
    
    if end_date:
        try:
            end = datetime.fromisoformat(end_date)
        except (ValueError, TypeError):
            errors.append("End date must be in ISO format (YYYY-MM-DD)")
            end = None
    else:
        end = None
    
    # Check that start is before end
    if start and end and start > end:
        errors.append("Start date must be before end date")
    
    return errors
