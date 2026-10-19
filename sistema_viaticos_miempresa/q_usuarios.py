# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""q_usuarios.py — Alta, cambio y baja de usuarios (solo superusuario).

Misma pantalla de `ui_usuarios.py`: el superusuario crea usuarios, cambia nombre,
rol y clave, y elimina usuarios; cada cambio queda en la bitácora.
"""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout

import database as db
import qt_comunes as C

ROLES_UI = [("EMPLEADO(A)", db.ROL_VENDEDOR), ("JUSTIFICACIÓN", db.ROL_JUSTIFICA)]
ROLES_DICT = dict(ROLES_UI)
ROLES_INV = {v: k for k, v in ROLES_UI}

COLUMNAS = [
    ("usuario", "USUARIO", 200),
    ("nombre", "NOMBRE", 250),
    ("rol", "ROL", 160),
    ("clave", "CLAVE", 130),
    ("creado", "CREADO", 160),
]


class UsuariosWindow(C.Ventana):
    """Ventana del módulo de usuarios."""

    def __init__(self, master=None, usuario=None):
        usuario = usuario or {"usuario": "SISTEMA", "nombre": "SISTEMA", "rol": ""}
        super().__init__(
            titulo="Usuarios del sistema — Solo superusuario",
            usuario=usuario, padre=master, ancho=1040, alto=740,
            info=C.etiqueta_sesion(usuario))
        self.sel_usuario = None
        if usuario.get("rol") != db.ROL_SUPER:
            C.aviso(self, "Usuarios", "Solo el superusuario administra los usuarios.")
            QTimer.singleShot(0, self.reject)      # la ventana se cierra sola
            return
        self._build()
        self._refrescar()

    # ---------- construcción ----------
    def _build(self):
        tarjeta = C.Tarjeta("Datos del usuario",
                            "Escriba los datos y use los botones; el usuario se elige "
                            "haciendo clic en la lista de abajo. Las claves se guardan "
                            "cifradas: no se pueden leer, solo cambiar.")
        self.txt_usuario = C.campo("", ancho=180, mayusculas=True, maximo=20)
        self.txt_nombre = C.campo("", ancho=260, mayusculas=True, maximo=60)
        self.cb_rol = C.combo([r[0] for r in ROLES_UI], ROLES_UI[0][0], ancho=170)
        self.txt_clave = C.campo("", ancho=150)
        tarjeta.agregar(C.rejilla([
            [("Usuario:", self.txt_usuario),
             ("Nombre que aparecerá en el sistema:", self.txt_nombre)],
            [("Rol:", self.cb_rol), ("Clave:", self.txt_clave)],
        ], esp=8))

        barra = C.margenes(QHBoxLayout(), esp=8)
        barra.addWidget(C.boton_amarillo("➕  Crear usuario", self._crear))
        barra.addWidget(C.boton_primario("💾  Guardar cambios", self._guardar))
        barra.addWidget(C.boton_peligro("🗑  Eliminar", self._eliminar))
        barra.addWidget(C.boton_secundario("🧹  Limpiar", self._limpiar))
        barra.addStretch(1)
        self.lbl_estado = C.etiqueta("Nuevo usuario", ayuda=True)
        barra.addWidget(self.lbl_estado)
        tarjeta.agregar_fila(barra)
        self.agregar(tarjeta)

        self.tabla = C.TablaDatos(
            COLUMNAS, titulo="Usuarios que pueden ingresar al sistema",
            nombre="usuarios", alto=300, filtros=True)
        self.tabla.agregar_boton("🔄  Actualizar", self._refrescar)
        self.tabla.al_seleccionar(self._al_seleccionar)
        self.agregar(self.tabla, 1)

    # ---------- datos ----------
    def _refrescar(self):
        """Vuelve a leer la lista de usuarios."""
        try:
            usuarios = db.listar_usuarios(incluir_super=True)
        except Exception as ex:
            C.error(self, "Usuarios", "No se pudo leer la lista de usuarios:\n\n%s" % ex)
            usuarios = []
        filas = [{"usuario": u.get("usuario") or "",
                  "nombre": u.get("nombre") or "",
                  "rol": db.ETIQUETA_ROL.get(u.get("rol"), u.get("rol") or ""),
                  "clave": "••••  cifrada" if u.get("tiene_clave") else "—",
                  "creado": u.get("creado_el") or ""} for u in usuarios]
        self.tabla.set_datos(filas)
        return self

    def _al_seleccionar(self, fila):
        """Carga en el formulario el usuario que se eligió en la lista."""
        if not fila:
            return
        try:
            actual = next((u for u in db.listar_usuarios()
                           if u.get("usuario") == fila.get("usuario")), None)
        except Exception:
            actual = None
        if not actual:
            return
        self.sel_usuario = actual.get("usuario")
        self.txt_usuario.setText(actual.get("usuario") or "")
        self.txt_nombre.setText(actual.get("nombre") or "")
        # La clave está cifrada y no se puede mostrar: se deja vacía, y vacía
        # significa «no cambiarla» al guardar.
        self.txt_clave.clear()
        self.txt_clave.setPlaceholderText("Nueva clave (vacío = no cambiar)")
        es_super = actual.get("rol") == db.ROL_SUPER
        self._bloquear_datos(es_super)
        if es_super:
            C.poner_combo(self.cb_rol, "SUPERUSUARIO")
            self.lbl_estado.setText("Superusuario: escriba la clave nueva y use "
                                    "«Guardar cambios» (lo demás no se cambia)")
        else:
            C.poner_combo(self.cb_rol, ROLES_INV.get(actual.get("rol"), ROLES_UI[0][0]))
            self.lbl_estado.setText("Editando: %s · deje la clave vacía para no cambiarla"
                                    % self.sel_usuario)

    def _bloquear_datos(self, bloquear):
        """Bloquea usuario, nombre y rol cuando lo que se edita es el superusuario.

        Del superusuario solo se puede cambiar la clave: su nombre de usuario, su
        nombre y su rol quedan fijos, y tampoco se puede eliminar.
        """
        self.txt_usuario.setReadOnly(bloquear)
        self.txt_nombre.setReadOnly(bloquear)
        self.cb_rol.setEnabled(not bloquear)

    def _limpiar(self):
        """Deja el formulario listo para un usuario nuevo."""
        self.sel_usuario = None
        for campo in (self.txt_usuario, self.txt_nombre, self.txt_clave):
            campo.clear()
        self._bloquear_datos(False)
        C.poner_combo(self.cb_rol, ROLES_UI[0][0])
        self.lbl_estado.setText("Nuevo usuario")
        self.tabla.tabla.clearSelection()

    def _datos(self, exigir_clave=True):
        """Lo que se va a guardar (o None si falta algo, con su aviso).

        Al editar un usuario la clave puede quedar vacía: significa «no cambiarla»
        (las claves están cifradas, así que no se pueden mostrar).
        """
        usuario = (self.txt_usuario.text() or "").strip().upper()
        nombre = (self.txt_nombre.text() or "").strip().upper() or usuario
        clave = (self.txt_clave.text() or "").strip()
        rol = ROLES_DICT.get(self.cb_rol.currentText(), db.ROL_VENDEDOR)
        if not usuario or (exigir_clave and not clave):
            C.aviso(self, "Usuarios", "Complete el usuario y la clave.")
            return None
        return usuario, nombre, clave, rol

    # ---------- acciones ----------
    def _crear(self):
        datos = self._datos()
        if not datos:
            return
        usuario, nombre, clave, rol = datos
        try:
            creado = db.agregar_usuario(usuario, clave, nombre, rol)
        except ValueError as ex:
            C.error(self, "Usuarios", str(ex))
            return
        if not creado:
            C.aviso(self, "Usuarios", "El usuario %s ya existe." % usuario)
            return
        db.registrar_bitacora(self.usuario, "CREÓ USUARIO", "usuarios", usuario,
                             "%s · %s" % (nombre, db.ETIQUETA_ROL.get(rol, rol)))
        self._refrescar()
        self._limpiar()
        C.informar(self, "Usuarios", "Usuario %s creado correctamente." % usuario)

    def _es_super(self, usuario):
        """True si el usuario de la lista es el superusuario del sistema."""
        try:
            return any(u.get("usuario") == usuario and u.get("rol") == db.ROL_SUPER
                       for u in db.listar_usuarios(incluir_super=True))
        except Exception:
            return False

    def _guardar(self):
        if not self.sel_usuario:
            C.aviso(self, "Usuarios", "Seleccione un usuario de la lista.")
            return
        datos = self._datos(exigir_clave=False)
        if not datos:
            return
        usuario, nombre, clave, rol = datos
        if usuario != self.sel_usuario:
            C.aviso(self, "Usuarios", "El nombre de usuario no se puede cambiar.\n"
                                      "Cree un usuario nuevo si lo necesita.")
            return
        if self._es_super(usuario):
            # Del superusuario solo se cambia la clave: su nombre y su rol quedan fijos.
            if not clave:
                C.aviso(self, "Usuarios", "Escriba la nueva clave del superusuario.")
                return
            if not db.actualizar_usuario(usuario, clave=clave, permitir_super=True):
                C.error(self, "Usuarios", "No se pudo cambiar la clave del superusuario.")
                return
            db.registrar_bitacora(self.usuario, "CAMBIÓ CLAVE SUPERUSUARIO", "usuarios",
                                  usuario, "Clave del superusuario actualizada")
            self._refrescar()
            self._limpiar()
            C.informar(self, "Usuarios", "Clave del superusuario actualizada.")
            return
        if not db.actualizar_usuario(usuario, clave=clave or None, nombre=nombre, rol=rol):
            C.error(self, "Usuarios", "No se pudo actualizar el usuario.")
            return
        db.registrar_bitacora(self.usuario, "CAMBIÓ USUARIO", "usuarios", usuario,
                             "%s · datos%s" % (nombre, " y clave actualizados"
                                               if clave else " actualizados"))
        self._refrescar()
        C.informar(self, "Usuarios", "Usuario %s actualizado." % usuario)

    def _eliminar(self):
        if not self.sel_usuario:
            C.aviso(self, "Usuarios", "Seleccione un usuario de la lista.")
            return
        if self._es_super(self.sel_usuario):
            C.aviso(self, "Usuarios", "El superusuario no se puede eliminar:\n"
                                      "solo se le puede cambiar la clave.")
            return
        if not C.confirmar(self, "Usuarios", "¿Eliminar el usuario %s?" % self.sel_usuario,
                           si="Sí, eliminar", no="Cancelar"):
            return
        usuario = self.sel_usuario
        if db.eliminar_usuario(usuario):
            db.registrar_bitacora(self.usuario, "ELIMINÓ USUARIO", "usuarios", usuario,
                                  "Baja de usuario")
            self._refrescar()
            self._limpiar()
        else:
            C.error(self, "Usuarios", "No se pudo eliminar ese usuario.")

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
