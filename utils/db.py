import random
import mysql.connector
from datetime import datetime, timedelta


conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Shiva@2001"
)
cursor = conn.cursor()

cursor.execute("CREATE DATABASE IF NOT EXISTS retail_demo")
print("✅ Database created")


cursor.execute("USE retail_demo")




conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Shiva@2001",
    database="retail_demo"
)

cursor = conn.cursor()

# ---------------------------
# 1. INSERT CUSTOMERS
# ---------------------------
customer_ids = []

for i in range(20):
    cursor.execute("""
        INSERT INTO customers 
        (first_name, last_name, email, phone, address, city, state, zip_code)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        f"First{i}",
        f"Last{i}",
        f"user{i}@mail.com",
        f"90000000{i}",
        f"Address {i}",
        random.choice(["Hyderabad", "Bangalore", "Chennai"]),
        random.choice(["Telangana", "Karnataka", "Tamil Nadu"]),
        f"5000{i}"
    ))
    customer_ids.append(cursor.lastrowid)

# ---------------------------
# 2. INSERT PRODUCTS
# ---------------------------
product_ids = []

for i in range(20):
    cursor.execute("""
        INSERT INTO products 
        (name, category, price, stock, brand, rating, supplier)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        f"Product{i}",
        random.choice(["Electronics", "Clothing"]),
        round(random.uniform(100, 1000), 2),
        random.randint(1, 100),
        random.choice(["BrandX", "BrandY"]),
        round(random.uniform(1, 5), 1),
        "SupplierY"
    ))
    product_ids.append(cursor.lastrowid)

# ---------------------------
# 3. INSERT ORDERS
# ---------------------------
order_ids = []

for i in range(20):
    customer_id = random.choice(customer_ids)

    order_date = datetime.now() - timedelta(days=random.randint(0, 30))

    cursor.execute("""
        INSERT INTO orders
        (customer_id, order_date, status, total_amount, shipping_address,
         shipping_city, shipping_state, shipping_zip)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        customer_id,
        order_date.date(),
        random.choice(["PLACED", "SHIPPED", "DELIVERED"]),
        0,  # will update later
        f"Address {i}",
        "City",
        "State",
        "500001"
    ))

    order_ids.append(cursor.lastrowid)

# ---------------------------
# 4. INSERT ORDER ITEMS
# ---------------------------
order_totals = {}

for order_id in order_ids:
    total_amount = 0

    for _ in range(random.randint(1, 3)):  # each order 1–3 items
        product_id = random.choice(product_ids)
        quantity = random.randint(1, 5)
        price = round(random.uniform(100, 1000), 2)
        discount = round(random.uniform(0, 50), 2)
        tax = round(price * 0.1, 2)

        total = (price * quantity) - discount + tax
        total_amount += total

        cursor.execute("""
            INSERT INTO order_items
            (order_id, product_id, quantity, price, discount, tax, total)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            order_id,
            product_id,
            quantity,
            price,
            discount,
            tax,
            total
        ))

    order_totals[order_id] = round(total_amount, 2)

# ---------------------------
# 5. UPDATE ORDER TOTALS
# ---------------------------
for order_id, total in order_totals.items():
    cursor.execute("""
        UPDATE orders SET total_amount = %s WHERE order_id = %s
    """, (total, order_id))

# ---------------------------
# 6. INSERT PAYMENTS
# ---------------------------
for order_id in order_ids:
    cursor.execute("""
        INSERT INTO payments
        (order_id, payment_method, payment_status, amount,
         transaction_id, payment_date, currency, gateway)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        order_id,
        random.choice(["UPI", "CARD", "NETBANKING"]),
        random.choice(["SUCCESS", "FAILED", "PENDING"]),
        order_totals[order_id],
        f"TXN{random.randint(10000,99999)}",
        datetime.now().date(),
        "INR",
        random.choice(["Razorpay", "Stripe"])
    ))

# ---------------------------
# FINAL COMMIT
# ---------------------------
conn.commit()
cursor.close()
conn.close()

print("✅ Data inserted successfully!")