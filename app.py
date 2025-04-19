import os
import csv
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
import sqlite3

# Ensure instance directory exists
os.makedirs('instance', exist_ok=True)

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'
login_manager.session_protection = "strong"

# Configure permanent session lifetime
app.permanent_session_lifetime = timedelta(days=365)  # 1 year

# Model definitions
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)  # New field for product name (required)
    display_case = db.Column(db.String(10), nullable=False)  # I, II, III, IV, etc.
    column = db.Column(db.Integer, nullable=False)  # 1 or 2
    row = db.Column(db.Integer, nullable=False)  # 1-7

    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'display_case': self.display_case,
            'column': self.column,
            'row': self.row
        }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables and default user
def init_db():
    with app.app_context():
        db.create_all()
        
        try:
            # Create default user if it doesn't exist
            existing_user = User.query.filter_by(username='vendedor').first()
            if not existing_user:
                default_user = User(username='vendedor')
                default_user.set_password('password123')
                db.session.add(default_user)
                try:
                    db.session.commit()
                    print("Default user 'vendedor' created with password 'password123'")
                except Exception as e:
                    # Handle potential race condition where another process created the user
                    # between our check and commit
                    db.session.rollback()
                    print(f"Could not create default user, it may already exist: {e}")
            else:
                print("Default user 'vendedor' already exists")
        except Exception as e:
            # Roll back the session in case of any error
            db.session.rollback()
            print(f"Error during database initialization: {e}")

# Initialize the database
init_db()

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Make session permanent and set remember=True
            session.permanent = True
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('La contraseña actual es incorrecta', 'danger')
        elif new_password != confirm_password:
            flash('Las nuevas contraseñas no coinciden', 'danger')
        elif len(new_password) < 6:
            flash('La nueva contraseña debe tener al menos 6 caracteres', 'danger')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Contraseña actualizada correctamente', 'success')
            return redirect(url_for('index'))
    
    return render_template('change_password.html')

# Application routes
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    search_term = request.form.get('search_term', '').strip()
    search_type = request.form.get('search_type', 'sku')  # Default to SKU search
    
    if search_type == 'sku':
        # Search by SKU (case-insensitive)
        product = Product.query.filter(Product.sku.ilike(f"{search_term.upper()}")).first()
        
        if product:
            return jsonify({
                'found': True,
                'multiple': False,
                'products': [product.to_dict()]
            })
        else:
            return jsonify({
                'found': False
            })
    else:
        # Search by name (case-insensitive) - return all matching products
        products = Product.query.filter(Product.name.ilike(f"%{search_term}%")).order_by(Product.display_case).all()
        
        if products:
            return jsonify({
                'found': True,
                'multiple': True,
                'products': [product.to_dict() for product in products]
            })
        else:
            return jsonify({
                'found': False
            })

@app.route('/products')
@login_required
def products():
    return render_template('products.html')

@app.route('/api/products', methods=['GET'])
@login_required
def get_products():
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    # Create base query
    query = Product.query
    
    # Apply search filter if provided
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    
    # Get total count for pagination
    total_count = query.count()
    
    # Apply pagination
    products = query.order_by(Product.sku, Product.display_case, Product.row)\
                   .paginate(page=page, per_page=per_page, error_out=False)
    
    # Return paginated results
    return jsonify({
        'products': [product.to_dict() for product in products.items],
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'pages': (total_count + per_page - 1) // per_page  # Ceiling division
    })

@app.route('/api/products', methods=['POST'])
@login_required
def add_product():
    data = request.json
    
    # Check if product with this SKU already exists
    existing_product = Product.query.filter_by(sku=data['sku']).first()
    if existing_product:
        return jsonify({'success': False, 'message': 'El producto con este SKU ya existe'}), 400
    
    # Validate data
    if not data['sku'] or not data['name'] or not data['display_case'] or not data['column'] or not data['row']:
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios'}), 400
    
    # Validate column and row
    try:
        column = int(data['column'])
        row = int(data['row'])
        if column not in [1, 2] or row < 1 or row > 7:
            return jsonify({'success': False, 'message': 'Valor de columna o fila no válido'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'La columna y la fila deben ser números'}), 400
    
    # Create new product - store SKU in uppercase
    product = Product(
        sku=data['sku'].upper(),
        name=data['name'],
        display_case=data['display_case'],
        column=column,
        row=row
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify({'success': True, 'product': product.to_dict()})

@app.route('/api/products/<int:id>', methods=['PUT'])
@login_required
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.json
    
    # Check if updating to an existing SKU (that's not this product's SKU)
    if data['sku'] != product.sku:
        existing_product = Product.query.filter_by(sku=data['sku']).first()
        if existing_product:
            return jsonify({'success': False, 'message': 'La columna y la fila deben ser números. El producto con este SKU ya existe.'}), 400
    
    # Validate data
    if not data['sku'] or not data['name'] or not data['display_case'] or not data['column'] or not data['row']:
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios'}), 400
    
    # Validate column and row
    try:
        column = int(data['column'])
        row = int(data['row'])
        if column not in [1, 2] or row < 1 or row > 7:
            return jsonify({'success': False, 'message': 'Valor de columna o fila no válido'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'La columna y la fila deben ser números'}), 400
    
    # Update product - store SKU in uppercase
    product.sku = data['sku'].upper()
    product.name = data['name']
    product.display_case = data['display_case']
    product.column = column
    product.row = row
    
    db.session.commit()
    
    return jsonify({'success': True, 'product': product.to_dict()})

@app.route('/api/products/<int:id>', methods=['DELETE'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/upload-csv', methods=['POST'])
@login_required
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No hay parte del archivo'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No hay ningún archivo seleccionado'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'message': 'El archivo debe ser un CSV'}), 400
    
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
            if len(row) != 5:  # Now we require 5 columns including name
                error_count += 1
                errors.append(f"La fila tiene un número incorrecto de columnas: {row}")
                continue
            
            sku, name, display_case, row_num, column = row  # Changed order: row before column
            sku = sku.upper()  # Convert SKU to uppercase
            
            # Validate data
            try:
                column = int(column)
                row_num = int(row_num)
                print(sku,display_case, column, row_num)
                # Provide more specific error messages
                if column not in [1, 2]:
                    error_count += 1
                    errors.append(f"El valor de columna para el SKU {sku} no es válido. La columna debe ser 1 o 2.")
                    continue
                
                if row_num < 1 or row_num > 7:
                    error_count += 1
                    errors.append(f"Valor de fila no válido para el SKU {sku}. La fila debe estar entre 1 y 7.")
                    continue
            except ValueError:
                error_count += 1
                errors.append(f"La columna y la fila deben ser números para el SKU {sku}")
                continue
            
            # Check if product with this SKU already exists
            existing_product = Product.query.filter_by(sku=sku).first()
            if existing_product:
                # Update existing product
                existing_product.name = name
                existing_product.display_case = display_case
                existing_product.column = column
                existing_product.row = row_num
            else:
                # Create new product
                product = Product(
                    sku=sku,
                    name=name,
                    display_case=display_case,
                    column=column,
                    row=row_num
                )
                db.session.add(product)
            
            success_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Se procesaron {success_count} productos con éxito, {error_count} errores",
            'errors': errors
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)