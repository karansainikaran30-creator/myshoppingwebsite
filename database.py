import sqlite3

DATABASE = "shop.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():

    connection = get_db_connection()


    # ========================================================
    # PRODUCTS TABLE
    # ========================================================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            image TEXT,
            description TEXT,
            stock INTEGER DEFAULT 0
        )
    """)


    # ========================================================
    # ORDERS TABLE
    # ========================================================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            address TEXT NOT NULL,
            pincode TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'Order Placed',
            payment_method TEXT DEFAULT 'COD',
            payment_status TEXT DEFAULT 'Pending',
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # ========================================================
    # ORDER ITEMS TABLE
    # ========================================================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)


    # ========================================================
    # NOTIFICATIONS TABLE
    # ========================================================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT DEFAULT 'Order',
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    """)


    # ========================================================
    # ADD PAYMENT COLUMNS TO OLD DATABASE
    # ========================================================

    columns = connection.execute("""
        PRAGMA table_info(orders)
    """).fetchall()


    column_names = [
        column["name"]
        for column in columns
    ]


    if "payment_method" not in column_names:

        connection.execute("""
            ALTER TABLE orders
            ADD COLUMN payment_method TEXT DEFAULT 'COD'
        """)


    if "payment_status" not in column_names:

        connection.execute("""
            ALTER TABLE orders
            ADD COLUMN payment_status TEXT DEFAULT 'Pending'
        """)


    connection.commit()
    connection.close()


if __name__ == "__main__":

    create_tables()

    print("Database and tables created successfully!")