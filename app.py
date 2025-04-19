import os
import csv
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from config import Config
import sqlite3

# Ensure instance directory exists
os.makedirs('instance', exist_ok=True)

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Model definition
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    display_case = db.Column(db.String(10), nullable=False)  # I, II, III, IV, etc.
    column = db.Column(db.Integer, nullable=False)  # 1 or 2
    row = db.Column(db.Integer, nullable=False)  # 1-7

    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'display_case': self.display_case,
            'column': self.column,
            'row': self.row
        }

# Create database tables
def init_db():
    with app.app_context():
        db.create_all()

# Initialize the database
init_db()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    sku = request.form.get('sku').upper()  # Convert to uppercase for search
    product = Product.query.filter_by(sku=sku).first()
    
    if product:
        return jsonify({
            'found': True,
            'product': product.to_dict()
        })
    else:
        return jsonify({
            'found': False
        })

@app.route('/products')
def products():
    return render_template('products.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products])

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    
    # Check if product with this SKU already exists
    existing_product = Product.query.filter_by(sku=data['sku']).first()
    if existing_product:
        return jsonify({'success': False, 'message': 'Product with this SKU already exists'}), 400
    
    # Validate data
    if not data['sku'] or not data['display_case'] or not data['column'] or not data['row']:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    # Validate column and row
    try:
        column = int(data['column'])
        row = int(data['row'])
        if column not in [1, 2] or row < 1 or row > 7:
            return jsonify({'success': False, 'message': 'Invalid column or row value'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Column and row must be numbers'}), 400
    
    # Create new product - store SKU in uppercase
    product = Product(
        sku=data['sku'].upper(),
        display_case=data['display_case'],
        column=column,
        row=row
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify({'success': True, 'product': product.to_dict()})

@app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.json
    
    # Check if updating to an existing SKU (that's not this product's SKU)
    if data['sku'] != product.sku:
        existing_product = Product.query.filter_by(sku=data['sku']).first()
        if existing_product:
            return jsonify({'success': False, 'message': 'Product with this SKU already exists'}), 400
    
    # Validate data
    if not data['sku'] or not data['display_case'] or not data['column'] or not data['row']:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    # Validate column and row
    try:
        column = int(data['column'])
        row = int(data['row'])
        if column not in [1, 2] or row < 1 or row > 7:
            return jsonify({'success': False, 'message': 'Invalid column or row value'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Column and row must be numbers'}), 400
    
    # Update product - store SKU in uppercase
    product.sku = data['sku'].upper()
    product.display_case = data['display_case']
    product.column = column
    product.row = row
    
    db.session.commit()
    
    return jsonify({'success': True, 'product': product.to_dict()})

@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'message': 'File must be a CSV'}), 400
    
    # Process CSV file
    try:
        # Read CSV file
        csv_data = file.read().decode('utf-8').splitlines()
        reader = csv.reader(csv_data)
        
        # Skip header row if exists
        next(reader, None)
        
        success_count = 0
        error_count = 0
        errors = []
        
        for row in reader:
            if len(row) != 4:
                error_count += 1
                errors.append(f"Row has incorrect number of columns: {row}")
                continue
            
            sku, display_case, column, row_num = row
            sku = sku.upper()  # Convert SKU to uppercase
            
            # Validate data
            try:
                column = int(column)
                row_num = int(row_num)
                print(sku,display_case, column, row_num)
                # Provide more specific error messages
                if column not in [1, 2]:
                    error_count += 1
                    errors.append(f"Invalid column value for SKU {sku}. Column must be 1 or 2.")
                    continue
                
                if row_num < 1 or row_num > 7:
                    error_count += 1
                    errors.append(f"Invalid row value for SKU {sku}. Row must be between 1 and 7.")
                    continue
            except ValueError:
                error_count += 1
                errors.append(f"Column and row must be numbers for SKU {sku}")
                continue
            
            # Check if product with this SKU already exists
            existing_product = Product.query.filter_by(sku=sku).first()
            if existing_product:
                # Update existing product
                existing_product.display_case = display_case
                existing_product.column = column
                existing_product.row = row_num
            else:
                # Create new product
                product = Product(
                    sku=sku,
                    display_case=display_case,
                    column=column,
                    row=row_num
                )
                db.session.add(product)
            
            success_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Processed {success_count} products successfully, {error_count} errors",
            'errors': errors
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)