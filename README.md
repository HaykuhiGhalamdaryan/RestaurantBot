# Telegram Bot for Dish Management

This project is a Telegram bot designed for managing restaurant dishes, orders, and user interactions. The bot allows users to create dishes, place orders, view the menu, and analyze top orders. It integrates with a MySQL database for persistent data storage and uses a structured JSON file for managing product categories and details.

## Features

- **User Management**: Automatically registers new users and prevents duplicate entries.
- **Dish Creation**: Allows admin users to create dishes by selecting categories, subcategories, and products from a JSON file.
- **Product Recommendations**: Suggests the top 5 most purchased products during dish creation.
- **Menu Display**: Shows all available dishes in the restaurant's menu with their prices.
- **Order Management**: Enables users to place orders from the menu, add items to their orders, and confirm them.
- **Top Orders Analysis**: Trains a model to analyze and display the most popular dishes based on order history.
- **Stock Validation**: Validates product stock during dish creation and order placement.

## Prerequisites

### Environment
- Python 3.8 or higher
- MySQL database

### Libraries
Install the required libraries using:
```bash
pip install -r requirements.txt
```

### Files
- **`terminal.json`**: A JSON file containing categories, subcategories, and products with their stock and prices.
- **`.env`**: Environment file with the following variables:
  ```
  db_user=<your-database-username>
  db_password=<your-database-password>
  host=<your-database-host>
  db_name=<your-database-name>
  ID=<admin-telegram-id>
  TOKEN=<bot-token>
  ```

### Folder Structure
- `bot.py`: Main script for the bot.
- `SuggestedProducts.py`: Module to suggest top products.
- `SaveDish.py`: Module to save dishes into the database.
- `TrainModel.py`: Module to train the top orders analysis model.
- `photos/`: Folder containing images of dishes.

## Database Schema

### Tables
#### `bot_users`
| Column   | Type         | Description          |
|----------|--------------|----------------------|
| `id`     | INT          | Primary key          |
| `name`   | VARCHAR(255) | User's name          |
| `user_id`| INT          | Telegram user ID     |

#### `dishes`
| Column         | Type         | Description                 |
|----------------|--------------|-----------------------------|
| `id`           | INT          | Primary key                 |
| `dish_name`    | VARCHAR(255) | Name of the dish            |
| `cost_price`   | FLOAT        | Cost price of the dish      |
| `selling_price`| FLOAT        | Selling price of the dish   |

#### `orders`
| Column      | Type         | Description               |
|-------------|--------------|---------------------------|
| `id`        | INT          | Primary key               |
| `user_id`   | INT          | Telegram user ID          |
| `dish_id`   | INT          | ID of the ordered dish    |
| `price`     | FLOAT        | Price of the ordered dish |
| `dish_name` | VARCHAR(255) | Name of the ordered dish  |
| `created_at`| TIMESTAMP    | Current timestamp         |

#### `dish_products`
| Column         | Type         | Description                 |
|----------------|--------------|-----------------------------|
| `id`           | INT          | Primary key                 |
| `dish_id`      | INT          | Id of the dish              |
| `product_name` | VARCHAR(255) | Name of the product         |
| `quantity`     | FLOAT        | Quantity of the product     |
| `unit`         | VARCHAR(50)  | Unit of the product         |

## How to Run the Bot

1. Clone the repository:
   ```bash
   git clone https://github.com/HaykuhiGhalamdaryan/RestaurantBot.git
   ```
2. Navigate to the project directory:
   ```bash
   cd RestaurantBot
   ```
3. Ensure your MySQL database is set up with the required schema.
4. Create and populate the `.env` file with your credentials.
5. Start the bot:
   ```bash
   python bot.py
   ```

## Usage

### Commands
- `/start`: Initiates the bot and displays options based on user type (admin or regular user).
- `/confirm`: Confirms all selected orders for a user.
- `/exit`: Cancels all current orders for a user.

### Callbacks
- `make_dish`: Starts the dish creation process for admin users.
- `menu`: Displays the menu of available dishes.
- `place_order`: Enables users to place orders from the menu.
- `top_orders`: Triggers the analysis of top orders.

## License
This project is licensed under the MIT License.

