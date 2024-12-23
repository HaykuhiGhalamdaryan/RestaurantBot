import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import pickle
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

def train_model():
    conn = mysql.connector.connect(**db_config)
    query = "SELECT dish_id, dish_name, created_at, user_id FROM orders;"
    df = pd.read_sql(query, conn)
    conn.close()

    df['created_at'] = pd.to_datetime(df['created_at'])
    
    order_counts = df.groupby([
        df['dish_id'], 
        df['created_at'].dt.dayofweek
    ]).size().reset_index(name='order_count')

    order_counts['day_of_week'] = order_counts['created_at']

    le = LabelEncoder()
    order_counts['dish_id_encoded'] = le.fit_transform(order_counts['dish_id'])

    X = order_counts[['dish_id_encoded', 'day_of_week']]
    y = order_counts['order_count']

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    with open("top_orders_model.pkl", "wb") as file:
        pickle.dump({
            'model': model, 
            'label_encoder': le
        }, file)