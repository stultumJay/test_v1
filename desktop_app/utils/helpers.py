"""
Helper utilities for StockaDoodle Desktop App
Icons, image loading, date formatting, etc.
"""

import os
from datetime import datetime
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtSvg import QSvgRenderer
from utils.config import AppConfig


def get_feather_icon(name: str, color: str = "white", size: int = 24) -> QIcon:
    """
    Get a Feather icon as QIcon with specified color and size
    
    Args:
        name: Icon name (e.g., 'user', 'settings', 'package')
        color: Icon color (hex or named color)
        size: Icon size in pixels
        
    Returns:
        QIcon object
    """
    # Feather Icons SVG path templates
    # In production, you'd have actual SVG files or use a library
    # For now, we'll create simple colored squares as placeholders
    
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Parse color
    if isinstance(color, str):
        if color.startswith('#'):
            q_color = QColor(color)
        else:
            q_color = QColor(color)
    else:
        q_color = QColor(color)
    
    painter.setBrush(q_color)
    painter.setPen(Qt.PenStyle.NoPen)
    
    # Draw a simple icon representation
    # In production, this would render actual Feather SVG icons
    if name in ['user', 'users']:
        # Circle for user icon
        painter.drawEllipse(size//4, size//4, size//2, size//2)
    elif name in ['package', 'box']:
        # Square for package
        painter.drawRect(size//4, size//4, size//2, size//2)
    elif name in ['settings', 'tool']:
        # Gear approximation
        painter.drawEllipse(size//3, size//3, size//3, size//3)
    elif name == 'dollar-sign':
        # S shape approximation
        painter.drawEllipse(size//4, size//4, size//2, size//2)
    elif name in ['shopping-cart', 'shopping-bag']:
        # Cart shape
        painter.drawRect(size//4, size//3, size//2, size//3)
    elif name in ['calendar', 'clock']:
        # Square for calendar
        painter.drawRoundedRect(size//4, size//4, size//2, size//2, 3, 3)
    elif name in ['alert-triangle', 'alert-circle']:
        # Triangle or circle warning
        painter.drawEllipse(size//4, size//4, size//2, size//2)
    elif name in ['edit', 'edit-2', 'edit-3']:
        # Pencil approximation
        painter.drawRect(size//3, size//4, size//4, size//2)
    elif name in ['trash', 'trash-2']:
        # Trash can
        painter.drawRect(size//3, size//3, size//3, size//2)
    elif name in ['plus', 'plus-circle', 'plus-square']:
        # Plus sign
        painter.drawRect(size//2 - 2, size//4, 4, size//2)
        painter.drawRect(size//4, size//2 - 2, size//2, 4)
    elif name in ['check', 'check-circle']:
        # Check mark
        painter.drawRect(size//3, size//2, size//4, 4)
        painter.drawRect(size//2, size//3, 4, size//3)
    elif name in ['x', 'x-circle']:
        # X mark
        painter.drawLine(size//4, size//4, 3*size//4, 3*size//4)
        painter.drawLine(3*size//4, size//4, size//4, 3*size//4)
    elif name in ['refresh-cw', 'rotate-cw']:
        # Circular arrow approximation
        painter.drawEllipse(size//4, size//4, size//2, size//2)
    elif name in ['file-text', 'file']:
        # Document
        painter.drawRect(size//3, size//4, size//3, size//2)
    elif name in ['lock', 'unlock']:
        # Lock shape
        painter.drawRect(size//3, size//2, size//3, size//3)
        painter.drawEllipse(size//3, size//4, size//3, size//4)
    elif name in ['log-out', 'log-in']:
        # Arrow
        painter.drawRect(size//4, size//2 - 2, size//2, 4)
    else:
        # Default: filled circle
        painter.drawEllipse(size//4, size//4, size//2, size//2)
    
    painter.end()
    
    return QIcon(pixmap)


def load_product_image(image_path: str, target_size: QSize = None, 
                      keep_aspect_ratio: bool = True) -> QPixmap:
    """
    Load a product image and optionally resize it
    
    Args:
        image_path: Path to the image file
        target_size: Desired size (QSize)
        keep_aspect_ratio: Whether to maintain aspect ratio
        
    Returns:
        QPixmap object
    """
    if not image_path or not os.path.exists(image_path):
        # Return placeholder image
        return create_placeholder_image(target_size or QSize(200, 200))
    
    try:
        pixmap = QPixmap(image_path)
        
        if target_size:
            if keep_aspect_ratio:
                pixmap = pixmap.scaled(
                    target_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            else:
                pixmap = pixmap.scaled(
                    target_size,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
        
        return pixmap
        
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return create_placeholder_image(target_size or QSize(200, 200))


def create_placeholder_image(size: QSize) -> QPixmap:
    """Create a placeholder image when no product image is available"""
    pixmap = QPixmap(size)
    pixmap.fill(QColor("#34495E"))
    
    painter = QPainter(pixmap)
    painter.setPen(QColor("#7f8c8d"))
    painter.drawText(
        pixmap.rect(),
        Qt.AlignmentFlag.AlignCenter,
        "No Image"
    )
    painter.end()
    
    return pixmap


def save_product_image(source_path: str, product_id: int = None) -> str:
    """
    Save a product image to the assets directory
    
    Args:
        source_path: Path to the source image
        product_id: Optional product ID for filename
        
    Returns:
        Relative path to saved image
    """
    try:
        import shutil
        from pathlib import Path
        
        # Ensure product images directory exists
        images_dir = Path("assets/product_images")
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        if product_id:
            ext = Path(source_path).suffix
            filename = f"product_{product_id}{ext}"
        else:
            filename = Path(source_path).name
        
        dest_path = images_dir / filename
        
        # Copy file
        shutil.copy2(source_path, dest_path)
        
        return str(dest_path)
        
    except Exception as e:
        print(f"Error saving product image: {e}")
        return None


def delete_product_image(image_path: str) -> bool:
    """
    Delete a product image file
    
    Args:
        image_path: Path to the image to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting image {image_path}: {e}")
        return False


def format_date(date_str: str, format_type: str = "short") -> str:
    """
    Format a date string for display
    
    Args:
        date_str: ISO format date string
        format_type: "short", "long", or "time"
        
    Returns:
        Formatted date string
    """
    if not date_str:
        return "N/A"
    
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        
        if format_type == "short":
            return dt.strftime("%Y-%m-%d")
        elif format_type == "long":
            return dt.strftime("%B %d, %Y at %I:%M %p")
        elif format_type == "time":
            return dt.strftime("%I:%M %p")
        else:
            return dt.strftime("%Y-%m-%d %H:%M")
            
    except Exception as e:
        print(f"Error formatting date {date_str}: {e}")
        return date_str


def format_currency(amount: float, symbol: str = "$") -> str:
    """
    Format a number as currency
    
    Args:
        amount: Numeric amount
        symbol: Currency symbol
        
    Returns:
        Formatted currency string
    """
    try:
        return f"{symbol}{amount:,.2f}"
    except:
        return f"{symbol}0.00"


def truncate_text(text: str, max_length: int = 50, ellipsis: str = "...") -> str:
    """
    Truncate text to a maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        ellipsis: String to append if truncated
        
    Returns:
        Truncated string
    """
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(ellipsis)] + ellipsis


def validate_email(email: str) -> bool:
    """
    Simple email validation
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid format, False otherwise
    """
    if not email:
        return False
    return '@' in email and '.' in email.split('@')[-1]


def generate_unique_filename(base_name: str, extension: str = ".jpg") -> str:
    """
    Generate a unique filename with timestamp
    
    Args:
        base_name: Base filename
        extension: File extension
        
    Returns:
        Unique filename string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}{extension}"