import os
import sys
from app import app, db, Product

def migrate_add_name():
    """
    Migration script to add the 'name' column to the Product table
    and set default values for existing products.
    """
    print("Starting migration to add 'name' field to Product table...")
    
    try:
        with app.app_context():
            # Check if the column already exists
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('product')]
            
            if 'name' not in columns:
                print("Adding 'name' column to Product table...")
                # Add the column using raw SQL with the connection
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE product ADD COLUMN name VARCHAR(100) DEFAULT ""'))
                    conn.commit()
                
                # Update existing products to use SKU as name temporarily
                products = Product.query.all()
                for product in products:
                    product.name = f"Producto {product.sku}"
                
                db.session.commit()
                print(f"Migration complete. Updated {len(products)} existing products with default names.")
            else:
                print("The 'name' column already exists in the Product table.")
                
        print("Migration completed successfully.")
        return True
    except Exception as e:
        print(f"Error during migration: {e}")
        return False

if __name__ == "__main__":
    success = migrate_add_name()
    sys.exit(0 if success else 1)