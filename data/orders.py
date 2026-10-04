ORDERS = {
    "ORD-1001": {"customer_name": "Maria Alvarez", "item": "Wireless Mouse", "status": "shipped", "amount_paid": 24.99},
    "ORD-1002": {"customer_name": "Tom Becker", "item": "Desk Lamp", "status": "delivered", "amount_paid": 39.50},
    "ORD-1003": {"customer_name": "Priya Nair", "item": "Bluetooth Speaker", "status": "processing", "amount_paid": 59.00},
    "ORD-1004": {"customer_name": "Liam Chen", "item": "Phone Case", "status": "delivered", "amount_paid": 15.99},
    "ORD-1005": {"customer_name": "Sara Kim", "item": "Laptop Stand", "status": "cancelled", "amount_paid": 45.00},
    "ORD-1006": {"customer_name": "David Osei", "item": "Keyboard", "status": "refunded", "amount_paid": 69.99},
    "ORD-1007": {"customer_name": "Elena Petrova", "item": "Webcam", "status": "shipped", "amount_paid": 54.25},
    "ORD-1008": {"customer_name": "Noah Dubois", "item": "USB Hub", "status": "delivered", "amount_paid": 19.99},
    "ORD-1009": {"customer_name": "Aisha Bello", "item": "Monitor Stand", "status": "processing", "amount_paid": 32.00},
    "ORD-1010": {"customer_name": "James Walsh", "item": "Noise-Cancelling Headphones", "status": "delivered", "amount_paid": 89.99},
}


def get_order_record(order_id: str) -> dict | None:
    return ORDERS.get(order_id)
