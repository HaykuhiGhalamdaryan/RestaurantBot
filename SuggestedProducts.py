import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

db_config = {
    'user': os.getenv("db_user"),
    'password': os.getenv("db_password"),
    'host': os.getenv("host"),
    'database': os.getenv("db_name")
}

def get_frequent_products():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT product_name, SUM(quantity) AS total_quantity
        FROM dish_products
        GROUP BY product_name
        ORDER BY total_quantity DESC
        LIMIT 5;
    """
    cursor.execute(query)
    frequent_products = cursor.fetchall()
    cursor.close()
    conn.close()
    return frequent_products

def suggest_products():
    suggestions = get_frequent_products()
    sugg_products = []
    for i in suggestions:
        sugg_products.append((i['product_name']).title())
    return sugg_products
