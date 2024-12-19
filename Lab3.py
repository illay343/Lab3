import json
import sqlite3
from flask import Flask, request, jsonify
from flask_basicauth import BasicAuth

app = Flask(__name__)

# Настройки Basic Auth
app.config['BASIC_AUTH_USERNAME'] = 'admin'
app.config['BASIC_AUTH_PASSWORD'] = 'password'
basic_auth = BasicAuth(app)

# Выбор типа хранилища: 'easy', 'medium', 'hard'
STORAGE_TYPE = 'easy'  # Замените на 'medium' или 'hard' для других уровней сложности

# EASY: Dictionary для хранения данных в памяти
if STORAGE_TYPE == 'easy':
    catalog = {
        1: {"name": "Laptop", "price": 1200, "color": "Silver"},
        2: {"name": "Phone", "price": 800, "color": "Black"}
    }

    def get_all_items():
        return catalog

    def get_item(item_id):
        return catalog.get(item_id)

    def create_item(data):
        new_id = max(catalog.keys(), default=0) + 1
        catalog[new_id] = data
        return new_id

    def update_item(item_id, data):
        catalog[item_id] = data

    def delete_item(item_id):
        del catalog[item_id]

# MEDIUM: Хранилище в файле
elif STORAGE_TYPE == 'medium':
    def load_catalog():
        try:
            with open("catalog.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_catalog(data):
        with open("catalog.json", "w") as f:
            json.dump(data, f)

    catalog = load_catalog()

    def get_all_items():
        return catalog

    def get_item(item_id):
        return catalog.get(str(item_id))

    def create_item(data):
        new_id = max(map(int, catalog.keys()), default=0) + 1
        catalog[str(new_id)] = data
        save_catalog(catalog)
        return new_id

    def update_item(item_id, data):
        catalog[str(item_id)] = data
        save_catalog(catalog)

    def delete_item(item_id):
        del catalog[str(item_id)]
        save_catalog(catalog)

# HARD: Хранилище в SQLite
elif STORAGE_TYPE == 'hard':
    def init_db():
        conn = sqlite3.connect('catalog.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                color TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    init_db()

    def get_all_items():
        conn = sqlite3.connect('catalog.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM items')
        items = cursor.fetchall()
        conn.close()
        return {item[0]: {"name": item[1], "price": item[2], "color": item[3]} for item in items}

    def get_item(item_id):
        conn = sqlite3.connect('catalog.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
        item = cursor.fetchone()
        conn.close()
        if item:
            return {"name": item[1], "price": item[2], "color": item[3]}
        return None

    def create_item(data):
        conn = sqlite3.connect('catalog.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO items (name, price, color) VALUES (?, ?, ?)', (data["name"], data["price"], data["color"]))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return new_id

    def update_item(item_id, data):
        conn = sqlite3.connect('catalog.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE items SET name = ?, price = ?, color = ? WHERE id = ?', (data["name"], data["price"], data["color"], item_id))
        conn.commit()
        conn.close()

    def delete_item(item_id):
        conn = sqlite3.connect('catalog.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
        conn.commit()
        conn.close()

# Роуты для API
@app.route('/items', methods=['GET', 'POST'])
@basic_auth.required
def items():
    if request.method == 'GET':
        return jsonify(get_all_items()), 200
    elif request.method == 'POST':
        data = request.json
        new_id = create_item(data)
        return jsonify({"message": "Item added", "id": new_id}), 201

@app.route('/items/<int:item_id>', methods=['GET', 'PUT', 'DELETE'])
@basic_auth.required
def item_detail(item_id):
    item = get_item(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    if request.method == 'GET':
        return jsonify(item), 200
    elif request.method == 'PUT':
        update_item(item_id, request.json)
        return jsonify({"message": "Item updated"}), 200
    elif request.method == 'DELETE':
        delete_item(item_id)
        return jsonify({"message": "Item deleted"}), 200

if __name__ == '__main__':
    app.run(debug=True)

# GET /items - получить все товары.
# POST /items - добавить новый товар.
# GET /items/<id> - получить товар по ID.
# PUT /items/<id> - обновить товар.
# DELETE /items/<id> - удалить товар.