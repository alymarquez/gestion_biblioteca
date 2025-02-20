from flask import Flask, render_template, request, url_for, redirect, jsonify
from models import Biblioteca, Libro, Usuario, Prestamo
from datetime import datetime

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
        return redirect(url_for('manejar_libros'))
    
    # Lógica barra búsqueda
    elif request.method == 'GET':
        query = request.args.get("query", "").lower()
        if query:
            libros_filtrados = [libro for libro in biblioteca.libros if 
                                query in libro.titulo.lower() or 
                                query in libro.autor.lower() or
                                query in libro.editorial.lower() or
                                query in str(libro.ISBN)]
        else:
            libros_filtrados = biblioteca.libros
            
        return render_template("libros.html", libros=libros_filtrados, query=query)


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
        return redirect(url_for('gestionar_prestamos'))
    
    elif request.method == "GET":
    
        for prestamo in biblioteca.prestamos:
            if isinstance(prestamo.fecha_prestamo, datetime):
                prestamo.fecha_prestamo = prestamo.fecha_prestamo.strftime('%Y-%m-%d')
        prestamos_por_usuario = {usuario.dni: usuario.librosTomados for usuario in biblioteca.usuarios}
        return render_template("prestamos.html", usuarios=biblioteca.usuarios, prestamos_por_usuario=prestamos_por_usuario, libros=biblioteca.libros, prestamos=biblioteca.prestamos)


if __name__ == '__main__':
    #cargar_datos()
    app.run(debug=True)

