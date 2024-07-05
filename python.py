import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from argparse import ArgumentParser, RawTextHelpFormatter

# Product class to store product details
class Item:
    def __init__(self, item_id, name, category, price, quantity):
        self.item_id = item_id
        self.name = name
        self.category = category
        self.price = price
        self.quantity = quantity

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "quantity": self.quantity
        }

    @staticmethod
    def from_dict(data):
        return Item(
            data["item_id"],
            data["name"],
            data["category"],
            data["price"],
            data["quantity"]
        )

# Inventory class to manage the list of products
class Stock:
    def __init__(self):
        self.items = {}
        self.load_items()

    def add_item(self, item):
        self.items[item.item_id] = item
        self.save_items()

    def update_item(self, item_id, name=None, category=None, price=None, quantity=None):
        if item_id in self.items:
            if name:
                self.items[item_id].name = name
            if category:
                self.items[item_id].category = category
            if price:
                self.items[item_id].price = price
            if quantity:
                self.items[item_id].quantity = quantity
            self.save_items()

    def remove_item(self, item_id):
        if item_id in self.items:
            del self.items[item_id]
            self.save_items()

    def view_items(self):
        return self.items.values()

    def save_items(self):
        with open("items.json", "w") as f:
            json.dump([item.to_dict() for item in self.items.values()], f)

    def load_items(self):
        if os.path.exists("items.json"):
            with open("items.json", "r") as f:
                items_data = json.load(f)
                self.items = {data["item_id"]: Item.from_dict(data) for data in items_data}

# Transaction class to represent sales and returns
class Transaction:
    def __init__(self, transaction_id, item_id, quantity, price, date):
        self.transaction_id = transaction_id
        self.item_id = item_id
        self.quantity = quantity
        self.price = price
        self.date = date

# Sale class inherited from Transaction
class Sale(Transaction):
    pass

# Return class inherited from Transaction with an additional reason attribute
class Return(Transaction):
    def __init__(self, transaction_id, item_id, quantity, price, date, reason):
        super().__init__(transaction_id, item_id, quantity, price, date)
        self.reason = reason

# Invoice class to generate PDF invoices
class Bill:
    def __init__(self, invoice_id, sales):
        self.invoice_id = invoice_id
        self.sales = sales

    def generate_pdf(self):
        if not os.path.exists("bills"):
            os.makedirs("bills")
        # Create a canvas
        c = canvas.Canvas(f"bills/invoice_{self.invoice_id}.pdf", pagesize=letter)
        
        # Set up PDF content
        c.setFont("Helvetica", 12)
        c.drawString(100, 750, f"Invoice ID: {self.invoice_id}")
        c.drawString(100, 730, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        c.drawString(100, 710, "---------------------------------------")
        
        # Calculate total amount
        total_amount = 0
        
        y_position = 690
        for sale in self.sales:
            item = stock.items[sale.item_id]
            line_item = f"Item: {item.name}, Quantity: {sale.quantity}, Price: {sale.price}, Date: {sale.date}"
            c.drawString(100, y_position, line_item)
            total_amount += float(sale.quantity) * float(sale.price)
            y_position -= 20  # Adjust the y position for the next line item

        c.drawString(100, y_position - 20, f"Total Amount: ${total_amount:.2f}")
        c.save()
        print(f"Invoice generated successfully with ID: {self.invoice_id}")

# Initialize stock
stock = Stock()

# CLI Handling Functions
def add_item(args):
    item = Item(args.item_id, args.name, args.category, args.price, args.quantity)
    stock.add_item(item)
    print("Item added successfully!")

def update_item(args):
    stock.update_item(args.item_id, args.name, args.category, args.price, args.quantity)
    print("Item updated successfully!")

def remove_item(args):
    stock.remove_item(args.item_id)
    print("Item removed successfully!")

def view_items(args):
    items = stock.view_items()
    for item in items:
        print(f"ID: {item.item_id}, Name: {item.name}, Category: {item.category}, Price: {item.price}, Quantity: {item.quantity}")

def record_sale(args):
    if args.item_id not in stock.items:
        print(f"Error: Item ID {args.item_id} not found in the inventory.")
        return

    item = stock.items[args.item_id]
    if item.quantity < args.quantity:
        print(f"Error: Insufficient quantity for Item ID {args.item_id}. Available: {item.quantity}, Requested: {args.quantity}")
        return

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sale = Sale(None, args.item_id, args.quantity, args.price, date)
    stock.items[args.item_id].quantity -= args.quantity
    stock.save_items()
    print("Sale recorded successfully!")

def record_return(args):
    if args.item_id not in stock.items:
        print(f"Error: Item ID {args.item_id} not found in the inventory.")
        return

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return_txn = Return(None, args.item_id, args.quantity, args.price, date, args.reason)
    stock.items[args.item_id].quantity += args.quantity
    stock.save_items()
    print("Return recorded successfully!")

def generate_invoice(args):
    sales = []
    for sale_data in args.sales:
        item_id, quantity, price = sale_data.split(',')
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sale = Sale(None, item_id, int(quantity), float(price), date)
        sales.append(sale)

    invoice_id = datetime.now().strftime("%Y%m%d%H%M%S")
    bill = Bill(invoice_id, sales)
    bill.generate_pdf()

# CLI Setup
parser = ArgumentParser(description="Advanced Inventory Management System CLI", formatter_class=RawTextHelpFormatter)
subparsers = parser.add_subparsers()

# Add Item Command
parser_add = subparsers.add_parser("add_item", help="Add a new item")
parser_add.add_argument("item_id", type=str, help="Item ID")
parser_add.add_argument("name", type=str, help="Item name")
parser_add.add_argument("category", type=str, help="Item category")
parser_add.add_argument("price", type=float, help="Item price")
parser_add.add_argument("quantity", type=int, help="Item quantity")
parser_add.set_defaults(func=add_item)

# Update Item Command
parser_update = subparsers.add_parser("update_item", help="Update an existing item")
parser_update.add_argument("item_id", type=str, help="Item ID")
parser_update.add_argument("--name", type=str, help="New item name")
parser_update.add_argument("--category", type=str, help="New item category")
parser_update.add_argument("--price", type=float, help="New item price")
parser_update.add_argument("--quantity", type=int, help="New item quantity")
parser_update.set_defaults(func=update_item)

# Remove Item Command
parser_remove = subparsers.add_parser("remove_item", help="Remove an existing item")
parser_remove.add_argument("item_id", type=str, help="Item ID")
parser_remove.set_defaults(func=remove_item)

# View Items Command
parser_view = subparsers.add_parser("view_items", help="View all items")
parser_view.set_defaults(func=view_items)

# Record Sale Command
parser_sale = subparsers.add_parser("record_sale", help="Record a sale transaction")
parser_sale.add_argument("item_id", type=str, help="Item ID")
parser_sale.add_argument("quantity", type=int, help="Quantity sold")
parser_sale.add_argument("price", type=float, help="Sale price")
parser_sale.set_defaults(func=record_sale)

# Record Return Command
parser_return = subparsers.add_parser("record_return", help="Record a return transaction")
parser_return.add_argument("item_id", type=str, help="Item ID")
parser_return.add_argument("quantity", type=int, help="Quantity returned")
parser_return.add_argument("price", type=float, help="Return price")
parser_return.add_argument("reason", type=str, help="Reason for return")
parser_return.set_defaults(func=record_return)

# Generate Invoice Command
parser_invoice = subparsers.add_parser("generate_invoice", help="Generate an invoice for sales")
parser_invoice.add_argument("sales", type=str, nargs='+', help="Sales data in the format item_id,quantity,price")
parser_invoice.set_defaults(func=generate_invoice)

# Parse Arguments
args = parser.parse_args()
if hasattr(args, "func"):
    args.func(args)
else:
    parser.print_help()




