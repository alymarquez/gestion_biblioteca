from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_mysqldb import MySQL
from flask import flash
import MySQLdb
from datetime import datetime

db=MySQL()

class Libro:
    def __init__(self, id, titulo, autor, ISBN, editorial, disponibilidad=True, user_id=None):
        self.id = id
        self.titulo = titulo
        self.autor = autor
        self.ISBN = ISBN
        self.editorial = editorial
        self.disponibilidad = disponibilidad
        self.user_id = user_id

    @staticmethod
    def agregar(titulo, autor, ISBN, editorial, user_id):
        cursor = db.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO libro (titulo, autor, ISBN, editorial, user_id) VALUES (%s, %s, %s, %s, %s)", 
                (titulo, autor, ISBN, editorial, user_id)
            )
            db.connection.commit()
            flash("Libro agregado correctamente", "success")

        except MySQLdb.IntegrityError:
            flash("Error: El libro ya está registrado en este sistema.", "danger")
        
        finally:
            cursor.close()

    @staticmethod
    def get_by_user(user_id):
        cursor = db.connection.cursor()
        cursor.execute("SELECT * FROM libro WHERE user_id = %s", (user_id,))
        libros = cursor.fetchall()
        return [Libro(*libro) for libro in libros]

    @staticmethod
    def get_by_isbn(isbn, user_id):
        cursor = db.connection.cursor()
        cursor.execute("SELECT * FROM libro WHERE ISBN = %s AND user_id = %s", (isbn, user_id))
        libro = cursor.fetchone()
        if libro:
            return Libro(*libro)
        return None

    @staticmethod
    def eliminar(isbn, user_id):
        cursor = db.connection.cursor()
        cursor.execute("DELETE FROM libro WHERE ISBN = %s AND user_id = %s", (isbn, user_id))
        db.connection.commit()
    
    def getDisponibilidad(self):
        return self.disponibilidad == 1

    def setDisponibilidad(self, disponibilidad):
        cursor = db.connection.cursor()
        cursor.execute("UPDATE libro SET disponibilidad = %s WHERE id = %s", (disponibilidad, self.id))
        db.connection.commit()
        cursor.close()


class Usuario:
    def __init__(self, id, nombre, apellido, dni, email, user_id, infracciones = 0):
        self.id = id
        self.nombre = nombre
        self.apellido = apellido
        self.dni = dni
        self.email = email
        self.user_id = user_id
        self.infracciones = infracciones

    @staticmethod
    def agregar(nombre, apellido, dni, email, user_id):
        cursor = db.connection.cursor()

        try:
            cursor.execute(
                "INSERT INTO usuario_biblioteca (nombre, apellido, dni, email, user_id) VALUES (%s, %s, %s, %s, %s)", 
                (nombre, apellido, dni, email, user_id)
            )
            db.connection.commit()
            flash("Usuario agregado correctamente", "success")

        except MySQLdb.IntegrityError as e:
            if "for key 'dni'" in str(e):
                flash("Error: El DNI ya está registrado.", "danger")
            elif "for key 'email'" in str(e):
                flash("Error: El email ya está registrado.", "danger")
            else:
                flash("Error: No se pudo agregar el usuario.", "danger")

        finally:
            cursor.close()

    @staticmethod
    def get_by_user(user_id):
        cursor = db.connection.cursor()
        cursor.execute("SELECT * FROM usuario_biblioteca WHERE user_id = %s", (user_id,))
        usuarios = cursor.fetchall()
        return [Usuario(*usuario) for usuario in usuarios]

    @staticmethod
    def eliminar(dni, user_id):
        cursor = db.connection.cursor()
        cursor.execute("DELETE FROM usuario_biblioteca WHERE dni = %s AND user_id = %s", (dni, user_id))
        db.connection.commit()
        cursor.close()

    def get_by_dni(dni, user_id):
        cursor = db.connection.cursor()
        cursor.execute("SELECT * FROM usuario_biblioteca WHERE dni = %s AND user_id = %s", (dni, user_id))
        usuario = cursor.fetchone()
        if usuario:
            return Usuario(*usuario)
        return None

class Prestamo:
    def __init__(self, id, user_id, libro_id, fecha_prestamo, fecha_devolucion, fecha_devolucion_real, libro_titulo, usuario_nombre, usuario_dni):
        self.id = id
        self.user_id = user_id
        self.libro_id = libro_id
        self.fecha_prestamo = fecha_prestamo
        self.fecha_devolucion = fecha_devolucion
        self.fecha_devolucion_real = fecha_devolucion_real
        self.libro_titulo = libro_titulo
        self.usuario_nombre = usuario_nombre
        self.usuario_dni = usuario_dni

    @staticmethod
    def agregar(user_id, libro_id, fecha_prestamo, fecha_devolucion, admin_id):
        cursor = db.connection.cursor()
        try:
            # Verificamos las infracciones del usuario
            cursor.execute("SELECT infracciones FROM usuario_biblioteca WHERE id = %s", (user_id,))
            infracciones = cursor.fetchone()[0]

            if infracciones >= 3:
                flash("Este usuario tiene más de 3 infracciones. No puede realizar más préstamos.", "danger")
                return

            cursor.execute(
                "INSERT INTO prestamo (user_id, libro_id, fecha_prestamo, fecha_devolucion, admin_id) VALUES (%s, %s, %s, %s, %s)", 
                (user_id, libro_id, fecha_prestamo, fecha_devolucion, admin_id)
            )
            db.connection.commit()

            flash("El préstamo ha sido realizado con éxito.", "success")

        except MySQLdb.Error as e:
            flash("Error al registrar el préstamo.", "danger")
        finally:
            cursor.close()

    @staticmethod
    def devolver(libro_id, user_id, admin_id):
        cursor = db.connection.cursor()
        try:
            cursor.execute("SELECT * FROM prestamo WHERE libro_id = %s AND user_id = %s AND admin_id = %s", (libro_id, user_id, admin_id))
            prestamo = cursor.fetchone()

            if prestamo:

                cursor.execute("UPDATE prestamo SET fecha_devolucion_real = NOW() WHERE id = %s", (prestamo[0],))
                db.connection.commit()

                fecha_devolucion_real = datetime.now()
                fecha_devolucion = datetime.combine(prestamo[4], datetime.min.time())
                
                if (fecha_devolucion_real - fecha_devolucion).days > 15:
                    cursor.execute("UPDATE usuario_biblioteca SET infracciones = infracciones + 1 WHERE id = %s", (user_id,))
                    db.connection.commit()
                    flash("El libro se ha devuelto con retraso. Se ha sumado una infracción al usuario.", "warning")

            else:
                flash("No se encontró un préstamo para este libro.", "error")
        
        except MySQLdb.Error as e:
            flash("Error al devolver el libro.", "danger")
        finally:
            cursor.close()

    @staticmethod
    def get_by_user(admin_id, user_id, libro_id):
        cursor = db.connection.cursor()
        cursor.execute("SELECT * FROM prestamo WHERE admin_id = %s AND user_id = %s AND libro_id = %s", (admin_id, user_id, libro_id, ))
        prestamos = cursor.fetchall()
        return [Prestamo(*prestamo) for prestamo in prestamos]

    def get_all():
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT
                prestamo.id,
                prestamo.user_id,
                prestamo.libro_id,
                prestamo.fecha_prestamo,
                prestamo.fecha_devolucion,
                prestamo.fecha_devolucion_real,
                libro.titulo,
                usuario_biblioteca.nombre,
                usuario_biblioteca.dni
            FROM
                prestamo
            JOIN
                libro ON prestamo.libro_id = libro.id
            JOIN
                usuario_biblioteca ON prestamo.user_id = usuario_biblioteca.id
        """) 
        prestamos = cursor.fetchall()
        return [Prestamo(*prestamo) for prestamo in prestamos]


class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __repr__(self):
        return f'User: {self.username}'
    
    @staticmethod
    def get_by_id(user_id):
        cursor = db.connection.cursor()
        cursor.execute("SELECT id, username, password FROM user WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user:
            return User(*user)
        return None

    @staticmethod
    def authenticate(username, password):
        cursor = db.connection.cursor()
        cursor.execute("SELECT id, username, password FROM user WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user[2], password):
            return User(*user)
        return None

    @staticmethod
    def create(username, password):
        cursor = db.connection.cursor()
        password_hash = generate_password_hash(password)
        cursor.execute("INSERT INTO user (username, password) VALUES (%s, %s)", (username, password_hash))
        db.connection.commit()
        return cursor.lastrowid
    
    @classmethod
    def check_password(cls, hashed_password, password):
        return check_password_hash(hashed_password, password)
