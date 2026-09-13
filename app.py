import os

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session
)

from database import get_db_connection, create_tables


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)

# Environment
# Local development defaults are kept so the website continues to work
# on your computer. For production, set these values in the hosting
# platform's Environment Variables.
APP_ENV = os.getenv("APP_ENV", "development").lower()
IS_PRODUCTION = APP_ENV == "production"

SECRET_KEY = os.getenv("SECRET_KEY")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if IS_PRODUCTION:
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY environment variable is required in production.")
    if not ADMIN_USERNAME:
        raise RuntimeError("ADMIN_USERNAME environment variable is required in production.")
    if not ADMIN_PASSWORD:
        raise RuntimeError("ADMIN_PASSWORD environment variable is required in production.")
else:
    SECRET_KEY = SECRET_KEY or "myshop-local-dev-secret-2026"
    ADMIN_USERNAME = ADMIN_USERNAME or "admin"
    ADMIN_PASSWORD = ADMIN_PASSWORD or "admin123"

app.secret_key = SECRET_KEY

# Session security
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = IS_PRODUCTION


# ============================================================
# ALLOWED ORDER STATUSES
# ============================================================

ALLOWED_ORDER_STATUSES = [
    "Order Placed",
    "Confirmed",
    "Shipped",
    "Out for Delivery",
    "Delivered",
    "Cancelled"
]


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

create_tables()

# Add active/hidden status to existing product tables if needed.
# Existing products become active by default.
connection = get_db_connection()
try:
    product_columns = connection.execute("PRAGMA table_info(products)").fetchall()
    product_column_names = [column["name"] for column in product_columns]
    if "active" not in product_column_names:
        connection.execute("ALTER TABLE products ADD COLUMN active INTEGER DEFAULT 1")
        connection.commit()
finally:
    connection.close()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def is_admin_logged_in():
    """
    Check whether admin is logged in.
    """

    return session.get("admin_logged_in", False) is True


def admin_required():
    """
    Return redirect response if admin is not logged in.
    """

    if not is_admin_logged_in():
        return redirect(url_for("admin_login"))

    return None


def valid_mobile(mobile):
    """
    Basic Indian mobile validation.
    """

    return (
        mobile.isdigit()
        and len(mobile) == 10
        and mobile[0] in "6789"
    )


def valid_pincode(pincode):
    """
    Basic Indian pincode validation.
    """

    return (
        pincode.isdigit()
        and len(pincode) == 6
        and pincode[0] != "0"
    )


def create_notification(
    connection,
    order,
    message,
    notification_type
):
    """
    Create local database notification.
    """

    connection.execute("""
        INSERT INTO notifications (
            order_id,
            customer_name,
            mobile,
            message,
            notification_type
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        order["id"],
        order["customer_name"],
        order["mobile"],
        message,
        notification_type
    ))


# ============================================================
# CUSTOMER HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# CHECKOUT PAGE
# ============================================================

@app.route("/checkout")
def checkout():

    return render_template(
        "checkout.html"
    )

# =========================
# ORDER SUCCESS PAGE
# =========================

@app.route("/order-success")
def order_success():
    return render_template("order_success.html")
# ============================================================
# TRACK ORDER PAGE
# ============================================================

@app.route("/track-order")
def track_order():

    return render_template(
        "track_order.html"
    )


# ============================================================
# GET ALL PRODUCTS
# ============================================================

@app.route("/api/products", methods=["GET"])
def get_products():

    connection = get_db_connection()

    try:

        products = connection.execute("""
            SELECT *
            FROM products
            ORDER BY id DESC
        """).fetchall()

        return jsonify([
            dict(product)
            for product in products
        ])

    finally:

        connection.close()


# ============================================================
# PLACE ORDER
# ============================================================

@app.route("/api/orders", methods=["POST"])
def place_order():

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Invalid request."
        }), 400


    customer_name = str(
        data.get("customer_name", "")
    ).strip()

    mobile = str(
        data.get("mobile", "")
    ).strip()

    address = str(
        data.get("address", "")
    ).strip()

    pincode = str(
        data.get("pincode", "")
    ).strip()

    items = data.get("items", [])


    # --------------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------------

    if not customer_name:

        return jsonify({
            "error": "Customer name is required."
        }), 400


    if len(customer_name) > 100:

        return jsonify({
            "error": "Customer name is too long."
        }), 400


    if not valid_mobile(mobile):

        return jsonify({
            "error": "Please enter a valid 10-digit mobile number."
        }), 400


    if not address:

        return jsonify({
            "error": "Address is required."
        }), 400


    if len(address) > 500:

        return jsonify({
            "error": "Address is too long."
        }), 400


    if not valid_pincode(pincode):

        return jsonify({
            "error": "Please enter a valid 6-digit pincode."
        }), 400


    if not isinstance(items, list) or not items:

        return jsonify({
            "error": "Cart is empty."
        }), 400


    # Prevent unnecessarily huge carts
    if len(items) > 50:

        return jsonify({
            "error": "Too many different products in cart."
        }), 400


    connection = get_db_connection()


    try:

        total = 0
        order_items = []


        # ----------------------------------------------------
        # CHECK PRODUCTS + STOCK
        # ----------------------------------------------------

        for item in items:

            try:

                product_id = int(
                    item.get("id")
                )

                quantity = int(
                    item.get("quantity", 0)
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({
                    "error": "Invalid product or quantity."
                }), 400


            if product_id <= 0 or quantity <= 0:

                return jsonify({
                    "error": "Invalid product or quantity."
                }), 400


            # Prevent unrealistic quantity
            if quantity > 100:

                return jsonify({
                    "error": "Maximum quantity per product is 100."
                }), 400


            product = connection.execute("""
                SELECT *
                FROM products
                WHERE id = ?
                AND active = 1
            """, (
                product_id,
            )).fetchone()


            if not product:

                return jsonify({
                    "error":
                    f"Product with ID {product_id} not found."
                }), 404


            if product["stock"] < quantity:

                return jsonify({
                    "error":
                    f"Only {product['stock']} items available "
                    f"for {product['name']}."
                }), 400


            subtotal = product["price"] * quantity

            total += subtotal


            order_items.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "price": product["price"],
                "quantity": quantity,
                "subtotal": subtotal
            })


        # ----------------------------------------------------
        # FORCE COD
        # ----------------------------------------------------

        payment_method = "COD"
        payment_status = "Pending"


        # ----------------------------------------------------
        # CREATE ORDER
        # ----------------------------------------------------

        cursor = connection.execute("""
            INSERT INTO orders (
                customer_name,
                mobile,
                address,
                pincode,
                total,
                status,
                payment_method,
                payment_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_name,
            mobile,
            address,
            pincode,
            total,
            "Order Placed",
            payment_method,
            payment_status
        ))


        order_id = cursor.lastrowid


        # ----------------------------------------------------
        # INSERT ORDER ITEMS + REDUCE STOCK
        # ----------------------------------------------------

        for item in order_items:

            connection.execute("""
                INSERT INTO order_items (
                    order_id,
                    product_id,
                    product_name,
                    price,
                    quantity,
                    subtotal
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                order_id,
                item["product_id"],
                item["product_name"],
                item["price"],
                item["quantity"],
                item["subtotal"]
            ))


            connection.execute("""
                UPDATE products
                SET stock = stock - ?
                WHERE id = ?
                AND stock >= ?
            """, (
                item["quantity"],
                item["product_id"],
                item["quantity"]
            ))


        # ----------------------------------------------------
        # FIRST NOTIFICATION
        # ----------------------------------------------------

        message = (
            f"Hi {customer_name}, your MyShop order "
            f"#{order_id} has been placed successfully. "
            f"Total: ₹{total:.2f}. "
            f"Payment: Cash on Delivery. "
            f"Expected delivery: within 7 days."
        )


        connection.execute("""
            INSERT INTO notifications (
                order_id,
                customer_name,
                mobile,
                message,
                notification_type
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            order_id,
            customer_name,
            mobile,
            message,
            "Order Placed"
        ))


        connection.commit()


        return jsonify({
            "success": True,
            "message": "Order placed successfully!",
            "order_id": order_id,
            "total": total
        }), 201


    except Exception as error:

        connection.rollback()

        print(
            "Order Error:",
            error
        )

        return jsonify({
            "error": "Unable to place order."
        }), 500


    finally:

        connection.close()


# ============================================================
# TRACK ORDER API
# ============================================================

@app.route("/api/track-order", methods=["POST"])
def api_track_order():

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Invalid request."
        }), 400


    order_id = data.get("order_id")

    mobile = str(
        data.get("mobile", "")
    ).strip()


    try:

        order_id = int(order_id)

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "error": "Invalid Order ID."
        }), 400


    if order_id <= 0:

        return jsonify({
            "error": "Invalid Order ID."
        }), 400


    if not valid_mobile(mobile):

        return jsonify({
            "error": "Please enter a valid mobile number."
        }), 400


    connection = get_db_connection()


    try:

        order = connection.execute("""
            SELECT *
            FROM orders
            WHERE id = ?
            AND mobile = ?
        """, (
            order_id,
            mobile
        )).fetchone()


        if not order:

            return jsonify({
                "error":
                "Order not found. Please check Order ID "
                "and mobile number."
            }), 404


        # ----------------------------------------------------
        # ORDER ITEMS
        # ----------------------------------------------------

        order_items = connection.execute("""
            SELECT *
            FROM order_items
            WHERE order_id = ?
            ORDER BY id ASC
        """, (
            order_id,
        )).fetchall()


        # ----------------------------------------------------
        # NOTIFICATIONS
        # ----------------------------------------------------

        notifications = connection.execute("""
            SELECT *
            FROM notifications
            WHERE order_id = ?
            ORDER BY id DESC
        """, (
            order_id,
        )).fetchall()


        return jsonify({

            "order": dict(order),

            "order_items": [
                dict(item)
                for item in order_items
            ],

            "notifications": [
                dict(notification)
                for notification in notifications
            ]

        })


    finally:

        connection.close()


# ============================================================
# ADMIN LOGIN PAGE
# ============================================================

@app.route(
    "/admin",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):

            session.clear()

            session["admin_logged_in"] = True

            return redirect(
                url_for("admin_dashboard")
            )


        return render_template(
            "admin/admin_login.html",
            error="Invalid username or password."
        )


    return render_template(
        "admin/admin_login.html"
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin/dashboard")
def admin_dashboard():

    auth = admin_required()

    if auth:

        return auth


    connection = get_db_connection()


    try:

        # ----------------------------------------------------
        # PRODUCTS
        # ----------------------------------------------------

        products = connection.execute("""
            SELECT *
            FROM products
            ORDER BY id DESC
        """).fetchall()


        # ----------------------------------------------------
        # ORDERS
        # ----------------------------------------------------

        orders = connection.execute("""
            SELECT *
            FROM orders
            ORDER BY id DESC
        """).fetchall()


        # ----------------------------------------------------
        # NOTIFICATIONS
        # ----------------------------------------------------

        notifications = connection.execute("""
            SELECT *
            FROM notifications
            ORDER BY id DESC
        """).fetchall()


        return render_template(
            "admin/dashboard.html",
            products=products,
            orders=orders,
            notifications=notifications
        )

    finally:

        connection.close()


# ============================================================
# ADMIN ORDER DETAILS
# ============================================================

@app.route("/admin/order/<int:order_id>")
def order_details(order_id):

    auth = admin_required()

    if auth:

        return auth


    connection = get_db_connection()


    try:

        # ----------------------------------------------------
        # ORDER
        # ----------------------------------------------------

        order = connection.execute("""
            SELECT *
            FROM orders
            WHERE id = ?
        """, (
            order_id,
        )).fetchone()


        if not order:

            return "Order not found", 404


        # ----------------------------------------------------
        # ORDER ITEMS
        # ----------------------------------------------------

        items = connection.execute("""
            SELECT *
            FROM order_items
            WHERE order_id = ?
            ORDER BY id ASC
        """, (
            order_id,
        )).fetchall()


        # ----------------------------------------------------
        # NOTIFICATIONS
        # ----------------------------------------------------

        notifications = connection.execute("""
            SELECT *
            FROM notifications
            WHERE order_id = ?
            ORDER BY id DESC
        """, (
            order_id,
        )).fetchall()


        return render_template(
            "admin/order_details.html",
            order=order,
            items=items,
            notifications=notifications
        )

    finally:

        connection.close()


# ============================================================
# UPDATE ORDER STATUS
# ============================================================

@app.route(
    "/admin/update-order-status/<int:order_id>",
    methods=["POST"]
)
def update_order_status(order_id):

    auth = admin_required()

    if auth:

        return auth


    new_status = request.form.get(
        "status",
        ""
    ).strip()


    if new_status not in ALLOWED_ORDER_STATUSES:

        return "Invalid status", 400


    connection = get_db_connection()


    try:

        # ----------------------------------------------------
        # GET CURRENT ORDER
        # ----------------------------------------------------

        order = connection.execute("""
            SELECT *
            FROM orders
            WHERE id = ?
        """, (
            order_id,
        )).fetchone()


        if not order:

            return "Order not found", 404


        old_status = order["status"]


        # ----------------------------------------------------
        # NO CHANGE
        # ----------------------------------------------------

        if old_status == new_status:

            return redirect(
                url_for(
                    "order_details",
                    order_id=order_id
                )
            )


        # ----------------------------------------------------
        # GET ORDER ITEMS
        # ----------------------------------------------------

        items = connection.execute("""
            SELECT *
            FROM order_items
            WHERE order_id = ?
        """, (
            order_id,
        )).fetchall()


        # ----------------------------------------------------
        # CANCEL ORDER
        # RESTORE STOCK ONLY ONCE
        # ----------------------------------------------------

        if (
            new_status == "Cancelled"
            and old_status != "Cancelled"
        ):

            for item in items:

                connection.execute("""
                    UPDATE products
                    SET stock = stock + ?
                    WHERE id = ?
                """, (
                    item["quantity"],
                    item["product_id"]
                ))


        # ----------------------------------------------------
        # PREVENT RESTOCKING AGAIN
        # ----------------------------------------------------

        if (
            old_status == "Cancelled"
            and new_status != "Cancelled"
        ):

            return (
                "A cancelled order cannot be reactivated.",
                400
            )


        # ----------------------------------------------------
        # UPDATE STATUS
        # ----------------------------------------------------

        connection.execute("""
            UPDATE orders
            SET status = ?
            WHERE id = ?
        """, (
            new_status,
            order_id
        ))


        # ----------------------------------------------------
        # STATUS NOTIFICATION
        # ----------------------------------------------------

        message = (
            f"Hi {order['customer_name']}, "
            f"your MyShop order #{order_id} "
            f"status is now '{new_status}'."
        )


        create_notification(
            connection,
            order,
            message,
            new_status
        )


        connection.commit()


        return redirect(
            url_for(
                "order_details",
                order_id=order_id
            )
        )


    except Exception as error:

        connection.rollback()

        print(
            "Status Update Error:",
            error
        )

        return "Unable to update order status.", 500


    finally:

        connection.close()


# ============================================================
# ADMIN MARK PAYMENT AS PAID
# ============================================================

@app.route(
    "/admin/mark-payment-paid/<int:order_id>",
    methods=["POST"]
)
def mark_payment_paid(order_id):

    auth = admin_required()

    if auth:

        return auth


    connection = get_db_connection()


    try:

        # ----------------------------------------------------
        # GET ORDER
        # ----------------------------------------------------

        order = connection.execute("""
            SELECT *
            FROM orders
            WHERE id = ?
        """, (
            order_id,
        )).fetchone()


        if not order:

            return "Order not found", 404


        # ----------------------------------------------------
        # CANCELLED ORDER
        # ----------------------------------------------------

        if order["status"] == "Cancelled":

            return (
                "Cancelled order cannot be marked as paid.",
                400
            )


        # ----------------------------------------------------
        # PAYMENT ALREADY PAID
        # ----------------------------------------------------

        if order["payment_status"] == "Paid":

            return redirect(
                url_for(
                    "order_details",
                    order_id=order_id
                )
            )


        # ----------------------------------------------------
        # UPDATE PAYMENT
        # ----------------------------------------------------

        connection.execute("""
            UPDATE orders
            SET payment_status = ?
            WHERE id = ?
        """, (
            "Paid",
            order_id
        ))


        # ----------------------------------------------------
        # PAYMENT NOTIFICATION
        # ----------------------------------------------------

        message = (
            f"Hi {order['customer_name']}, "
            f"payment for your MyShop order "
            f"#{order_id} has been received successfully."
        )


        create_notification(
            connection,
            order,
            message,
            "Payment Received"
        )


        connection.commit()


        return redirect(
            url_for(
                "order_details",
                order_id=order_id
            )
        )


    except Exception as error:

        connection.rollback()

        print(
            "Payment Update Error:",
            error
        )

        return "Unable to update payment status.", 500


    finally:

        connection.close()


# ============================================================
# ADMIN ADD PRODUCT
# ============================================================

@app.route(
    "/admin/add-product",
    methods=["GET", "POST"]
)
def add_product():

    auth = admin_required()

    if auth:

        return auth


    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        price = request.form.get(
            "price",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        image = request.form.get(
            "image",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        stock = request.form.get(
            "stock",
            "0"
        ).strip()


        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not name or not price or not category:

            return render_template(
                "admin/add_product.html",
                error=(
                    "Name, price and category "
                    "are required."
                )
            )


        if len(name) > 150:

            return render_template(
                "admin/add_product.html",
                error="Product name is too long."
            )


        try:

            price = float(price)
            stock = int(stock)

            if price <= 0 or stock < 0:

                raise ValueError

        except ValueError:

            return render_template(
                "admin/add_product.html",
                error="Invalid price or stock."
            )


        connection = get_db_connection()


        try:

            connection.execute("""
                INSERT INTO products (
                    name,
                    price,
                    category,
                    image,
                    description,
                    stock
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                name,
                price,
                category,
                image,
                description,
                stock
            ))


            connection.commit()


        finally:

            connection.close()


        return redirect(
            url_for("admin_dashboard")
        )


    return render_template(
        "admin/add_product.html"
    )


# ============================================================
# ADMIN EDIT PRODUCT
# ============================================================

@app.route(
    "/admin/edit-product/<int:product_id>",
    methods=["GET", "POST"]
)
def edit_product(product_id):

    auth = admin_required()

    if auth:

        return auth


    connection = get_db_connection()


    try:

        product = connection.execute("""
            SELECT *
            FROM products
            WHERE id = ?
        """, (
            product_id,
        )).fetchone()


        if not product:

            return "Product not found", 404


        if request.method == "POST":

            name = request.form.get(
                "name",
                ""
            ).strip()

            price = request.form.get(
                "price",
                ""
            ).strip()

            category = request.form.get(
                "category",
                ""
            ).strip()

            image = request.form.get(
                "image",
                ""
            ).strip()

            description = request.form.get(
                "description",
                ""
            ).strip()

            stock = request.form.get(
                "stock",
                "0"
            ).strip()


            if not name or not price or not category:

                return render_template(
                    "admin/edit_product.html",
                    product=product,
                    error=(
                        "Name, price and category "
                        "are required."
                    )
                )


            try:

                price = float(price)
                stock = int(stock)

                if price <= 0 or stock < 0:

                    raise ValueError

            except ValueError:

                return render_template(
                    "admin/edit_product.html",
                    product=product,
                    error="Invalid price or stock."
                )


            connection.execute("""
                UPDATE products
                SET
                    name = ?,
                    price = ?,
                    category = ?,
                    image = ?,
                    description = ?,
                    stock = ?
                WHERE id = ?
            """, (
                name,
                price,
                category,
                image,
                description,
                stock,
                product_id
            ))


            connection.commit()


            return redirect(
                url_for("admin_dashboard")
            )


        return render_template(
            "admin/edit_product.html",
            product=product
        )


    finally:

        connection.close()


# ============================================================
# ADMIN HIDE / SHOW PRODUCT
# ============================================================

@app.route(
    "/admin/toggle-product/<int:product_id>",
    methods=["POST"]
)
def toggle_product(product_id):

    auth = admin_required()
    if auth:
        return auth

    connection = get_db_connection()

    try:
        product = connection.execute("""
            SELECT *
            FROM products
            WHERE id = ?
        """, (
            product_id,
        )).fetchone()

        if not product:
            return "Product not found", 404

        new_active = 0 if int(product["active"] or 0) == 1 else 1

        connection.execute("""
            UPDATE products
            SET active = ?
            WHERE id = ?
        """, (
            new_active,
            product_id
        ))

        connection.commit()

        return redirect(
            url_for("admin_dashboard")
        )

    except Exception as error:
        connection.rollback()
        print("Toggle Product Error:", error)
        return "Unable to update product status.", 500

    finally:
        connection.close()


# ============================================================
# ADMIN DELETE PRODUCT
# ============================================================

@app.route(
    "/admin/delete-product/<int:product_id>",
    methods=["POST"]
)
def delete_product(product_id):

    auth = admin_required()

    if auth:

        return auth


    connection = get_db_connection()


    try:

        # ----------------------------------------------------
        # CHECK PRODUCT
        # ----------------------------------------------------

        product = connection.execute("""
            SELECT *
            FROM products
            WHERE id = ?
        """, (
            product_id,
        )).fetchone()


        if not product:

            return "Product not found", 404


        # ----------------------------------------------------
        # CHECK WHETHER PRODUCT EXISTS IN ORDERS
        # ----------------------------------------------------

        ordered = connection.execute("""
            SELECT id
            FROM order_items
            WHERE product_id = ?
            LIMIT 1
        """, (
            product_id,
        )).fetchone()


        if ordered:

            return (
                "This product is already part of an order "
                "and cannot be deleted.",
                400
            )


        # ----------------------------------------------------
        # DELETE
        # ----------------------------------------------------

        connection.execute("""
            DELETE FROM products
            WHERE id = ?
        """, (
            product_id,
        ))


        connection.commit()


        return redirect(
            url_for("admin_dashboard")
        )


    except Exception as error:

        connection.rollback()

        print(
            "Delete Product Error:",
            error
        )

        return "Unable to delete product.", 500


    finally:

        connection.close()


# ============================================================
# ADMIN LOGOUT
# ============================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("admin_login")
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=False
    )