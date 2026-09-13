import sqlite3


# Connect to database
conn = sqlite3.connect("shop.db")

cursor = conn.cursor()


# Remove duplicate products
cursor.execute("""
DELETE FROM products
WHERE id NOT IN (
    SELECT MIN(id)
    FROM products
    GROUP BY name
)
""")


# Save changes
conn.commit()


print("Duplicate products removed successfully!")


# Show remaining products
cursor.execute("""
SELECT id, name, price, stock
FROM products
ORDER BY id
""")


products = cursor.fetchall()


print("\nProducts in database:")


for product in products:
    print(product)


# Close database
conn.close()