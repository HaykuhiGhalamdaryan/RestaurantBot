import telebot
from telebot import types, TeleBot
import json
import os
import mysql.connector
from SuggestedProducts import suggest_products
from SaveDish import save_dish
from TrainModel import train_model
from dotenv import load_dotenv
import pickle
import pandas as pd

load_dotenv()
    
db_config = {
    'user': os.getenv("db_user"),
    'password': os.getenv("db_password"),
    'host': os.getenv("host"),
    'database': os.getenv("db_name")
}

with open("terminal.json", 'r') as file:
    json_products = json.load(file)

ID = os.getenv("ID")
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

user_states = {}
user_orders = {}

STATE_DISH_NAME = 1
STATE_NUM_PRODUCTS = 2
STATE_CATEGORY = 3
STATE_SUBCATEGORY = 4
STATE_PRODUCT = 5
STATE_UNIT = 6
STATE_QUANTITY = 7
STATE_CONFIRM = 8
STATE_ORDER = 9
    
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    if message.from_user.id == int(ID):
        make_dish_button = types.InlineKeyboardButton("Make Dish", callback_data='make_dish')
        menu_button = types.InlineKeyboardButton("Menu", callback_data='menu')
        markup.add(make_dish_button, menu_button)
    else:
        menu_button = types.InlineKeyboardButton("Menu", callback_data='menu')
        place_order_button = types.InlineKeyboardButton("Place order", callback_data='place_order')
        top_orders_button = types.InlineKeyboardButton("Top orders", callback_data='top_orders')
        markup.add(menu_button, place_order_button, top_orders_button)
        
    bot.send_message(message.chat.id, f'Hello {message.from_user.first_name}․')
    bot.send_message(message.chat.id, "Welcome! Choose an option:", reply_markup=markup)
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bot_users")
        
        data = cursor.fetchall()
        names = []
        ids = []
        for i in data:
            names.append(i[1])
            ids.append(i[2])

        if message.from_user.first_name not in names and message.from_user.id not in ids:
            cursor.execute(
                "INSERT INTO bot_users (name, user_id) VALUES (%s, %s)",
                (message.from_user.first_name, message.from_user.id)
            )

            conn.commit()
            cursor.close()
            conn.close()

            bot.send_message(message.chat.id, "Your data saved successfully!")
        else:
            bot.send_message(message.chat.id, "Your data already saved!")
            
    except mysql.connector.Error as e:
        bot.send_message(message.chat.id, f"Failed to save data. Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data in ['make_dish', 'menu', 'place_order', 'top_orders'])
def callback_handler(call):
    if call.data == 'make_dish':
        make_dish_start(call.message)
    elif call.data == 'menu':
        display_dishes(call.message)
    elif call.data == 'place_order':
        start_order(call.message)
    elif call.data == 'top_orders':
        display_top_orders(call.message)   

def make_dish_start(message):
    bot.send_message(message.chat.id, "Let's create a dish!")
    user_states[message.chat.id] = {
        'state': STATE_DISH_NAME,
        'data': {}
    }
    bot.send_message(message.chat.id, "Enter the dish name (required):")

@bot.message_handler(func=lambda message: message.chat.id in user_states)
def handle_dish_creation(message):
    user_id = message.chat.id
    state_info = user_states[user_id]
    state = state_info['state']
    data = state_info['data']

    if state == STATE_DISH_NAME:
        dish_name = message.text.strip()
        if dish_name:
            data['dish_name'] = dish_name
            state_info['state'] = STATE_NUM_PRODUCTS
            bot.send_message(user_id, "Enter the number of products:")
            
        else:
            bot.send_message(user_id, "Dish name is required! Please enter it again:")
            
    elif state == STATE_NUM_PRODUCTS:
        try:
            num_products = int(message.text)
            data['num_products'] = num_products
            data['selected_products'] = []
            data['current_product_index'] = 0
            state_info['state'] = STATE_CATEGORY
            bot.send_message(message.chat.id, "5 most purchased products that I can recommend:\n" + ", ".join(suggest_products()))
            bot.send_message(user_id, "Categories:\n" + ", ".join(json_products.keys()))
            bot.send_message(user_id, "Select a category:")
        except ValueError:
            bot.send_message(user_id, "Invalid number! Please enter a valid number:")

    elif state == STATE_CATEGORY:
        category = message.text.lower()
        if category in json_products:
            data['category'] = category
            state_info['state'] = STATE_SUBCATEGORY
            subcategories = list(json_products[category].keys())
            bot.send_message(user_id, "Subcategories:\n" + ", ".join(subcategories))
            bot.send_message(user_id, "Select a subcategory:")
        else:
            bot.send_message(user_id, "Invalid category! Please select again:")

    elif state == STATE_SUBCATEGORY:
        subcategory = message.text.title()
        category = data['category']
        if subcategory in json_products[category]:
            data['subcategory'] = subcategory
            state_info['state'] = STATE_PRODUCT
            products = [product['name'] for product in json_products[category][subcategory]]
            bot.send_message(user_id, "Products:\n" + ", ".join(products))
            bot.send_message(user_id, "Select a product:")
        else:
            bot.send_message(user_id, "Invalid subcategory! Please select again:")

    elif state == STATE_PRODUCT:
        selected_product = message.text.title()
        category = data['category']
        subcategory = data['subcategory']
        products = json_products[category][subcategory]
        for product in products:
            if product['name'] == selected_product:
                data['selected_product'] = product
                units = get_product_units(product['unit'])
                state_info['state'] = STATE_UNIT
                bot.send_message(user_id, f"The unit for '{selected_product}' is: {product['unit']}")
                bot.send_message(user_id, f"Select unit: {units[0]} or {units[1]}")
                return
        bot.send_message(user_id, "Invalid product! Please select again:")

    elif state == STATE_UNIT:
        unit = message.text.lower()
        if unit in ['kg', 'g', 'liter', 'ml', 'dozen', 'pc']:
            data['unit'] = unit
            state_info['state'] = STATE_QUANTITY
            bot.send_message(user_id, "Enter the quantity:")
        else:
            bot.send_message(user_id, "Invalid unit! Please select again:")

    elif state == STATE_QUANTITY:
        try:
            quantity = int(message.text)
            data['quantity'] = quantity

            product = data['selected_product']
            unit = data['unit']
            if unit in ['g', 'ml']:
                quantity = quantity / 1000
            elif unit == 'pc':
                quantity = quantity / 10

            if quantity <= product['stock']:
                data['selected_products'].append({
                    'name': product['name'],
                    'quantity': quantity,
                    'unit': unit,
                    'price': product['price'] * quantity,
                })

                current_index = data['current_product_index']
                if current_index + 1 < data['num_products']:
                    data['current_product_index'] += 1
                    state_info['state'] = STATE_CATEGORY
                    bot.send_message(user_id, "Categories:\n" + ", ".join(json_products.keys()))
                    bot.send_message(user_id, "Select a category:")
                else:
                    cost_price = sum([p['price'] for p in data['selected_products']])
                    selling_price = cost_price * 1.2
                    bot.send_message(user_id, f"Cost Price: {cost_price} AMD\nSelling Price: {selling_price} AMD")
                    state_info['state'] = STATE_CONFIRM
                    bot.send_message(user_id, "Do you want to save this dish? (yes/no)")
            else:
                bot.send_message(user_id, "Insufficient stock! Please enter a valid quantity:")
        except ValueError:
            bot.send_message(user_id, "Invalid quantity! Please enter again:")

    elif state == STATE_CONFIRM:
        if message.text.lower() == 'yes':
            success = save_dish(
                message.chat.id,
                bot,
                data['dish_name'],
                sum([p['price'] for p in data['selected_products']]),
                sum([p['price'] for p in data['selected_products']]) * 1.2,
                data['selected_products']
            )
            if success:
                bot.send_message(message.chat.id, "Dish saved successfully!")  
                state_info['state'] = STATE_ORDER
                         
            else:
                bot.send_message(message.chat.id, "Failed to save the dish. Please try again.")
            del user_states[user_id]
        else:
            bot.send_message(user_id, "Dish creation canceled.")
            del user_states[user_id]

def get_product_units(unit):
    if unit == 'kg':
        return ['kg', 'g']
    elif unit == 'liter':
        return ['liter', 'ml']
    elif unit == 'dozen':
        return ['dozen', 'pc']
    else:
        return [unit]
    
def display_dishes(message):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM dishes")
        dishes = cursor.fetchall()
        conn.close()

        if dishes:
            response = "Menu\n"
            for dish in dishes:
                response += f"- {dish['dish_name']}: Price: {dish['selling_price']} AMD\n"
        else:
            response = "No dishes found."

        bot.send_message(message.chat.id, response)
    except mysql.connector.Error as e:
        bot.send_message(message.chat.id, f"Error fetching dishes: {e}")
        
@bot.callback_query_handler(func=lambda call: call.data == 'place_order')
def start_order(call):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM dishes")
        dishes = cursor.fetchall()
        conn.close()

        if not dishes:
            bot.send_message(call.chat.id, "No dishes available in the menu. Please check back later.")
            return
        
        markup = types.InlineKeyboardMarkup()
        for dish in dishes:
            name = f"{dish['dish_name']} (Price: {dish['selling_price']} AMD)"
            button = types.InlineKeyboardButton(
                name,
                callback_data=f"order_dish_{dish['id']}"
            )
            markup.add(button)

        bot.send_message(call.chat.id, "Please select a dish to order:", reply_markup=markup)

    except mysql.connector.Error as e:
        bot.send_message(call.chat.id, f"Failed to retrieve dishes. Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("order_dish_"))
def order_dish(call):
    try:
        dish_id = call.data.split("_")[2]

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM dishes WHERE id = %s", (dish_id,))
        dish = cursor.fetchone()
        conn.close()

        if dish:
            user_id = call.message.chat.id

            if user_id not in user_orders:
                user_orders[user_id] = []
            user_orders[user_id].append({
                'dish_id': dish['id'],
                'dish_name': dish['dish_name'],
                'price': dish['selling_price']
            })

            bot.send_message(
                call.message.chat.id,
                f"You selected: {dish['dish_name']} (Price: {dish['selling_price']} AMD)\nYour order has been added."
            )
            photo = open(f"C:\\Users\\User\\OneDrive\\Рабочий стол\\practice Py 10.01\\RestaurantProject\\photos\\{dish['dish_name'].replace(' ', '')}.jpg", 'rb')
            bot.send_photo(call.message.chat.id, photo)

        bot.answer_callback_query(call.id, "Dish added to your order!", show_alert=False)

    except mysql.connector.Error as e:
        bot.send_message(call.message.chat.id, f"Failed to retrieve dish details. Error: {e}")
        
@bot.message_handler(commands=['confirm'])
def confirm_order(message):
    user_id = message.chat.id

    if user_id not in user_orders or not user_orders[user_id]:
        bot.send_message(user_id, "You have no orders to confirm.")
        return

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        for order in user_orders[user_id]:
            cursor.execute(
                "INSERT INTO orders (user_id, dish_id, price, dish_name) VALUES (%s, %s, %s, %s)",
                (user_id, order['dish_id'], order['price'], order['dish_name'])
            )
        conn.commit()
        conn.close()

        user_orders[user_id] = []

        bot.send_message(user_id, "Your orders have been confirmed. Thank you!")

    except mysql.connector.Error as e:
        bot.send_message(user_id, f"Failed to save your orders. Error: {e}")

@bot.message_handler(commands=['exit'])
def exit_order(message):
    user_id = message.chat.id
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        for order in user_orders[user_id]:
            cursor.execute(
                "DELETE FROM orders WHERE dish_id = order['dish_id']"
            )
        conn.commit()
        conn.close()

        bot.send_message(user_id, "Your orders exited.")

    except mysql.connector.Error as e:
        bot.send_message(user_id, f"Failed to exit your orders. Error: {e}") 

def display_top_orders(call):
    try:
        train_model()
        with open("top_orders_model.pkl", "rb") as file:
            saved_data = pickle.load(file)
            model = saved_data['model']
            le = saved_data['label_encoder']

        today = pd.Timestamp.now()
        day_of_week = today.dayofweek

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT dish_id, dish_name FROM orders;")
        dishes = cursor.fetchall()
        conn.close()

        dish_ids = [dish[0] for dish in dishes]
        dish_ids_encoded = le.transform(dish_ids)
        
        X_pred = pd.DataFrame({
            'dish_id_encoded': dish_ids_encoded, 
            'day_of_week': day_of_week
        })

        predictions = model.predict(X_pred)

        predictions_df = pd.DataFrame({
            'dish_id': dish_ids,
            'predicted_count': predictions
        }).sort_values(by='predicted_count', ascending=False)

        top_dishes = predictions_df.head(3)

        response = "Top Orders:\n"
        for _, row in top_dishes.iterrows():
            dish_name = next(d[1] for d in dishes if d[0] == row['dish_id'])
            response += f"- {dish_name}\n"

        bot.send_message(call.chat.id, response)

    except Exception as e:
        bot.send_message(call.chat.id, f"Error predicting top orders: {e}")
        
if __name__ == '__main__':
    try:
        print("before call to IP")
        bot.polling(none_stop=True)
        print("after call to IP")
    except (KeyboardInterrupt, SystemExit):
        pass