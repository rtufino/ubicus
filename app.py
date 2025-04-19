import os
import csv
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables and default user
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create default user if it doesn't exist
        if not User.query.filter_by(username='vendedor').first():
            default_user = User(username='vendedor')
            default_user.set_password('password123')
            db.session.add(default_user)
            db.session.commit()
            print("Default user 'vendedor' created with password 'password123'")

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
@login_required
def products():
    return render_template('products.html')

@app.route('/api/products', methods=['GET'])
@login_required
def get_products():
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products])

@app.route('/api/products', methods=['POST'])
@login_required
def add_product():
    data = request.json
    
    # Check if product with this SKU already exists
    existing_product = Product.query.filter_by(sku=data['sku']).first()
    if existing_product:
        return jsonify({'success': False, 'message': 'El producto con este SKU ya existe'}), 400
    
    # Validate data
    if not data['sku'] or not data['display_case'] or not data['column'] or not data['row']:
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
    if not data['sku'] or not data['display_case'] or not data['column'] or not data['row']:
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
            if len(row) != 4:
                error_count += 1
                errors.append(f"La fila tiene un número incorrecto de columnas: {row}")
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
            'message': f"Se procesaron {success_count} productos con éxito, {error_count} errores",
            'errors': errors
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)