from flask import Flask, render_template, request, url_for, redirect, jsonify, json
from models import Biblioteca, Libro, Usuario, Prestamo
from datetime import datetime
from json import JSONDecodeError
import json

app = Flask(__name__)

biblioteca = Biblioteca()

@app.route('/') 
def index():
    return render_template("index.html")

@app.route('/libros', methods=['GET', 'POST']) 
def manejar_libros():
    if request.method == 'POST':
        data = request.form.to_dict()
        nuevo_libro = Libro(
            titulo=data['titulo'],
            autor=data['autor'],
            ISBN=str(data['ISBN']),
            editorial=data['editorial']
        )
        biblioteca.agregarLibro(nuevo_libro)
        #guardar_datos()
        return redirect(url_for('manejar_libros'))
    elif request.method == 'GET':
        return render_template("libros.html", libros=biblioteca.libros)

@app.route('/eliminar/<isbn>', methods=['POST'])
def eliminar_libro(isbn):
    biblioteca.eliminarLibro(isbn)
    return redirect(url_for('manejar_libros'))

@app.route('/editar/<isbn>', methods=['GET', 'POST'])
def editar_libro(isbn):
    libro = biblioteca.buscarLibro(isbn)
    
    if not libro:
        return "Libro no encontrado", 404
    
    if request.method == 'POST':
        libro.titulo = request.form['titulo']
        libro.autor = request.form['autor']
        libro.editorial = request.form['editorial']
        #guardar_datos()
        return redirect(url_for('manejar_libros'))
    
    return render_template('editar_libro.html', libro=libro)

@app.route('/usuarios', methods=['GET', 'POST']) 
def manejar_usuarios():
    if request.method == 'POST':
        data = request.form.to_dict()
        nuevo_usuario = Usuario(
            nombre=data['nombre'],
            apellido=data['apellido'],
            dni=str(data['DNI']),
            email=data['email']
        )
        biblioteca.registrarUsuario(nuevo_usuario)
        #guardar_datos()
        return redirect(url_for('manejar_usuarios'))
    elif request.method == "GET":
        return render_template("usuarios.html", usuarios=biblioteca.usuarios)

@app.route('/prestamos', methods=['GET', 'POST']) 
def gestionar_prestamos():
    if request.method == "POST":
        data = request.form.to_dict()
        userdni = str(data['dni'])
        isbn = str(data['ISBN'])
        usuario = next((u for u in biblioteca.usuarios if str(u.dni) == userdni), None)
        libro = next((l for l in biblioteca.libros if str(l.ISBN) == isbn), None)
        
        if not usuario or not libro:
            return jsonify({'mensaje': 'Usuario o libro no encontrado'}), 404
        
        if 'fecha_prestamo' in data:
            if not libro.getDisponibilidad():
                return jsonify({'mensaje': f'El libro "{libro.titulo}" no está disponible'}), 404
            
            fecha_prestamo=datetime.strptime(data['fecha_prestamo'], '%Y-%m-%d')
            fecha_devolucion = datetime.strptime(data['fecha_devolucion'], '%Y-%m-%d')
            biblioteca.pedirLibro(usuario, libro, fecha_prestamo, fecha_devolucion)
        
        else:
            prestamo = next((p for p in biblioteca.prestamos if
                                str(p.libro.ISBN) == isbn and str(p.usuario.dni) == userdni), None)
            if not prestamo:
                return jsonify({'mensaje': f'El libro "{libro.titulo}" no está prestado al usuario {usuario.nombre}' }), 404
            biblioteca.devolverLibro(usuario, libro)
        #guardar_datos()
        return redirect(url_for('gestionar_prestamos'))
    
    elif request.method == "GET":
    
        for prestamo in biblioteca.prestamos:
            if isinstance(prestamo.fecha_prestamo, datetime):
                prestamo.fecha_prestamo = prestamo.fecha_prestamo.strftime('%Y-%m-%d')
        prestamos_por_usuario = {usuario.dni: usuario.librosTomados for usuario in biblioteca.usuarios}
        return render_template("prestamos.html", usuarios=biblioteca.usuarios, prestamos_por_usuario=prestamos_por_usuario, libros=biblioteca.libros, prestamos=biblioteca.prestamos)
'''
def guardar_datos():
    with open('datos.json', 'w') as f:
        datos = {
            'libros': [libro.__dict__ for libro in biblioteca.libros],
            'usuarios': [usuario.__dict__ for usuario in biblioteca.usuarios],
            'prestamos': [{
                'id_prestamo': prestamo.id,
                'libro': prestamo.libro.__dict__,
                'usuario': prestamo.usuario.__dict__,
                'fecha_prestamo': prestamo.fecha_prestamo.strftime('%Y-%m-%d') if isinstance(prestamo.fecha_prestamo, datetime) else str(prestamo.fecha_prestamo),
                'fecha_devolucion': prestamo.fecha_devolucion.strftime('%Y-%m-%d') if isinstance(prestamo.fecha_devolucion, datetime) else str(prestamo.fecha_devolucion),
            } for prestamo in biblioteca.prestamos ]
        }
        json.dump(datos, f, indent=4, default=str)


def cargar_datos():
    try:
        with open('datos.json', 'r') as f:
            contenido = f.read().strip()
            if not contenido:
                datos = {}
            else:
                datos = json.loads(contenido)
            
            for libro_data in datos.get('libros', []):
                disponible = libro_data.pop('disponible', True)
                libro = Libro(**libro_data)
                libro.setDisponibilidad(disponible)
                biblioteca.agregarLibro(libro)

            for usuario_data in datos.get('usuarios', []):
                usuario_data.pop('libros_prestados', None)
                usuario = Usuario(**usuario_data)
                biblioteca.registrarUsuario(usuario)
                    
            for prestamo_data in datos.get('prestamos', []):
                libro_data = prestamo_data['libro']
                usuario_data = prestamo_data['usuario']
                libro = next((libro for libro in biblioteca.libros if str(libro.ISBN) == str(libro_data['ISBN'])), None)
                usuario = next((usuario for usuario in biblioteca.usuarios if
                                str(usuario.dni) == str(usuario_data['dni'])), None)
                
                if libro and usuario:
                    prestamo = Prestamo(
                        
                        libro=libro,
                        usuario=usuario,
                        fecha_prestamo= prestamo_data['fecha_prestamo'],
                        fecha_devolucion= prestamo_data['fecha_devolucion']
                    )
                    biblioteca.prestamos.append(prestamo)
    except FileNotFoundError:
        pass
    except json.JSONDecodeError:
        pass
'''
if __name__ == '__main__':
    #cargar_datos()
    app.run(debug=True)

