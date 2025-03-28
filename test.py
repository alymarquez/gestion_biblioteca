from werkzeug.security import generate_password_hash, check_password_hash

password = "indis"
nuevo_hash = generate_password_hash(password, method="scrypt")
print("Nuevo hash generado:", nuevo_hash)

# Prueba la verificación con el nuevo hash
print("Verificación manual con nuevo hash:", check_password_hash(nuevo_hash, password))