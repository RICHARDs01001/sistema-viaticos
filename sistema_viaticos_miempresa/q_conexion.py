# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""q_conexion.py — Conexión a la base de datos y migración (solo superusuario), PySide6.

Mismas funciones que `ui_conexion.py`:
  - Ver qué conexión está en uso (local o central) y cuántos datos hay.
  - Elegir entre la base LOCAL (SQLite de esta PC) y la CENTRAL del servidor.
  - Escribir y probar los datos de PostgreSQL (host, puerto, base, usuario, clave).
  - Guardar los archivos de respaldo dentro de la base o en una carpeta (puede ser de red).
  - Fijar la numeración de los viáticos por año.
  - Elegir el tamaño de la pantalla en ESTA computadora (zoom).
  - Subir los datos locales a la base central (migración).

También trae la pantalla que aparece al arrancar cuando la base no responde
(`VentanaServidor` y `asegurar_conexion`), para poder corregir la dirección del
servidor o trabajar en local.
"""
import os
import subprocess
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QHBoxLayout

import configuracion as cfg
import database as db
import qt_comunes as C
import qt_tema as T

# Mismas opciones de tamaño que la interfaz anterior (tema.ZOOM_OPCIONES).
OPCIONES_ZOOM = (("Automático", None), ("100 %", 1.0), ("90 %", 0.9),
                 ("80 %", 0.8), ("70 %", 0.7), ("60 %", 0.6))

AYUDA_SERVIDOR = (
    "1) En el servidor: abra la carpeta «servidor» y ejecute  el servicio de PostgreSQL encendido\n"
    "   (queda PostgreSQL escuchando en el puerto 5432).\n"
    "2) En las demás computadoras solo hace falta el .exe: ya trae la dirección\n"
    "   del servidor. Si alguna vez cambia, escríbala aquí, pulse «Probar conexión»\n"
    "   y luego «Guardar».\n"
    "3) En UNA sola máquina (la que tiene los datos actuales): pulse\n"
    "   «⬆ Subir mis datos locales a la central». Eso copia empleados, vehículos,\n"
    "   parámetros, clientes, viáticos, ajustes, justificaciones, respaldos y la\n"
    "   bitácora a la base central.\n"
    "4) Abra el sistema en las demás máquinas: ya verán los mismos datos.")


def zoom_texto(valor):
    """«Automático» o «80 %», para mostrar en pantalla y en los avisos."""
    return "Automático" if not valor else "%d %%" % int(round(float(valor) * 100))


def reiniciar_sistema():
    """Cierra el sistema y lo vuelve a abrir para que se aplique el tamaño nuevo."""
    orden = [sys.executable]
    if not getattr(sys, "frozen", False):
        orden.append(os.path.abspath(sys.argv[0]))
    try:
        subprocess.Popen(orden, cwd=str(cfg.carpeta_app()))
    except Exception:
        return False
    app = QApplication.instance()
    if app is not None:
        app.quit()
    return True


class ConexionWindow(C.Ventana):
    """Ventana de conexión, respaldos, numeración y tamaño de pantalla."""

    def __init__(self, master=None, usuario=None):
        usuario = usuario or {"usuario": "SISTEMA", "nombre": "SISTEMA", "rol": ""}
        super().__init__(
            titulo="Conexión y base de datos — Superusuario",
            usuario=usuario, padre=master, ancho=1020, alto=800,
            info=C.etiqueta_sesion(usuario))
        if usuario.get("rol") != db.ROL_SUPER:
            C.aviso(self, "Conexión", "Solo el superusuario puede cambiar la conexión.")
            QTimer.singleShot(0, self.reject)
            return
        self._build()
        self._cargar()

    # ---------- construcción ----------
    def _build(self):
        # --- conexión en uso ---
        actual = C.Tarjeta("Conexión en uso", "Lo que están usando todas las pantallas ahora")
        self.lbl_actual = C.etiqueta("", clave=True)
        self.lbl_local = C.etiqueta("")
        self.lbl_central = C.etiqueta("")
        actual.agregar(self.lbl_actual)
        actual.agregar(self.lbl_local)
        actual.agregar(self.lbl_central)
        self.agregar(actual)

        # --- tipo de base ---
        tipo = C.Tarjeta("Tipo de base", "Elija de dónde leen y escriben los datos")
        self.rb_motor, self.radios_motor = C.radios(
            [("Base LOCAL (cada máquina con su archivo SQLite)", "sqlite"),
             ("Base CENTRAL en el servidor (PostgreSQL)", "postgres")],
            actual="sqlite")
        tipo.agregar(self.rb_motor)
        self.agregar(tipo)

        # --- datos de PostgreSQL ---
        pg = C.Tarjeta("Datos del servidor (PostgreSQL)",
                       "El equipo donde corre la base central")
        self.e_host = C.campo("", ancho=220)
        self.e_puerto = C.campo("", ancho=90)
        self.e_base = C.campo("", ancho=160)
        self.e_usuario = C.campo("", ancho=160)
        self.e_clave = C.campo_clave(ancho=160)
        pg.agregar(C.rejilla([
            [("Servidor (IP o nombre):", self.e_host), ("Puerto:", self.e_puerto),
             ("Base de datos:", self.e_base)],
            [("Usuario:", self.e_usuario), ("Clave:", self.e_clave)],
        ], esp=8))
        self.agregar(pg)

        # --- archivos de respaldo ---
        resp = C.Tarjeta("Archivos de respaldo (facturas)",
                         "Dónde se guardan las facturas y comprobantes que se suben")
        self.rb_resp, self.radios_resp = C.radios(
            [("Guardar dentro de la base central (recomendado: todas las máquinas ven "
              "los archivos)", "base"),
             ("Guardar en una carpeta compartida del servidor", "carpeta")],
            actual="base")
        resp.agregar(self.rb_resp)
        fila_carpeta = C.margenes(QHBoxLayout(), esp=8)
        self.e_carpeta = C.campo("", ancho=520)
        fila_carpeta.addWidget(C.etiqueta("Carpeta:", clave=True))
        fila_carpeta.addWidget(self.e_carpeta, 1)
        fila_carpeta.addWidget(C.boton_secundario("Elegir…", self._elegir_carpeta))
        fila_carpeta.addStretch(1)
        resp.agregar_fila(fila_carpeta)
        self.agregar(resp)

        # --- numeración ---
        num = C.Tarjeta("Numeración de viáticos (reinicia cada año)",
                        "Puede fijar en qué número va el próximo viático del año")
        self.lbl_num = C.etiqueta("", clave=True)
        num.agregar(self.lbl_num)
        fila_num = C.margenes(QHBoxLayout(), esp=8)
        self.e_num_anio = C.campo("", ancho=90)
        self.e_num_inicio = C.campo("", ancho=90)
        fila_num.addWidget(C.etiqueta("Año:", clave=True))
        fila_num.addWidget(self.e_num_anio)
        fila_num.addWidget(C.etiqueta("El próximo viático de ese año será el N°:",
                                      clave=True))
        fila_num.addWidget(self.e_num_inicio)
        fila_num.addWidget(C.boton_amarillo("💾  Fijar numeración", self._fijar_numeracion))
        fila_num.addStretch(1)
        num.agregar_fila(fila_num)
        self.agregar(num)

        # --- tamaño de la pantalla (de esta PC) ---
        pan = C.Tarjeta("Tamaño de la pantalla en esta computadora",
                        "Solo afecta a esta máquina: se guarda en config.json")
        self.rb_zoom, self.radios_zoom = C.radios(
            [(texto, valor) for texto, valor in OPCIONES_ZOOM], actual=None,
            horizontal=True)
        pan.agregar(self.rb_zoom)
        self.lbl_zoom = C.etiqueta("", clave=True)
        pan.agregar(self.lbl_zoom)
        self.agregar(pan)

        # --- botones de acción ---
        barra = C.margenes(QHBoxLayout(), esp=8)
        barra.addWidget(C.boton_amarillo("💾  Guardar", self._guardar))
        barra.addWidget(C.boton_primario("🔌  Probar conexión", self._probar))
        barra.addWidget(C.boton_primario("⬆  Subir mis datos locales a la central",
                                        self._migrar))
        barra.addWidget(C.boton_secundario("🔄  Actualizar información", self._cargar))
        self.lbl_estado = C.etiqueta("")
        barra.addWidget(self.lbl_estado)
        barra.addStretch(1)
        self.agregar_fila(barra)

        # --- ayuda ---
        ayuda = C.Tarjeta("Para dejar el servidor en marcha",
                          "Los pasos completos están en documentacion\\SERVIDOR_POSTGRES.md")
        lbl = C.etiqueta(AYUDA_SERVIDOR)
        lbl.setStyleSheet("font-family: Consolas, 'Courier New', monospace;")
        ayuda.agregar(lbl)
        self.agregar(ayuda)

    # ---------- utilidades ----------
    @staticmethod
    def _set(caja, valor):
        caja.setText("" if valor is None else str(valor))

    @staticmethod
    def _valor_radio(botones, defecto=None):
        for valor, boton in botones.items():
            if boton.isChecked():
                return valor
        return defecto

    @staticmethod
    def _resumen(datos):
        """Texto corto con lo que hay en una base (local o central)."""
        if not datos or "error" in datos:
            return str(datos)
        return ("%s viáticos · %s empleados · %s clientes · %s respaldos · "
                "%s movimientos de bitácora"
                % (datos.get("viajes", 0), datos.get("empleados", 0),
                   datos.get("clientes", 0), datos.get("respaldos", 0),
                   datos.get("bitacora", 0)))

    # ---------- datos ----------
    def _cargar(self):
        """Lee config.json y muestra la situación real (local y central)."""
        datos = cfg.leer()
        pg = datos.get("postgres", {})
        motor = "postgres" if str(datos.get("motor")).lower() == "postgres" else "sqlite"
        for boton in self.radios_motor.values():
            boton.setChecked(boton.property("valor") == motor)
        self._set(self.e_host, pg.get("host", "localhost"))
        self._set(self.e_puerto, str(pg.get("puerto", 5432)))
        self._set(self.e_base, pg.get("base", "viaticos"))
        self._set(self.e_usuario, pg.get("usuario", "miempresa"))
        self._set(self.e_clave, pg.get("clave", ""))
        modo = cfg.modo_respaldos()
        for boton in self.radios_resp.values():
            boton.setChecked(boton.property("valor") == modo)
        self._set(self.e_carpeta, (datos.get("respaldos", {}).get("carpeta") or ""))
        self.lbl_actual.setText("En uso: " + cfg.describir())
        self._cargar_numeracion()
        self._cargar_zoom()
        try:
            import migracion
            self.lbl_local.setText("Datos locales (SQLite): "
                                   + self._resumen(migracion.resumen_local()))
        except Exception as ex:
            self.lbl_local.setText("Datos locales: no se pudieron leer (%s)" % ex)
        try:
            if db.es_postgres():
                db.init_db()
                self.lbl_central.setText(
                    "Datos en la central: %d viáticos · %d empleados · %d clientes · "
                    "%d movimientos de bitácora"
                    % (len(db.resumen_viaticos()), len(db.listar_empleados()),
                       len(db.listar_clientes()), len(db.listar_bitacora())))
            else:
                self.lbl_central.setText("Datos en la central: (la conexión actual es local)")
        except Exception as ex:
            self.lbl_central.setText("Datos en la central: no se pudo conectar (%s)" % ex)

    def _datos(self):
        """Lo que se guardaría en config.json (motor, postgres, respaldos y zoom)."""
        return {
            "motor": self._valor_radio(self.radios_motor, "sqlite"),
            "postgres": {"host": (self.e_host.text() or "").strip(),
                         "puerto": int((self.e_puerto.text() or "").strip() or 5432),
                         "base": (self.e_base.text() or "").strip(),
                         "usuario": (self.e_usuario.text() or "").strip(),
                         "clave": self.e_clave.text()},
            "respaldos": {"modo": self._valor_radio(self.radios_resp, "base"),
                          "carpeta": (self.e_carpeta.text() or "").strip()},
            # El tamaño de la pantalla es de ESTA computadora: se guarda en
            # config.json (junto al .exe) y no viaja a la base ni a las demás PC.
            "interfaz": {"zoom": self._zoom_elegido() or 0},
        }

    # ---------- tamaño de la pantalla (zoom) ----------
    def _zoom_elegido(self):
        """Tamaño marcado aquí. None = Automático, según la pantalla de esta PC."""
        valor = self._valor_radio(self.radios_zoom, None)
        try:
            valor = float(valor or 0)
        except (TypeError, ValueError):
            valor = 0.0
        return None if valor <= 0 else round(valor, 3)

    def _cargar_zoom(self):
        """Marca el tamaño guardado en esta PC y muestra cuál está en uso."""
        real = T.zoom_guardado()
        elegido = real
        if real is not None:      # un valor escrito a mano va al botón más cercano
            elegido = min((v for _, v in OPCIONES_ZOOM if v is not None),
                          key=lambda v: abs(v - real))
        for boton in self.radios_zoom.values():
            valor = boton.property("valor")
            boton.setChecked((None if elegido is None else round(float(elegido), 3))
                             == (None if valor is None else round(float(valor), 3)))
        self.lbl_zoom.setText("En uso: " + zoom_texto(real))

    # ---------- numeración ----------
    def _cargar_numeracion(self):
        try:
            datos = db.numeraciones()
        except Exception as ex:
            self.lbl_num.setText("No se pudo leer la numeración (%s)" % ex)
            return
        resumen = " · ".join(
            "%s: %s viático(s), el próximo es el N° %s"
            % (d["anio"], d["viaticos"], d["siguiente"]) for d in datos[:4])
        self.lbl_num.setText(resumen or "Sin viáticos registrados")
        if not (self.e_num_anio.text() or "").strip():
            self._set(self.e_num_anio, str(db.anio_actual()))
            self._set(self.e_num_inicio, str(datos[0]["siguiente"]) if datos else "1")

    def _fijar_numeracion(self):
        try:
            anio = int((self.e_num_anio.text() or "").strip())
            numero = int((self.e_num_inicio.text() or "").strip())
        except ValueError:
            C.error(self, "Numeración", "Escriba un año y un número válidos.")
            return
        if not (2000 <= anio <= 2100) or numero < 1:
            C.error(self, "Numeración", "Revise el año y el número.")
            return
        if not C.confirmar(
                self, "Numeración",
                "El próximo viático del año %d será el N° %d.\n\n"
                "Si ya existen viáticos en ese año, el sistema usará el siguiente número "
                "libre para no repetir ninguno.\n\n¿Confirmar?" % (anio, numero),
                si="Sí, fijar numeración"):
            return
        try:
            siguiente = db.fijar_inicio(numero, anio)
        except Exception as ex:
            C.error(self, "Numeración", "No se pudo fijar la numeración:\n\n%s" % ex)
            return
        db.registrar_bitacora(self.usuario, "FIJÓ NUMERACIÓN DE VIÁTICOS", "viáticos",
                             str(anio), "El próximo viático será el N° %d" % numero)
        self._cargar_numeracion()
        if db.numero_visible(siguiente) != numero:
            C.informar(self, "Numeración",
                       "Se fijó el N° %d, pero en %d ya existen viáticos hasta el N° %d. "
                       "El próximo será el N° %d."
                       % (numero, anio, db.numero_visible(siguiente) - 1,
                          db.numero_visible(siguiente)))
        else:
            C.informar(self, "Numeración",
                       "Listo: el próximo viático de %d será el N° %d." % (anio, numero))

    # ---------- acciones ----------
    def _elegir_carpeta(self):
        ruta = QFileDialog.getExistingDirectory(
            self, "Carpeta de respaldos (puede ser de red)")
        if ruta:
            self._set(self.e_carpeta, ruta)
            for boton in self.radios_resp.values():
                boton.setChecked(boton.property("valor") == "carpeta")

    def _guardar(self):
        try:
            datos = self._datos()
        except ValueError:
            C.error(self, "Conexión", "El puerto debe ser un número.")
            return
        antes = T.zoom_guardado()
        try:
            cfg.guardar(datos)
        except OSError as ex:
            C.error(self, "Conexión", "No se pudo guardar config.json:\n\n%s" % ex)
            return
        db.cerrar_conexiones()      # la conexión guardada era de la dirección anterior
        db.registrar_bitacora(self.usuario, "CAMBIÓ CONEXIÓN", "conexión",
                              datos["motor"], cfg.describir())
        self._cargar()
        C.informar(self, "Conexión", "Configuración guardada.\n\n" + cfg.describir())
        if (antes or 0) != (T.zoom_guardado() or 0):
            self._aplicar_zoom()

    def _aplicar_zoom(self):
        """Ofrece cerrar y abrir el sistema para que se vea el tamaño nuevo."""
        aviso = ("El tamaño «%s» se aplica al volver a abrir el sistema.\n\n"
                 "¿Cerrar y abrir el sistema ahora?" % zoom_texto(T.zoom_guardado()))
        if not C.confirmar(self, "Tamaño de la pantalla", aviso, si="Sí, reiniciar"):
            return
        if not reiniciar_sistema():
            C.informar(self, "Tamaño de la pantalla",
                       "Cierre el sistema y vuelva a abrirlo para ver el tamaño nuevo.")

    def _probar(self):
        try:
            ok, mensaje = db.probar_conexion(self._datos())
        except Exception as ex:
            ok, mensaje = False, str(ex)
        self.lbl_estado.setText("OK" if ok else "FALLÓ")
        (C.informar if ok else C.error)(self, "Probar conexión", mensaje)

    def _paso(self, texto):
        """Muestra en qué parte va la migración."""
        self.lbl_estado.setText(str(texto))

    # ---------- migración a la base central ----------
    def _migrar(self):
        try:
            datos = self._datos()
        except ValueError:
            C.error(self, "Migración", "El puerto debe ser un número.")
            return
        if datos["motor"] != "postgres":
            C.aviso(self, "Migración",
                    "Elija primero «Base CENTRAL en el servidor» y guarde.")
            return
        try:
            import migracion
        except Exception as ex:
            C.error(self, "Migración",
                    "No se pudo cargar el módulo de migración:\n\n%s" % ex)
            return
        # Se lee primero lo que hay en ESTA máquina: así el aviso dice exactamente lo
        # que se va a copiar y evita vaciar la central sin darse cuenta (caso típico:
        # abrir el .exe de la carpeta «dist», cuya base propia está vacía).
        local = migracion.resumen_local()
        if local.get("error"):
            C.error(self, "Migración", str(local["error"]))
            return
        aviso = ("Esta máquina enviará:\n\n" + self._resumen(local) +
                 "\n\nSe REEMPLAZA todo lo que haya en la base central.\n\n"
                 "Hágalo solo desde la máquina que tiene los datos buenos.")
        if not local.get("viajes"):
            aviso = ("⚠ CUIDADO: esta máquina no tiene ningún viático. Si continúa, la base "
                     "central quedará VACÍA.\n\nEsto pasa cuando se abre el sistema desde el "
                     ".exe de la carpeta «dist»: ese ejecutable usa su propia carpeta "
                     "«dist\\data», que está vacía. Para subir los datos reales abra el sistema "
                     "con INICIAR.bat (o desde el código, no desde el .exe).\n\n" + aviso)
        if not C.confirmar_peligro(self, "Subir datos a la central", aviso + "\n\n¿Continuar?",
                                   si="Sí, subir los datos"):
            return
        cfg.guardar(datos)
        self._paso("Migrando…")
        QApplication.processEvents()          # que el aviso se vea en pantalla
        try:
            resumen = migracion.migrar(progreso=self._paso)
        except Exception as ex:
            C.error(self, "Migración", "Falló la migración:\n\n%s" % ex)
            self.lbl_estado.setText("FALLÓ")
            return
        db.olvidar_cache()                    # la base cambió por completo
        self.lbl_estado.setText("Listo")
        db.registrar_bitacora(self.usuario, "MIGRÓ A BASE CENTRAL", "conexión",
                              cfg.leer()["postgres"]["host"], self._resumen(resumen))
        self._cargar()
        C.informar(self, "Migración",
                   "Datos copiados a la base central:\n\n" + self._resumen(resumen) +
                   "\n\nAhora el sistema trabaja contra el servidor.")


class VentanaServidor(C.Ventana):
    """Pantalla que aparece al arrancar cuando la base central no responde.

    Permite escribir otra dirección del servidor (y guardarla) o seguir trabajando en
    esta computadora con la base local. Deja en `self.accion`: "local", "salir" o None
    (se guardó otra conexión y hay que volver a intentar).
    """

    def __init__(self, mensaje="", padre=None):
        super().__init__(
            titulo="No se pudo abrir la base de datos", padre=padre,
            ancho=900, alto=640,
            subtitulo="Escriba otra dirección del servidor o trabaje en esta computadora "
                      "con la base local")
        self.accion = None
        self.boton_volver.hide()          # aquí todavía no se «vuelve al menú»
        datos = cfg.leer().get("postgres", {})

        tabla = C.Tarjeta("Datos del servidor (PostgreSQL)",
                          "Lo que se probará y quedará guardado en config.json")
        self.e_host = C.campo(datos.get("host", ""), ancho=200)
        self.e_puerto = C.campo(str(datos.get("puerto", 5432)), ancho=90)
        self.e_base = C.campo(datos.get("base", "viaticos"), ancho=150)
        self.e_usuario = C.campo(datos.get("usuario", "miempresa"), ancho=150)
        self.e_clave = C.campo_clave(ancho=150)
        self.e_clave.setText(datos.get("clave", ""))
        tabla.agregar(C.rejilla([
            [("Servidor (IP o nombre):", self.e_host), ("Puerto:", self.e_puerto)],
            [("Base de datos:", self.e_base), ("Usuario:", self.e_usuario)],
            [("Clave:", self.e_clave)],
        ], esp=8))
        self.lbl_error = C.etiqueta((mensaje or "").strip()[:900])
        self.lbl_error.setObjectName("error")
        tabla.agregar(self.lbl_error)
        self.agregar(tabla)

        barra = C.margenes(QHBoxLayout(), esp=8)
        barra.addWidget(C.boton_amarillo("🔌  Probar y guardar", self._probar))
        barra.addWidget(C.boton_secundario("💻  Trabajar en esta PC (base local)",
                                          self._local))
        barra.addWidget(C.boton_secundario("✖  Salir", self._salir))
        barra.addStretch(1)
        self.agregar_fila(barra)

    def _datos(self):
        """Lo que se guardaría: base central en el servidor indicado."""
        return {"motor": cfg.MOTOR_POSTGRES,
                "postgres": {"host": (self.e_host.text() or "").strip(),
                             "puerto": int((self.e_puerto.text() or "").strip() or 5432),
                             "base": (self.e_base.text() or "").strip(),
                             "usuario": (self.e_usuario.text() or "").strip(),
                             "clave": self.e_clave.text()},
                "respaldos": {"modo": "base", "carpeta": ""}}

    def _probar(self):
        try:
            datos = self._datos()
        except ValueError:
            self.lbl_error.setText("El puerto debe ser un número (por ejemplo 5432).")
            return
        ok, mensaje = db.probar_conexion(datos)
        if not ok:
            self.lbl_error.setText("No se pudo conectar:\n" + str(mensaje).strip()[:900])
            return
        cfg.guardar(datos)
        db.registrar_bitacora("SISTEMA", "CAMBIÓ CONEXIÓN (ARRANQUE)", "conexión",
                              datos["postgres"]["host"], cfg.describir())
        self.done(self.Accepted)

    def _local(self):
        """Trabajar sin servidor: usa la base SQLite de esta misma máquina."""
        cfg.guardar({"motor": cfg.MOTOR_SQLITE})
        self.accion = "local"
        self.done(self.Accepted)

    def _salir(self):
        self.accion = "salir"
        self.done(self.Rejected)


def asegurar_conexion(app=None):
    """Deja lista la base de datos antes de mostrar el ingreso.

    Devuelve True si se puede entrar al sistema. Si la base central del servidor no
    responde, muestra `VentanaServidor` para escribir otra dirección o para trabajar
    con la base local de esa máquina.
    """
    if app is None:
        app = QApplication.instance()
    if app is None:
        import q_login
        app = q_login.crear_app()
    T.aplicar_tema(app)
    while True:
        try:
            db.init_db()
            return True
        except Exception as ex:
            mensaje = str(ex)
        ventana = VentanaServidor(mensaje)
        ventana.exec()
        if ventana.accion == "salir":
            return False
        # accion None (se guardó otro servidor) o "local" (ya se guardó sqlite): en los
        # dos casos se vuelve a intentar con la configuración nueva.

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
