"""
PFO 2 - Cliente de consola para la API de Gestión de Tareas.
Requiere que servidor.py esté corriendo.
"""

import getpass
import requests

URL_BASE = "http://127.0.0.1:5000"
sesion = {"usuario": None, "contrasena": None}


def mostrar_respuesta(resp):
    try:
        datos = resp.json()
    except ValueError:
        datos = resp.text
    print(f"\n[{resp.status_code}] {datos}\n")


def pedir_credenciales():
    usuario = input("Usuario: ").strip()
    #contrasena = getpass.getpass("Contraseña: ") Evita que la contraseña se muestre en la consola.
    contrasena = input("Contraseña: ") #muestra la contraseña en la consola para facilitar las pruebas
    return usuario, contrasena


def registrar():
    usuario, contrasena = pedir_credenciales()
    resp = requests.post(f"{URL_BASE}/registro",
                         json={"usuario": usuario, "contraseña": contrasena})
    mostrar_respuesta(resp)


def iniciar_sesion():
    usuario, contrasena = pedir_credenciales()
    resp = requests.post(f"{URL_BASE}/login",
                         json={"usuario": usuario, "contraseña": contrasena})
    mostrar_respuesta(resp)
    if resp.status_code == 200:
        sesion["usuario"], sesion["contrasena"] = usuario, contrasena


def ver_tareas():
    if not sesion["usuario"]:
        print("\nPrimero tenés que iniciar sesión (opción 2).\n")
        return
    resp = requests.get(f"{URL_BASE}/tareas",
                        auth=(sesion["usuario"], sesion["contrasena"]))
    if resp.status_code == 200:
        print("\n--- HTML recibido de /tareas ---")
        print(resp.text)
    else:
        mostrar_respuesta(resp)


def main():
    opciones = {"1": registrar, "2": iniciar_sesion, "3": ver_tareas}
    while True:
        conectado = f" (sesión: {sesion['usuario']})" if sesion["usuario"] else ""
        print(f"=== Gestor de Tareas{conectado} ===")
        print("1. Registrarse")
        print("2. Iniciar sesión")
        print("3. Ver tareas")
        print("4. Salir")
        opcion = input("Elegí una opción: ").strip()
        if opcion == "4":
            print("¡Hasta luego!")
            break
        accion = opciones.get(opcion)
        if not accion:
            print("\nOpción inválida.\n")
            continue
        try:
            accion()
        except requests.exceptions.ConnectionError:
            print("\nNo se pudo conectar con el servidor. ¿Está corriendo servidor.py?\n")


if __name__ == "__main__":
    main()
