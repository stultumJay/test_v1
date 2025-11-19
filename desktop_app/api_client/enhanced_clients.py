"""
Enhanced API client modules with advanced filtering and gamification
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta, date
from .base import APIResponse, role_required

class EnhancedProductClient:
    """
    Enhanced product management client with advanced features
    Extends basic ProductClient with filtering, search, and inventory queries
    """
    
    def __init__(self, api):
        self.api = api
    
    def list_all(self, include_image: bool = False) -> APIResponse:
        """Get all products"""
        return self.api._request('GET', 'products', params={
            'include_image': 'true' if include_image else 'false'
        })
    
    def search(self, query: str, include_image: bool = False) -> APIResponse:
        """
        Search products by name
        
        Args:
            query: Search term
            include_image: Whether to include Base64 image data
        """
        return self.api._request('GET', 'products', params={
            'search': query,
            'include_image': 'true' if include_image else 'false'
        })
    
    def filter_by_category(self, category_id: int, include_image: bool = False) -> APIResponse:
        """
        Filter products by category
        
        Args:
            category_id: Category ID to filter by
            include_image: Whether to include Base64 image data
        """
        return self.api._request('GET', 'products', params={
            'category_id': category_id,
            'include_image': 'true' if include_image else 'false'
        })
    
    def get_low_stock(self, threshold: int = None) -> APIResponse:
        """
        Get products with low stock
        Filters products where stock_level <= min_stock_level
        
        Args:
            threshold: Optional custom threshold (overrides min_stock_level)
        
        Returns:
            APIResponse with list of low stock products
        """
        resp = self.list_all()
        if not resp.success:
            return resp
        
        products = resp.data
        
        if threshold is not None:
            # Custom threshold
            low_stock = [p for p in products if p.get('stock_level', 0) <= threshold]
        else:
            # Use each product's min_stock_level
            low_stock = [
                p for p in products 
                if p.get('stock_level', 0) <= p.get('min_stock_level', 10)
            ]
        
        return APIResponse(True, data=low_stock)
    
    def get_out_of_stock(self) -> APIResponse:
        """Get products with zero stock"""
        resp = self.list_all()
        if not resp.success:
            return resp
        
        out_of_stock = [p for p in resp.data if p.get('stock_level', 0) == 0]
        return APIResponse(True, data=out_of_stock)
    
    def get_expiring_soon(self, days: int = 7) -> APIResponse:
        """
        Get products expiring within N days
        
        Args:
            days: Number of days threshold
        """
        resp = self.list_all()
        if not resp.success:
            return resp
        
        products = resp.data
        today = date.today()
        threshold_date = today + timedelta(days=days)
        
        expiring = []
        for p in products:
            exp_date_str = p.get('expiration_date')
            if exp_date_str:
                try:
                    exp_date = datetime.fromisoformat(exp_date_str).date()
                    if today <= exp_date <= threshold_date:
                        expiring.append(p)
                except ValueError:
                    continue
        
        return APIResponse(True, data=expiring)
    
    def get_expired(self) -> APIResponse:
        """Get products that have already expired"""
        resp = self.list_all()
        if not resp.success:
            return resp
        
        products = resp.data
        today = date.today()
        
        expired = []
        for p in products:
            exp_date_str = p.get('expiration_date')
            if exp_date_str:
                try:
                    exp_date = datetime.fromisoformat(exp_date_str).date()
                    if exp_date < today:
                        expired.append(p)
                except ValueError:
                    continue
        
        return APIResponse(True, data=expired)
    
    @role_required('Admin', 'Manager')
    def update_stock(self, product_id: int, new_stock_level: int) -> APIResponse:
        """
        Update product stock level
        
        Args:
            product_id: Product ID
            new_stock_level: New stock quantity
        """
        return self.api._request('PUT', f'products/{product_id}', json_data={
            'stock_level': new_stock_level
        })
    
    @role_required('Admin', 'Manager')
    def adjust_stock(self, product_id: int, delta: int) -> APIResponse:
        """
        Adjust stock by a delta (positive or negative)
        
        Args:
            product_id: Product ID
            delta: Amount to add (positive) or subtract (negative)
        """
        # Get current stock
        resp = self.api._request('GET', f'products/{product_id}')
        if not resp.success:
            return resp
        
        current_stock = resp.data.get('stock_level', 0)
        new_stock = max(0, current_stock + delta)  # Don't go negative
        
        return self.update_stock(product_id, new_stock)
    
    def get_inventory_value(self) -> APIResponse:
        """
        Calculate total inventory value
        Returns: APIResponse with {'total_value': float, 'product_count': int}
        """
        resp = self.list_all()
        if not resp.success:
            return resp
        
        total_value = sum(
            p.get('price', 0) * p.get('stock_level', 0) 
            for p in resp.data
        )
        
        return APIResponse(True, data={
            'total_value': total_value,
            'product_count': len(resp.data)
        })


class RetailerMetricsClient:
    """
    Client for retailer gamification features
    Handles streaks, quotas, and performance tracking
    """
    
    def __init__(self, api):
        self.api = api
    
    def get_metrics(self, retailer_id: int) -> APIResponse:
        """
        Get retailer metrics (streak, quota, etc.)
        
        Args:
            retailer_id: Retailer user ID
        """
        return self.api._request('GET', f'retailer/{retailer_id}')
    
    def get_leaderboard(self, limit: int = 10) -> APIResponse:
        """
        Get top performers leaderboard
        
        Args:
            limit: Number of top retailers to return
        """
        resp = self.api._request('GET', 'retailer/leaderboard')
        if resp.success and limit:
            # Limit results
            resp.data = resp.data[:limit]
        return resp
    
    def calculate_streak(self, retailer_id: int) -> APIResponse:
        """
        Calculate current streak for a retailer
        Streak = consecutive days with sales
        
        Returns:
            APIResponse with {'current_streak': int, 'last_sale_date': str}
        """
        resp = self.get_metrics(retailer_id)
        if not resp.success:
            return resp
        
        metrics = resp.data
        return APIResponse(True, data={
            'current_streak': metrics.get('current_streak', 0),
            'last_sale_date': metrics.get('last_sale_date'),
            'daily_quota_usd': metrics.get('daily_quota_usd', 0.0)
        })
    
    def get_daily_performance(self, retailer_id: int) -> APIResponse:
        """
        Get today's sales performance for a retailer
        
        Returns:
            APIResponse with {'today_sales': float, 'quota_progress': float}
        """
        # Get metrics
        resp = self.get_metrics(retailer_id)
        if not resp.success:
            return resp
        
        metrics = resp.data
        daily_quota = metrics.get('daily_quota_usd', 0.0)
        
        # Check if last sale was today
        last_sale_date = metrics.get('last_sale_date')
        today = date.today().isoformat()
        
        today_sales = 0.0
        if last_sale_date == today:
            today_sales = daily_quota
        
        # Calculate progress percentage
        quota_progress = 0.0
        if daily_quota > 0:
            # Assume daily target is based on historical average
            # For now, use arbitrary target of $1000/day
            target = 1000.0
            quota_progress = min(100.0, (today_sales / target) * 100)
        
        return APIResponse(True, data={
            'today_sales': today_sales,
            'quota_progress': quota_progress,
            'target': 1000.0
        })
    
    def get_weekly_performance(self, retailer_id: int) -> APIResponse:
        """
        Get week's sales performance
        Requires sales history endpoint
        """
        # TODO: Implement when sales history endpoint is available
        return APIResponse(False, error="Weekly performance not yet implemented")
    
    def get_achievements(self, retailer_id: int) -> Dict:
        """
        Calculate achievements/badges for a retailer
        
        Returns:
            Dict with achievement data
        """
        resp = self.get_metrics(retailer_id)
        if not resp.success:
            return {'achievements': [], 'error': resp.error}
        
        metrics = resp.data
        streak = metrics.get('current_streak', 0)
        daily_quota = metrics.get('daily_quota_usd', 0.0)
        
        achievements = []
        
        # Streak achievements
        if streak >= 7:
            achievements.append({
                'name': 'Week Warrior',
                'description': '7-day sales streak',
                'icon': 'fire',
                'tier': 'bronze'
            })
        if streak >= 30:
            achievements.append({
                'name': 'Monthly Master',
                'description': '30-day sales streak',
                'icon': 'star',
                'tier': 'gold'
            })
        
        # Sales volume achievements
        if daily_quota >= 1000:
            achievements.append({
                'name': 'Thousand Club',
                'description': '$1000+ in daily sales',
                'icon': 'dollar-sign',
                'tier': 'silver'
            })
        if daily_quota >= 5000:
            achievements.append({
                'name': 'High Roller',
                'description': '$5000+ in daily sales',
                'icon': 'trending-up',
                'tier': 'platinum'
            })
        
        return {
            'achievements': achievements,
            'total_count': len(achievements),
            'streak': streak,
            'quota': daily_quota
        }


class EnhancedSalesClient:
    """
    Enhanced sales client with analytics and reporting
    """
    
    def __init__(self, api):
        self.api = api
    
    @role_required('Admin', 'Manager', 'Retailer')
    def record(self, retailer_id: int, items: List[Dict], total_amount: float = None) -> APIResponse:
        """
        Record sale with automatic total calculation
        
        Args:
            retailer_id: ID of retailer making the sale
            items: List of {'product_id': int, 'quantity': int, 'price': float}
            total_amount: Optional manual total (calculated if not provided)
        """
        # Calculate total if not provided
        if total_amount is None:
            total_amount = sum(
                item['price'] * item['quantity'] 
                for item in items
            )
        
        return self.api._request('POST', 'sales', json_data={
            'retailer_id': retailer_id,
            'items': items,
            'total_amount': total_amount
        })
    
    @role_required('Admin', 'Manager')
    def get_report(self, start_date: str = None, end_date: str = None) -> APIResponse:
        """
        Get sales report for date range
        
        Args:
            start_date: ISO format date string (YYYY-MM-DD)
            end_date: ISO format date string (YYYY-MM-DD)
        """
        params = {}
        if start_date:
            params['start'] = start_date
        if end_date:
            params['end'] = end_date
        
        return self.api._request('GET', 'sales/reports', params=params)
    
    @role_required('Admin', 'Manager')
    def get_today_sales(self) -> APIResponse:
        """Get today's sales report"""
        today = date.today().isoformat()
        return self.get_report(start_date=today, end_date=today)
    
    @role_required('Admin', 'Manager')
    def get_week_sales(self) -> APIResponse:
        """Get this week's sales report"""
        today = date.today()
        week_start = (today - timedelta(days=today.weekday())).isoformat()
        return self.get_report(start_date=week_start, end_date=today.isoformat())
    
    @role_required('Admin', 'Manager')
    def get_month_sales(self) -> APIResponse:
        """Get this month's sales report"""
        today = date.today()
        month_start = date(today.year, today.month, 1).isoformat()
        return self.get_report(start_date=month_start, end_date=today.isoformat())


# Integration into main API client
def enhance_api_client(api_client):
    """
    Add enhanced clients to existing API client instance
    
    Usage:
        api = StockaDoodleAPI()
        enhance_api_client(api)
        api.products_enhanced.get_low_stock()
    """
    api_client.products_enhanced = EnhancedProductClient(api_client)
    api_client.retailer_metrics = RetailerMetricsClient(api_client)
    api_client.sales_enhanced = EnhancedSalesClient(api_client)