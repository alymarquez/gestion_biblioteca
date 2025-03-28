from flask import Flask, render_template, request, url_for, redirect, jsonify, flash
from models import Libro, Usuario, Prestamo, User
from datetime import datetime
from config import config
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

app = Flask(__name__)
app.secret_key = 'supersecretkey'

db.init_app(app)
login_manager_app = LoginManager(app)
login_manager_app.login_view = 'login'

@login_manager_app.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

@app.route('/') 
def home():
    return redirect(url_for('login'))

@app.route('/index')
@login_required
def index():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST']) 
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.authenticate(username, password)

        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Usuario o contraseña incorrectos")
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        User.create(username, password)
        flash("Usuario registrado con éxito")
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

# LIBROS
@app.route('/libros', methods=['GET', 'POST'])
@login_required
def manejar_libros():
    cursor = db.connection.cursor()

    if request.method == 'POST':
        data = request.form.to_dict()
        titulo=data['titulo']
        autor=data['autor']
        ISBN=str(data['ISBN'])
        editorial=data['editorial']
        
        Libro.agregar(titulo, autor, ISBN, editorial, current_user.id)
        return redirect(url_for('manejar_libros'))
    
    # Lógica barra búsqueda
    elif request.method == 'GET':
        query = request.args.get("query", "").lower()
        user_id = current_user.id
        if query:
            sql = """
                SELECT id, titulo, autor, editorial, ISBN FROM libro
                WHERE (LOWER(titulo) LIKE %s OR LOWER(autor) LIKE %s OR LOWER(editorial) LIKE %s OR ISBN LIKE %s) AND user_id = %s
            """
            param = f"%{query}%"  # 🔹 Para hacer una búsqueda parcial
            cursor.execute(sql, (param, param, param, param, user_id))
        else:
            cursor.execute("SELECT id, titulo, autor, editorial, ISBN FROM libro WHERE user_id = %s", (user_id,))
        
        libros = cursor.fetchall()
        cursor.close()

        return render_template("libros.html", libros=libros, query=query)

@app.route('/eliminar/<isbn>', methods=['POST'])
@login_required
def eliminar_libro(isbn):
    Libro.eliminar(isbn, current_user.id)
    return redirect(url_for('manejar_libros'))

@app.route('/editar/<isbn>', methods=['GET', 'POST'])
@login_required
def editar_libro(isbn):
    cursor = db.connection.cursor()
    cursor.execute("SELECT id, titulo, autor, editorial FROM libro WHERE ISBN = %s AND user_id = %s", (isbn, current_user.id))
    libro = cursor.fetchone()

    if not libro:
        return "Libro no encontrado", 404
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        editorial = request.form['editorial']

        cursor.execute("""
            UPDATE libro 
            SET titulo = %s, autor = %s, editorial = %s 
            WHERE ISBN = %s AND user_id = %s
        """, (titulo, autor, editorial, isbn, current_user.id))

        db.connection.commit()
        cursor.close()

        return redirect(url_for('manejar_libros'))
    
    cursor.close()
    return render_template('editar_libro.html', libro={'id': libro[0], 'titulo': libro[1], 'autor': libro[2], 'editorial': libro[3]})

# USUARIOS
@app.route('/usuarios', methods=['GET', 'POST']) 
@login_required
def manejar_usuarios():
    cursor = db.connection.cursor()
    if request.method == 'POST':
        data = request.form.to_dict()
        nombre = data['nombre']
        apellido = data['apellido']
        dni = str(data['DNI'])
        email = data['email']


        Usuario.agregar(nombre, apellido, dni, email, current_user.id)
        return redirect(url_for('manejar_usuarios'))
    
    elif request.method == "GET":
        query = request.args.get("query", "").lower()
        user_id = current_user.id

        if query:
            sql = """
                SELECT id, nombre, apellido, dni, email FROM usuario_biblioteca
                WHERE (LOWER(nombre) LIKE %s OR LOWER(apellido) LIKE %s OR LOWER(dni) LIKE %s OR LOWER(email) LIKE %s) AND user_id = %s
            """
            param = f"%{query}%"  #  Para hacer una búsqueda parcial
            cursor.execute(sql, (param, param, param, param, user_id))
        else:
            cursor.execute("SELECT id, nombre, apellido, dni, email FROM usuario_biblioteca WHERE user_id = %s", (user_id,))
        
        
        usuarios = cursor.fetchall()
        cursor.close()

        return render_template("usuarios.html", usuarios=usuarios, query=query)


@app.route('/eliminarusuario/<dni>', methods=['POST'])
@login_required
def eliminar_usuario(dni):
    Usuario.eliminar(dni, current_user.id)
    return redirect(url_for('manejar_usuarios'))

@app.route('/editarusuario/<dni>', methods=['GET', 'POST'])
@login_required
def editar_usuario(dni):
    cursor = db.connection.cursor()
    cursor.execute("SELECT id, nombre, apellido, dni, email FROM usuario_biblioteca WHERE dni = %s AND user_id = %s", (dni, current_user.id))
    usuario = cursor.fetchone()

    if not usuario:
        return "Usuario no encontrado", 404
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        dni = request.form['dni']
        email = request.form['email']

        cursor.execute("""
            UPDATE usuario_biblioteca
            SET nombre = %s, apellido = %s, dni = %s, email = %s
            WHERE dni = %s AND user_id = %s
        """, (nombre, apellido, dni, email, dni, current_user.id))

        db.connection.commit()
        cursor.close()

        return redirect(url_for('manejar_usuarios'))
    
    cursor.close()
    return render_template('editar_usuario.html', usuario={'id': usuario[0], 'nombre': usuario[1], 'apellido': usuario[2], 'dni': usuario[3], 'email': usuario[4]})



@app.route('/prestamos', methods=['GET', 'POST']) 
@login_required
def gestionar_prestamos():
    usuarios = Usuario.get_by_user(current_user.id)
    libros = Libro.get_by_user(current_user.id)

    if request.method == "POST":
        data = request.form.to_dict()
        userdni = str(data['dni'])
        isbn = str(data['ISBN'])

        usuario = Usuario.get_by_dni(userdni, current_user.id)
        libro = Libro.get_by_isbn(isbn, current_user.id)

        if not usuario or not libro:
            flash('Usuario o libro no encontrado', 'error')
            return redirect(url_for('gestionar_prestamos'))

        # Si se va a hacer un préstamo, se valida la disponibilidad del libro
        if 'fecha_prestamo' in data:
            if not libro.getDisponibilidad():
                flash(f'El libro "{libro.titulo}" no está disponible', 'error')
                return redirect(url_for('gestionar_prestamos'))
            
            try:
                fecha_prestamo = data['fecha_prestamo'].strip()
                fecha_devolucion = data['fecha_devolucion'].strip()

                # Verificar que las fechas no estén vacías
                if not fecha_prestamo or not fecha_devolucion:
                    raise ValueError("Las fechas de préstamo y devolución son obligatorias.")
                
                fecha_prestamo = datetime.strptime(data['fecha_prestamo'], '%Y-%m-%d') 
                fecha_devolucion = datetime.strptime(data['fecha_devolucion'], '%Y-%m-%d')

                #Agregar el préstamo a la base de datos y realizar otras acciones necesarias
                Prestamo.agregar(usuario.id, libro.id, fecha_prestamo, fecha_devolucion, current_user.id)
                libro.setDisponibilidad(0)
                flash('Préstamo realizado con éxito', 'success')
                return redirect(url_for('gestionar_prestamos'))
            
            except ValueError as e:
                flash(f"Error en la fecha: {e}", "error")
                return redirect(url_for('gestionar_prestamos'))
            
        else:  # En caso de que se esté devolviendo un libro
            prestamo = Prestamo.get_by_user(current_user.id, usuario, libro)
            
            if not prestamo:
                flash(f'El libro "{libro.titulo}" no está prestado al usuario {usuario.nombre}', 'error')
                return redirect(url_for('gestionar_prestamos'))

        Prestamo.devolver(libro, usuario, current_user.id)
        libro.setDisponibilidad(1)
        flash('Devolución realizado con éxito', 'success')
        return redirect(url_for('gestionar_prestamos'))

    elif request.method == "GET":
        prestamos = Prestamo.get_all()

        # Convertir la fecha de préstamo a formato de cadena
        for prestamo in prestamos:
            if isinstance(prestamo.fecha_prestamo, datetime):
                prestamo.fecha_prestamo = prestamo.fecha_prestamo.strftime('%Y-%m-%d')

        # Renderizar la plantilla y pasar los datos a la vista
        return render_template("prestamos.html", usuarios=usuarios, libros=libros, prestamos=prestamos)


def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1>Pagina no encontrada</h1>", 404


if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run(debug=True)

