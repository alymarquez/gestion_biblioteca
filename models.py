class Libro:
    contador = 0
    def __init__(self, titulo, autor, ISBN, editorial, disponibilidad=True):
        Libro.contador += 1
        self.id = Libro.contador
        self.titulo = titulo
        self.autor = autor
        self.ISBN = ISBN
        self.editorial = editorial
        self.disponibilidad = disponibilidad

    def __repr__(self):
        return f'Titulo: {self.titulo}, Autor: {self.autor}. ISBN: {self.ISBN}\n '

    def getTitulo(self):
        return self.titulo

    def getISBN(self):
        return self.ISBN

    def getDisponibilidad(self):
        return self.disponibilidad

    def setDisponibilidad(self, disponible):
        self.disponibilidad = disponible


class Usuario:
    contador = 0

    def __init__(self, nombre, apellido, dni, email, **kwargs ):
        Usuario.contador += 1
        self.id = Usuario.contador
        self.nombre = nombre
        self.apellido = apellido
        self.dni = dni
        self.email = email
        self.librosTomados = kwargs.get('librosTomados', [])

    def getLibros(self):
        return self.librosTomados

    def getNombre(self):
        return self.nombre

    def getApellido(self):
        return self.apellido

    def getDni(self):
        return self.dni

    def agregarLibro(self, libro):
        self.librosTomados.append(libro)


class Biblioteca:
    usuarios = []
    libros = []
    prestamos = []

    def registrarUsuario(self, usuario):
        for u in self.usuarios:
            if u.dni == usuario.dni:
                print(f"El usuario con DNI {usuario.dni} ya está registrado en la biblioteca.")
                return
            if u.email == usuario.email:
                print(f'El email ya está registrado')
                return
        self.usuarios.append(usuario)
        print(f"El usuario '{usuario.getNombre()}' registrado correctamente.")

    def agregarLibro(self, libro):
        for l in self.libros:
            if l.ISBN == libro.ISBN:
                print(f"El libro con ISBN {libro.ISBN} ya está en la biblioteca.")
                return
        self.libros.append(libro)
        print(f"Libro '{libro.titulo}' agregado correctamente.")

    def eliminarLibro(self, isbn):
        for l in self.libros:
            if l.ISBN == isbn:
                self.libros.remove(l)
                return
        print(f'El libro no se encuentra en la biblioteca')
    
    def buscarLibro(self, isbn):
        for l in self.libros:
            if l.ISBN == isbn:
                return l
        print('El libro con isbn {isbn} no se encuentra en la biblioteca')
        #return None
    
    def librosDisponibles(self):
        return [libro for libro in self.libros if libro.getDisponibilidad()]

    def pedirLibro(self, usuario, libro, fecha_prestamo, fecha_devolucion):
        if not libro.getDisponibilidad():
            print(f"El libro '{libro.titulo}' no está disponible para préstamo.")
            return
        
        if len(usuario.getLibros()) >= 3:
            print(f"El usuario '{usuario.getNombre()} {usuario.getApellido()}' ha alcanzado el límite de préstamos.")
            return

        for libroUsuario in usuario.getLibros():
            if libroUsuario.ISBN == libro.ISBN:
                print(f"El usuario ya tiene un préstamo activo del libro '{libro.titulo}'.")
                return

        for prestamo in self.getPrestamos():
            if prestamo.libro.ISBN == libro.ISBN and prestamo.usuario.getDni() == usuario.getDni():
                print(f"El usuario ya tiene un préstamo activo del libro '{libro.titulo}'.")
                return
        

        prestamo = Prestamo(usuario, libro, fecha_prestamo, fecha_devolucion)
        libro.setDisponibilidad(False)
        self.prestamos.append(prestamo)
        usuario.agregarLibro(libro)
        print(f"Préstamo realizado: {prestamo}")

    def devolverLibro(self, usuario, libro):
      # si el ISBN de un libro coincide con el ISBN del libro de algun prestamo entonces append a libros y remove el prestamo
      for libroUsuario in usuario.getLibros():
        if libroUsuario.ISBN == libro.ISBN:
          for prestamo in self.prestamos:
            if prestamo.libro.ISBN == libroUsuario.ISBN:
              self.prestamos.remove(prestamo)
              usuario.librosTomados.remove(libroUsuario)
              libro.setDisponibilidad(True)
              print(f"Libro devuelto con exito")
              return
      print(f"El libro no existe")


    def getPrestamos(self):
        return self.prestamos


class Prestamo:
    contador_id = 0

    def __init__(self, usuario, libro, fecha_prestamo, fecha_devolucion):
        Prestamo.contador_id += 1
        self.id = Prestamo.contador_id
        self.usuario = usuario
        self.libro = libro
        self.fecha_prestamo = fecha_prestamo
        self.fecha_devolucion = fecha_devolucion

    def __repr__(self):
        return f'Prestamo {self.id} a {self.usuario.nombre} con dni {self.usuario.dni} del libro {self.libro.getTitulo()}'
