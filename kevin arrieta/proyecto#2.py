from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import sqlite3
import os
import shutil
import re
from PIL import Image, ImageTk    

# =============================================================================
# CONFIGURACIÓN DE RUTAS Y CARPETAS PERSISTENTES
# =============================================================================

# Define la ruta absoluta del directorio actual para que la BBDD no cambie de lugar
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_BBDD = os.path.join(DIRECTORIO_ACTUAL, "BaseUsuarios.db")
CARPETA_UPLOADS = os.path.join(DIRECTORIO_ACTUAL, "uploads")

# Crear carpeta para almacenamiento persistente de fotos y archivos si no existe
if not os.path.exists(CARPETA_UPLOADS):
    os.makedirs(CARPETA_UPLOADS)

# =============================================================================
# CONFIGURACIÓN DE LA VENTANA
# =============================================================================

raiz = Tk()
raiz.title("Sistema de Gestión de Usuarios")
raiz.geometry("1100x750")
raiz.resizable(False, False)

# Manejo seguro de la carga del icono
ruta_icono = os.path.join(DIRECTORIO_ACTUAL, "c:\\Users\\PC\\Downloads\\eagle-take-off-calvo-53918840.ico")
if os.path.exists(ruta_icono):
    try:
        raiz.iconbitmap(ruta_icono)
    except Exception:
        pass

# =============================================================================
# VARIABLES DE CONTROL
# =============================================================================

id_seleccionado = StringVar()
nombre = StringVar()
apellido = StringVar()
correo = StringVar()
direccion = StringVar()
ciudad = StringVar()
codigo_postal = StringVar()

genero = StringVar(value="Masculino")
estado = IntVar(value=1)
tipo_usuario = StringVar(value="Seleccione")

ruta_imagen = StringVar()
ruta_archivo = StringVar()

# =============================================================================
# CONEXIÓN A BASE DE DATOS Y MIGRACIÓN AUTOMÁTICA
# =============================================================================

def conexion_bbdd():
    try:
        conexion = sqlite3.connect(RUTA_BBDD)
        cursor = conexion.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS USUARIOS ( 
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                correo TEXT UNIQUE,
                direccion TEXT,
                ciudad TEXT,
                codigo_postal TEXT,
                genero TEXT,
                estado INTEGER,
                tipo_usuario TEXT,
                imagen TEXT,
                archivo TEXT
            )
        """)
        
        cursor.execute("PRAGMA table_info(USUARIOS)")
        columnas_existentes = [col[1] for col in cursor.fetchall()]
        if "correo" not in columnas_existentes:
            cursor.execute("ALTER TABLE USUARIOS ADD COLUMN correo TEXT")

        conexion.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Error BD", f"Error al conectar la base de datos: {e}")
    finally:
        conexion.close()

conexion_bbdd()

# =========================================================================
# FUNCIONES AUXILIARES DE VALIDACIÓN Y ARCHIVOS
# =========================================================================

def es_correo_valido(email):
    """ Valida el formato del correo mediante expresión regular """
    if not email:
        return True
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(patron, email) is not None

def existe_correo_duplicado(email, id_actual=None):
    """ Verifica si el correo ya pertenece a otro usuario registrado """
    if not email:
        return False
    conexion = sqlite3.connect(RUTA_BBDD)
    cursor = conexion.cursor()
    if id_actual:
        cursor.execute("SELECT id FROM USUARIOS WHERE correo = ? AND id != ?", (email, id_actual))
    else:
        cursor.execute("SELECT id FROM USUARIOS WHERE correo = ?", (email,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado is not None

def copiar_a_uploads(ruta_origen):
    """ Copia cualquier archivo adjunto a la carpeta 'uploads/' para evitar enlaces rotos """
    if not ruta_origen or not os.path.exists(ruta_origen):
        return ""
    
    if os.path.abspath(ruta_origen).startswith(CARPETA_UPLOADS):
        return ruta_origen

    nombre_archivo = os.path.basename(ruta_origen)
    ruta_destino = os.path.join(CARPETA_UPLOADS, nombre_archivo)
    
    contador = 1
    nombre_base, extension = os.path.splitext(nombre_archivo)
    while os.path.exists(ruta_destino):
        nuevo_nombre = f"{nombre_base}_{contador}{extension}"
        ruta_destino = os.path.join(CARPETA_UPLOADS, nuevo_nombre)
        contador += 1

    try:
        shutil.copy(ruta_origen, ruta_destino)
        return ruta_destino
    except Exception as e:
          print(f"Error al copiar archivo: {e}")
          return ruta_origen

def mostrar_imagen_en_label(path_img):
    """ Función auxiliar para renderizar la imagen sin deformar el contenedor """
    if path_img and os.path.exists(path_img):
        try:
            imagen = Image.open(path_img)
            imagen.thumbnail((130, 130))
            imagen_tk = ImageTk.PhotoImage(imagen)
            etiqueta_imagen.config(image=imagen_tk, text="")
            etiqueta_imagen.image = imagen_tk
            return
        except Exception as error:
            print(f"Error al cargar imagen: {error}")
            
    etiqueta_imagen.config(image="", text="Sin Imagen")
    etiqueta_imagen.image = None

def limpiar():
    id_seleccionado.set("")
    nombre.set("")
    apellido.set("")
    correo.set("")
    direccion.set("")
    ciudad.set("")
    codigo_postal.set("")
    genero.set("Masculino")
    estado.set(1)
    tipo_usuario.set("Seleccione")
    ruta_imagen.set("")
    ruta_archivo.set("")
    entrada_buscar.delete(0, END)
    
    mostrar_imagen_en_label(None)
    etiqueta_archivo.config(text="Archivo: No adjunto")

def seleccionar_imagen():
    archivo = filedialog.askopenfilename(
        title="Seleccionar imagen",
        filetypes=[
            ("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp"),
            ("Todos los archivos", "*.*")
        ]
    )
    if archivo:
        ruta_imagen.set(archivo)
        mostrar_imagen_en_label(archivo)

def seleccionar_archivo():
    archivo = filedialog.askopenfilename(
        title="Seleccionar archivo o imagen",
        filetypes=[
            ("Todos los archivos compatibles", "*.pdf *.docx *.xlsx *.txt *.png *.jpg *.jpeg *.gif *.bmp"),
            ("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp"),
            ("Documentos", "*.pdf *.docx *.xlsx *.txt"),
            ("Todos los archivos", "*.*")
        ]
    )
    if archivo:
        ruta_archivo.set(archivo)
        nombre_archivo = os.path.basename(archivo)
        etiqueta_archivo.config(text=f"Archivo: {nombre_archivo}")
        
        extension = os.path.splitext(archivo)[1].lower()
        if extension in [".png", ".jpg", ".jpeg", ".gif", ".bmp"]:
            ruta_imagen.set(archivo)
            mostrar_imagen_en_label(archivo)

# =========================================================================
# OPERACIONES CRUD (BLOQUE GUARDAR CONTACTO PERMANENTE)
# =========================================================================

def guardar_contacto():
    if not nombre.get().strip():
        messagebox.showwarning("Advertencia", "Debe ingresar el nombre.")
        return
    if not apellido.get().strip():
        messagebox.showwarning("Advertencia", "Debe ingresar el apellido.")
        return
    if tipo_usuario.get() == "Seleccione":
        messagebox.showwarning("Advertencia", "Debe seleccionar el tipo de usuario.")
        return

    correo_txt = correo.get().strip()
    if correo_txt and not es_correo_valido(correo_txt):
        messagebox.showwarning("Correo Inválido", "Por favor ingrese un correo electrónico válido (ejemplo@dominio.com).")
        return

    if existe_correo_duplicado(correo_txt):
        messagebox.showerror("Duplicado", "El correo ingresado ya pertenece a otro usuario.")
        return

    # Guardado seguro de fotos y archivos locales
    foto_local = copiar_a_uploads(ruta_imagen.get())
    archivo_local = copiar_a_uploads(ruta_archivo.get())

    try:
        conexion = sqlite3.connect(RUTA_BBDD)
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO usuarios
            (nombre, apellido, correo, direccion, ciudad, codigo_postal, genero, estado, tipo_usuario, imagen, archivo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nombre.get().strip(),
            apellido.get().strip(),
            correo_txt,
            direccion.get().strip(),
            ciudad.get().strip(),
            codigo_postal.get().strip(),
            genero.get(),
            estado.get(),
            tipo_usuario.get(),
            foto_local,
            archivo_local
        ))
        
        # CONFIRMACIÓN PERMANENTE EN DISCO DURO (No se borran al cerrar)
        conexion.commit()
        
        messagebox.showinfo("Registro Exitoso", "Contacto guardado permanentemente en la base de datos.")
        mostrar_datos()
        limpiar()
    except sqlite3.Error as e:
        messagebox.showerror("Error BD", f"Error al guardar: {e}")
    finally:
        conexion.close()

def mostrar_datos():
    for elemento in tabla.get_children():
        tabla.delete(elemento)

    try:
        conexion = sqlite3.connect(RUTA_BBDD)
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT id, nombre, apellido, correo, direccion, ciudad, codigo_postal, genero, estado, tipo_usuario 
            FROM usuarios ORDER BY id ASC
        """)
        registros = cursor.fetchall()

        for registro in registros:      
            estado_texto = "Activo" if registro[8] == 1 else "Inactivo"
            tabla.insert("", END, values=(
                registro[0], registro[1], registro[2], registro[3],
                registro[4], registro[5], registro[6], registro[7], estado_texto, registro[9]
            ))
            
        filas = tabla.get_children()
        if filas:
            tabla.see(filas[-1])
            
    except sqlite3.Error as e:
        messagebox.showerror("Error BD", f"Error al consultar datos: {e}")
    finally:
        conexion.close()

def buscar():
    texto = entrada_buscar.get().strip()
    
    for elemento in tabla.get_children():
        tabla.delete(elemento)
        
    try:
        conexion = sqlite3.connect(RUTA_BBDD)
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT id, nombre, apellido, correo, direccion, ciudad, codigo_postal, genero, estado, tipo_usuario
            FROM usuarios
            WHERE nombre LIKE ? OR apellido LIKE ? OR correo LIKE ? OR ciudad LIKE ?
            ORDER BY id ASC
        """, (f"%{texto}%", f"%{texto}%", f"%{texto}%", f"%{texto}%"))
        
        registros = cursor.fetchall()
        for registro in registros:
            estado_texto = "Activo" if registro[8] == 1 else "Inactivo"
            tabla.insert("", END, values=(
                registro[0], registro[1], registro[2], registro[3],
                registro[4], registro[5], registro[6], registro[7], estado_texto, registro[9]
            ))
    except sqlite3.Error as e:
        messagebox.showerror("Error BD", f"Error en la búsqueda: {e}")
    finally:
        conexion.close()

def cargar_archivos_registro(id_usuario):
    try:
        conexion = sqlite3.connect(RUTA_BBDD)
        cursor = conexion.cursor()
        cursor.execute("SELECT imagen, archivo FROM usuarios WHERE id = ?", (id_usuario,))
        registro = cursor.fetchone()
    except sqlite3.Error as e:
        messagebox.showerror("Error BD", f"Error al cargar archivos: {e}")
        return
    finally:
        conexion.close()

    if not registro:
        return

    img_path, arc_path = registro[0], registro[1]
    ruta_imagen.set(img_path if img_path else "")
    ruta_archivo.set(arc_path if arc_path else "")

    if arc_path:
        etiqueta_archivo.config(text=f"Archivo: {os.path.basename(arc_path)}")
    else:
        etiqueta_archivo.config(text="Archivo: No adjunto")

    mostrar_imagen_en_label(img_path)

def seleccionar_registro(event):
    seleccionado = tabla.focus()
    if not seleccionado:
        return
        
    datos = tabla.item(seleccionado, "values")
    if not datos:
        return
        
    id_seleccionado.set(datos[0])
    nombre.set(datos[1])
    apellido.set(datos[2])
    correo.set(datos[3])
    direccion.set(datos[4])
    ciudad.set(datos[5])
    codigo_postal.set(datos[6])
    genero.set(datos[7])
    estado.set(1 if datos[8] == "Activo" else 0)
    tipo_usuario.set(datos[9])
    
    cargar_archivos_registro(datos[0])

def actualizar():
    if not id_seleccionado.get():
        messagebox.showwarning("Advertencia", "Seleccione un registro de la tabla inferior.")
        return

    correo_txt = correo.get().strip()
    if correo_txt and not es_correo_valido(correo_txt):
        messagebox.showwarning("Correo Inválido", "Por favor ingrese un correo electrónico válido.")
        return

    if existe_correo_duplicado(correo_txt, id_actual=id_seleccionado.get()):
        messagebox.showerror("Duplicado", "El correo ingresado ya pertenece a otro usuario.")
        return

    foto_local = copiar_a_uploads(ruta_imagen.get())
    archivo_local = copiar_a_uploads(ruta_archivo.get())

    try:
        conexion = sqlite3.connect(RUTA_BBDD)
        cursor = conexion.cursor()
        cursor.execute("""
            UPDATE usuarios
            SET nombre = ?, apellido = ?, correo = ?, direccion = ?, ciudad = ?,
                codigo_postal = ?, genero = ?, estado = ?, tipo_usuario = ?,
                imagen = ?, archivo = ?
            WHERE id = ?
        """, (
            nombre.get().strip(),
            apellido.get().strip(),
            correo_txt,
            direccion.get().strip(),
            ciudad.get().strip(),
            codigo_postal.get().strip(),
            genero.get(),
            estado.get(),
            tipo_usuario.get(),
            foto_local,
            archivo_local,
            id_seleccionado.get()
        ))
        conexion.commit()
        messagebox.showinfo("Actualizar", "Contacto actualizado correctamente.")
        mostrar_datos()
        limpiar()
    except sqlite3.Error as e:
        messagebox.showerror("Error BD", f"Error al actualizar: {e}")
    finally:
        conexion.close()

def eliminar():
    if not id_seleccionado.get():
        messagebox.showwarning("Advertencia", "Seleccione un registro de la tabla.")
        return

    if messagebox.askyesno("Eliminar", "¿Está seguro de eliminar este registro?"):
        try:
            conexion = sqlite3.connect(RUTA_BBDD)
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id = ?", (id_seleccionado.get(),))
            conexion.commit()
            messagebox.showinfo("Eliminar", "Contacto eliminado.")
            mostrar_datos()
            limpiar()
        except sqlite3.Error as e:
            messagebox.showerror("Error BD", f"Error al eliminar: {e}")
        finally:
            conexion.close()

# =========================================================================
# INTERFAZ GRÁFICA (Widgets)
# =========================================================================

miFrame = Frame(raiz, bd=2, relief="groove", padx=10, pady=10)
miFrame.pack(padx=10, pady=10, fill="x")

Label(miFrame, text="FORMULARIO DE REGISTRO DE USUARIOS", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=6, pady=10)

Label(miFrame, text="Nombre:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
Entry(miFrame, textvariable=nombre, width=25).grid(row=1, column=1, padx=5, pady=5)

Label(miFrame, text="Apellido:").grid(row=1, column=2, padx=5, pady=5, sticky="e")
Entry(miFrame, textvariable=apellido, width=25).grid(row=1, column=3, padx=5, pady=5)

Label(miFrame, text="Correo:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
Entry(miFrame, textvariable=correo, width=25).grid(row=2, column=1, padx=5, pady=5)

Label(miFrame, text="Dirección:").grid(row=2, column=2, padx=5, pady=5, sticky="e")
Entry(miFrame, textvariable=direccion, width=25).grid(row=2, column=3, padx=5, pady=5)

Label(miFrame, text="Ciudad:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
Entry(miFrame, textvariable=ciudad, width=25).grid(row=3, column=1, padx=5, pady=5)

Label(miFrame, text="Código Postal:").grid(row=3, column=2, padx=5, pady=5, sticky="e")
Entry(miFrame, textvariable=codigo_postal, width=25).grid(row=3, column=3, padx=5, pady=5)

Label(miFrame, text="Género:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
Radiobutton(miFrame, text="Masculino", variable=genero, value="Masculino").grid(row=4, column=1, sticky="w")
Radiobutton(miFrame, text="Femenino", variable=genero, value="Femenino").grid(row=5, column=1, sticky="w")

Checkbutton(miFrame, text="Usuario activo", variable=estado).grid(row=5, column=2, pady=5)

Label(miFrame, text="Tipo de usuario:").grid(row=5, column=3, padx=5, pady=5, sticky="e")
combo_tipo = ttk.Combobox(
    miFrame,
    textvariable=tipo_usuario,
    values=["Administrador", "Docente", "Estudiante", "Invitado"],
    state="readonly",
    width=22
)
combo_tipo.grid(row=5, column=4, padx=5, pady=5)

# --- BOTONES Y MARCO PARA LA IMAGEN ---
Label(miFrame, text="Imagen:").grid(row=6, column=0, padx=5, pady=5, sticky="e")
Button(miFrame, text="Seleccionar Imagen", command=seleccionar_imagen, bg="#3498DB", fg="white", width=20).grid(row=6, column=1, padx=5, pady=5)

Button(miFrame, text="📎 Adjuntar Archivo", command=seleccionar_archivo, bg="#9B59B6", fg="white", width=20).grid(row=7, column=1, padx=5, pady=5)

marco_imagen = Frame(miFrame, width=140, height=140, bg="#E0E0E0", relief="sunken", bd=1)
marco_imagen.grid(row=6, column=2, rowspan=3, padx=10, pady=5)
marco_imagen.grid_propagate(False)

etiqueta_imagen = Label(marco_imagen, text="Sin Imagen", bg="#E0E0E0", fg="#666666", font=("Arial", 9))
etiqueta_imagen.pack(fill=BOTH, expand=True)

etiqueta_archivo = Label(miFrame, text="Archivo: No adjunto", width=30, anchor="w")
etiqueta_archivo.grid(row=8, column=0, columnspan=2, padx=5, pady=5)

# =========================================================================
# FRAME DE BOTONES
# =========================================================================

frame_botones = Frame(raiz, bd=2, relief="groove", padx=10, pady=10)
frame_botones.pack(padx=10, pady=5, fill="x")

Button(frame_botones, text="➕ INSERTAR", command=guardar_contacto, bg="#27AE60", fg="white", font=("Arial", 10, "bold"), width=13).pack(side=LEFT, padx=5)
Button(frame_botones, text="✏️ ACTUALIZAR", command=actualizar, bg="#F39C12", fg="white", font=("Arial", 10, "bold"), width=13).pack(side=LEFT, padx=5)
Button(frame_botones, text="🗑️ ELIMINAR", command=eliminar, bg="#E74C3C", fg="white", font=("Arial", 10, "bold"), width=13).pack(side=LEFT, padx=5)
Button(frame_botones, text="🧹 LIMPIAR", command=limpiar, bg="#34495E", fg="white", font=("Arial", 10, "bold"), width=13).pack(side=LEFT, padx=5)
Button(frame_botones, text="💾 GUARDAR CONTACTO", command=guardar_contacto, bg="#8E44AD", fg="white", font=("Arial", 10, "bold"), width=18).pack(side=LEFT, padx=5)
Button(frame_botones, text="🚪 SALIR", command=raiz.destroy, bg="#7F8C8D", fg="white", font=("Arial", 10, "bold"), width=10).pack(side=LEFT, padx=5)

# =========================================================================
# BUSCADOR
# =========================================================================

frame_buscar = Frame(raiz)
frame_buscar.pack(padx=10, pady=5, fill="x")

Label(frame_buscar, text="Buscar:").pack(side=LEFT, padx=5)
entrada_buscar = Entry(frame_buscar, width=40)
entrada_buscar.pack(side=LEFT, padx=5)
entrada_buscar.bind("<KeyRelease>", lambda e: buscar())
Button(frame_buscar, text="🔍 BUSCAR", command=buscar, bg="#2980B9", fg="white", width=15).pack(side=LEFT, padx=5)
Button(frame_buscar, text="MOSTRAR TODOS", command=mostrar_datos, bg="#16A085", fg="white", width=15).pack(side=LEFT, padx=5)

# =========================================================================
# TABLA DE CONTACTOS (TREEVIEW)
# =========================================================================

frame_tabla = Frame(raiz, bd=2, relief="groove")
frame_tabla.pack(padx=10, pady=5, fill="both", expand=True)

scroll_vertical = Scrollbar(frame_tabla, orient=VERTICAL)
scroll_vertical.pack(side=RIGHT, fill=Y)

scroll_horizontal = Scrollbar(frame_tabla, orient=HORIZONTAL)
scroll_horizontal.pack(side=BOTTOM, fill=X)

columnas = ("ID", "Nombre", "Apellido", "Correo", "Dirección", "Ciudad", "Código Postal", "Género", "Estado", "Tipo Usuario")

tabla = ttk.Treeview(
    frame_tabla,
    columns=columnas,
    show="headings",
    yscrollcommand=scroll_vertical.set,
    xscrollcommand=scroll_horizontal.set,
    height=10
)

for columna in columnas:
    tabla.heading(columna, text=columna)
    tabla.column(columna, width=120, anchor="center")

tabla.column("ID", width=40)
tabla.column("Nombre", width=110)
tabla.column("Apellido", width=110)
tabla.column("Correo", width=160)
tabla.column("Dirección", width=150)
tabla.column("Ciudad", width=110)
tabla.column("Código Postal", width=90)
tabla.column("Género", width=90)
tabla.column("Estado", width=80)
tabla.column("Tipo Usuario", width=120)

tabla.pack(side=LEFT, fill=BOTH, expand=True)

scroll_vertical.config(command=tabla.yview)
scroll_horizontal.config(command=tabla.xview)

tabla.bind("<ButtonRelease-1>", seleccionar_registro)

# =========================================================================
# CARGAR DATOS
# =========================================================================

mostrar_datos()
raiz.mainloop()