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

def save_dish(chat_id, bot, dish_name, cost_price, selling_price, selected_products):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO dishes (dish_name, cost_price, selling_price) VALUES (%s, %s, %s)",
            (dish_name, cost_price, selling_price)
        )
        dish_id = cursor.lastrowid

        for product in selected_products:
            product_name = product['name']
            quantity = product['quantity']
            unit = product['unit']
            cursor.execute(
                "INSERT INTO dish_products (dish_id, product_name, quantity, unit) VALUES (%s, %s, %s, %s)",
                (dish_id, product_name, quantity, unit)
            )

        conn.commit()
        cursor.close()
        conn.close()

        bot.send_message(chat_id, "Dish saved successfully!")
        return True

    except mysql.connector.Error as e:
        bot.send_message(chat_id, f"Failed to save the dish. Error: {e}")
        return False