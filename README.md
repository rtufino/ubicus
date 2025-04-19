# Organizador de Productos en Estanterías

Aplicación web desarrollada en Python Flask para organizar productos en estanterías de una tienda retail. La aplicación permite gestionar la ubicación de productos en vitrinas, columnas y filas específicas.

## Características

- **Gestión de productos**: Agregar, editar y eliminar productos
- **Búsqueda de ubicaciones**: Encontrar rápidamente dónde está ubicado un producto por su SKU o nombre
- **Importación desde CSV**: Cargar datos masivamente desde archivos CSV
- **Autenticación de usuarios**: Protección con usuario y contraseña
- **Interfaz responsiva**: Diseñada con Bootstrap para funcionar en dispositivos móviles y de escritorio

## Datos almacenados

- **SKU**: Código único del producto
- **Nombre**: Nombre descriptivo del producto
- **Vitrina**: Identificador en números romanos (I, II, III, IV, etc.)
- **Columna**: Número de columna (1 o 2)
- **Fila**: Número de fila (1 - 7)

## Tecnologías utilizadas

- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5, jQuery
- **Base de datos**: SQLite
- **Autenticación**: Flask-Login

## Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Navegador web moderno

## Instalación

1. Clonar el repositorio:
   ```
   git clone https://github.com/rtufino/ubicus.git
   cd ubicus
   ```

2. Crear y activar un entorno virtual:
   ```
   python3 -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar las dependencias:
   ```
   pip install -r requirements.txt
   ```

4. Configurar las variables de entorno (opcional):
   ```
   # Crear archivo .env con el siguiente contenido:
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=your_secret_key_here
   DATABASE_URL=sqlite:///products.db
   ```

## Ejecución

1. Iniciar la aplicación:
   ```
   python app.py
   ```

2. Abrir en el navegador:
   ```
   http://localhost:5000
   ```

3. Iniciar sesión:
   - Usuario: `vendedor`
   - Contraseña: `password123`

## Uso

### Búsqueda de productos
- En la página principal, seleccione si desea buscar por SKU o por nombre
- Ingrese el término de búsqueda y haga clic en "Buscar"
- La aplicación mostrará la ubicación exacta (vitrina, columna y fila)

### Gestión de productos
- En la sección "Productos", puede ver todos los productos registrados
- Utilice los botones para agregar, editar o eliminar productos
- Para importar desde CSV, utilice el botón "Cargar CSV"

### Formato del archivo CSV
```
SKU,NOMBRE,VITRINA,FILA,COLUMNA
ABC123,Producto A,I,3,1
DEF456,Producto B,II,5,2
```

### Cambio de contraseña
- Haga clic en su nombre de usuario en la barra de navegación
- Seleccione "Cambiar Contraseña"
- Ingrese su contraseña actual y la nueva contraseña

## Migración a la nueva versión

Si está actualizando desde una versión anterior, debe ejecutar el script de migración para agregar el campo "nombre" a la base de datos:

```
python migrate_add_name.py
```

Este script agregará el campo "nombre" a la tabla de productos y asignará nombres predeterminados a los productos existentes.

## Despliegue en producción

Para desplegar en un servidor de producción, se recomienda:
- Utilizar Gunicorn como servidor WSGI
- Configurar Nginx como proxy inverso
- Habilitar HTTPS con Let's Encrypt
- Considerar migrar a una base de datos más robusta como PostgreSQL

## Autor

**Rodrigo Tufiño**  
Email: rtufino@lisoft.net

## Licencia

Este proyecto está licenciado bajo los términos de la licencia MIT.