
from pathlib import Path
import os

# Project directory
BASE_DIR = Path(__file__).resolve().parent

# Source and output file paths
SOURCE_CSV = BASE_DIR / "food_orders.csv"
TRANSFORMED_CSV = BASE_DIR / "transformed_food_orders.csv"
INVALID_CSV = BASE_DIR / "invalid_food_orders.csv"
VALIDATION_REPORT = BASE_DIR / "validation_report.txt"
REJECTED_CSV = BASE_DIR / "rejected_records.csv"
MISSING_REPORT = BASE_DIR / "missing_values_report.csv"
FINANCIAL_INCOMPLETE_CSV = BASE_DIR / "financial_incomplete_records.csv"

# Batch configuration
BATCH_SIZE = 100

# Database names
RAW_DB_NAME = "food_orders_raw_db"
ANALYTICS_DB_NAME = "food_orders_analytics_db"

# Table names
RAW_TABLE_NAME = "raw_food_orders"
ANALYTICS_TABLE_NAME = "cleaned_food_orders"

# MySQL connection configuration
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": os.getenv("MYSQL_PASSWORD", "YOUR_MYSQL_PASSWORD"),
    "port": 3306
}

# Raw database configuration
RAW_DB_CONFIG = {
    **MYSQL_CONFIG,
    "database": RAW_DB_NAME
}

# Analytics database configuration
ANALYTICS_DB_CONFIG = {
    **MYSQL_CONFIG,
    "database": ANALYTICS_DB_NAME
}
