<div align="center">
    <img src="desktop_app\assets\icons\stockadoodle-transparent.png" alt="Stockadoodle Logo" width="150">
    
    <h1> Stockadoodle - Inventory Management System </h1>
</div>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python Version"/>
  <img src="https://img.shields.io/badge/PyQt6-Framework-green.svg" alt="PyQt6"/>
  <img src="https://img.shields.io/badge/SQLite-4169E1?logo=sqlite&logoColor=fff&style=plastic" alt="SQLite"/>
  <img src="https://img.shields.io/badge/status-maintained-brightgreen.svg" alt="Status"/>
</p>


## Overview
StockaDoodle is an inventory management system designed for **QuickMart Convenience Stores** in order to facilitate the management of daily operations of each branches. Each branch operates its own independent server, ensuring that all data—such as product inventory, sales, and user activities—is stored locally on each branch’s server. This decentralized setup allows Admins, Managers, and Retailers to carry out their respective duties within their branch, all in a secure and easy-to-use environment. Admins manage user accounts and system settings, Managers deal with stock monitoring and reporting, and Retailers use the Point-of-Sale (POS) module to record sales.


## Directory Structure
A brief overview of the project's directory structure:

* `api_server/`: 1. BACKEND (Flask API & DB).
    * `app.py/`: Main Flask app, API routes, and DB setup.
    * `inventory.db/`: SQLite database file.
    * `requirements.txt/`: Flask, SQLAlchemy, dotenv, etc.
    * `core/`: Business Logic
        * `activity_logger.py/`: Logs all transaction for Security Log.
        * `inventory_manager.py/`: Handles stock levels and low-stock alerts.
        * `mfa_service.py/`: Multi-factor Authentication for Admin/Manager.
        * `sales_manager.py/`: Transaction processing and gamification logic.
        * `user_manager.py/`: Authentication and User CRUD
    * `models/`
        * `category.py/`
        * `product.py/`: Includes low-stock threshold field.
        * `sale.py/`: Records transcation details.
        * `user.py/`: Includes role (Admin, Manager, Retailer).
* `desktop_app/`: 2. FRONTEND (PyQT6 Client).
    * `main.py/`: PyQt6 entry point.
    * `requirements.txt/`: PyQt6, requests, Matplotlib/PyQtGraph.
    * `assets/`: Static files for UI.
        * `icons/`: Image icons for UI.
        * `product_images/`: Local cache for product images.
    * `api_client/`: Connection layer to the backend.
        * `stockadoodle_api.py/`: **CRITICAL:** Wrapper class for all HTTP requests.
    * `ui/`: All User Interfaces
        * `login_window.py/`: UI for logging in.
        * `mfa_window.py/`: UI for Multi-factor Authentication of Admin/Manager
        * `admin_dashboard/`: User with Admin-role Dashboard
        * `manager_dashboard/`: User with Manager-role Dashboard
        * `retailer_pos/`: User with Retailer-role Dashboard (Point of Sale)
    * `utils/`: Shared client utilities
        * `config/`: App level configuration (e.g., API base URL, colors, fonts)
        * `decorators.py/`: For local UI permission checks
        * `style_utils.py/`: For UI styling