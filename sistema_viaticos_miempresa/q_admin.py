# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""q_admin.py — Parámetros y catálogos internos (PySide6), sin gestión de usuarios.

Mismas pestañas y mismas funciones que `ui_admin.py`:
  1) Parámetros del cálculo (horas límite y valores por día/km).
  2) Empleados (alta, baja e importación desde Excel).
  3) Clientes / proyectos (alta, baja e importación desde Excel).
  4) Vehículos (placa, tipo y chofer).
  5) Provincias y kilómetros desde Cuenca.

Cada cambio queda registrado en la bitácora, igual que antes.
"""
from datetime import time as dtime

from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QHBoxLayout, QListWidget, QTabWidget, QVBoxLayout, QWidget,
)

import database as db
import qt_comunes as C
import qt_tema as T
from calculos import horas_de_texto, horas_texto

PARAMS_UI = [
    ("hora_limite_desayuno", "Desayuno — hora límite de salida (HH:MM)", "time"),
    ("valor_desayuno", "Desayuno — valor por día (USD)", "float"),
    ("hora_limite_almuerzo", "Almuerzo — hora límite de regreso (HH:MM)", "time"),
    ("valor_almuerzo", "Almuerzo — valor por día (USD)", "float"),
    ("hora_limite_merienda", "Merienda — hora límite de regreso (HH:MM)", "time"),
    ("valor_merienda", "Merienda — valor por día (USD)", "float"),
    ("hora_limite_taxi_salida", "Taxi salida — hora límite (HH:MM)", "time"),
    ("valor_taxi_salida", "Taxi salida — valor (USD)", "float"),
    ("hora_limite_taxi_regreso", "Taxi regreso — hora límite (HH:MM)", "time"),
    ("valor_taxi_regreso", "Taxi regreso — valor (USD)", "float"),
    ("valor_hospedaje", "Hospedaje — valor por noche (USD)", "float"),
    ("valor_agua", "Agua — valor por día (USD)", "float"),
    ("valor_combustible_km", "Combustible — valor por km (USD)", "float"),
    ("valor_parqueadero_peaje", "Parqueadero/Peaje — valor sugerido por viaje (USD)", "float"),
    ("redondeo_cajero", "Redondeo cajero — múltiplo de (USD)", "float"),
    ("velocidad_automovil", "Estimado de viaje — velocidad del automóvil (km/h)", "float"),
    ("velocidad_camion", "Estimado de viaje — velocidad del camión/camioneta (km/h)", "float"),
    ("velocidad_bus", "Estimado de viaje — velocidad del bus (km/h)", "float"),
    ("horas_desayuno_viaje", "Estimado de viaje — horas extra por el desayuno en el camino", "float"),
    ("horas_almuerzo_viaje", "Estimado de viaje — horas extra por el almuerzo en el camino", "float"),
    ("horas_merienda_viaje", "Estimado de viaje — horas extra por la merienda en el camino", "float"),
    ("hospedaje_por_fechas", "Hospedaje — contar las noches por las fechas del viaje (como el Excel)", "si_no"),
    ("taxi_regreso_madrugada", "Taxi regreso — pagarlo también al que vuelve de madrugada (el Excel no lo paga)", "si_no"),
]

TIPOS_VEHICULO_UI = ["CAMIONETA", "CAMION", "CAMION GRUA", "AUTOMOVIL", "MOTO", "BUS",
                     "OTRO"]


class _PanelLista(QWidget):
    """Pestaña con una lista, un campo para escribir y sus botones."""

    def __init__(self, boton_agregar="Agregar", al_agregar=None, al_eliminar=None,
                 al_importar=None, ayuda="", padre=None):
        super().__init__(padre)
        lay = C.margenes(QVBoxLayout(self), 12, 12, 12, 12, 8)
        if ayuda:
            lay.addWidget(C.etiqueta(ayuda, ayuda=True))
        self.lista = QListWidget()
        self.lista.setAlternatingRowColors(True)
        lay.addWidget(self.lista, 1)
        barra = C.margenes(QHBoxLayout(), esp=6)
        self.entrada = C.campo("", mayusculas=True)
        barra.addWidget(self.entrada, 1)
        barra.addWidget(C.boton_primario(boton_agregar, al_agregar))
        barra.addWidget(C.boton_peligro("Eliminar", al_eliminar))
        if al_importar is not None:
            barra.addWidget(C.boton_amarillo("📥  Importar Excel", al_importar))
        lay.addLayout(barra)
        if al_agregar is not None:
            self.entrada.returnPressed.connect(al_agregar)
class AdminWindow(C.Ventana):
    """Ventana de parámetros y catálogos."""

    def __init__(self, master=None, usuario=None):
        usuario = usuario or {"usuario": "SISTEMA", "nombre": "MIEMPRESA"}
        super().__init__(
            titulo="Parámetros y catálogos — Sistema de Viáticos",
            usuario=usuario, padre=master, ancho=1080, alto=780,
            info=C.etiqueta_sesion(usuario))
        self.pestanas = QTabWidget()
        self.agregar(self.pestanas, 1)
        self._tab_parametros()
        self._tab_empleados()
        self._tab_clientes()
        self._tab_vehiculos()
        self._tab_rutas()

    # ------------------------------------------------- bitácora y parámetros
    def _bitacora(self, accion, entidad, referencia="", detalle=""):
        """Registra el cambio en el informe de actividad del superusuario."""
        db.registrar_bitacora(self.usuario, accion, entidad, referencia, detalle)

    def _tab_parametros(self):
        panel = QWidget()
        lay = C.margenes(QVBoxLayout(panel), 14, 14, 14, 14, 10)
        parametros = db.cargar_parametros()
        self._entradas = {}
        filas = []
        for attr, etiqueta, tipo in PARAMS_UI:
            valor = parametros[attr]
            if tipo == "si_no":
                # Parámetros de sí/no (por ejemplo «hospedaje por fechas»): se eligen
                # de la lista para que no se escriban valores raros.
                caja = C.combo(["SÍ", "NO"], "SÍ" if float(valor or 0) > 0 else "NO",
                               ancho=120)
            else:
                caja = C.campo("", ancho=120)
                caja.setText(valor.strftime("%H:%M") if tipo == "time"
                             else "%.2f" % float(valor))
            self._entradas[attr] = (caja, tipo)
            filas.append([(etiqueta, caja)])
        lay.addWidget(C.rejilla(filas, esp=6))
        barra = C.margenes(QHBoxLayout(), esp=8)
        barra.addWidget(C.boton_primario("💾  Guardar parámetros", self._guardar))
        barra.addStretch(1)
        lay.addLayout(barra)
        lay.addStretch(1)
        self.pestanas.addTab(panel, "⚙️ Parámetros")

    def _guardar(self):
        """Valida y guarda todos los parámetros (igual que antes: HH:MM y números)."""
        parametros = db.cargar_parametros()
        try:
            for attr, (caja, tipo) in self._entradas.items():
                texto = (caja.currentText() if isinstance(caja, QComboBox)
                         else (caja.text() or "")).strip()
                if tipo == "time":
                    h, m = texto.split(":")
                    if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
                        raise ValueError
                    parametros[attr] = dtime(int(h), int(m))
                elif tipo == "si_no":
                    parametros[attr] = 1.0 if texto.upper().startswith("S") else 0.0
                else:
                    parametros[attr] = float(texto)
        except ValueError:
            C.error(self, "Parámetros",
                    "Revise los valores. Use HH:MM y números válidos.")
            return
        db.guardar_parametros(parametros)
        self._bitacora("CAMBIÓ PARÁMETROS", "parámetros", "valor por día/km",
                       " · ".join("%s=%s" % (k, v)
                                  for k, v in list(parametros.items())[:6]) + " …")
        C.informar(self, "Parámetros", "Parámetros guardados correctamente.")

    # ------------------------------------------------------------- empleados
    def _tab_empleados(self):
        panel = _PanelLista(
            boton_agregar="Agregar empleado", al_agregar=self._add_emp,
            al_eliminar=self._del_emp, al_importar=self._importar_empleados,
            ayuda="Escriba el nombre del empleado y presione Agregar (o Enter). "
                  "Puede importar toda la lista desde un Excel.")
        self.pestanas.addTab(panel, "👥 Empleados")
        self.lst_emp = panel.lista
        self.txt_emp = panel.entrada
        self._ref_emp()

    def _ref_emp(self):
        """Vuelve a leer la lista de empleados."""
        self.lst_emp.clear()
        for nombre in db.listar_empleados():
            self.lst_emp.addItem(nombre)

    def _add_emp(self):
        nombre = (self.txt_emp.text() or "").strip().upper()
        if not nombre:
            return
        db.agregar_empleado(nombre)
        self._bitacora("AGREGÓ EMPLEADO", "empleados", nombre, "Nuevo empleado")
        self.txt_emp.clear()
        self._ref_emp()

    def _del_emp(self):
        item = self.lst_emp.currentItem()
        if item is None:
            return
        nombre = item.text()
        if C.confirmar(self, "Empleados", "¿Eliminar a %s?" % nombre,
                       si="Sí, eliminar"):
            db.eliminar_empleado(nombre)
            self._bitacora("ELIMINÓ EMPLEADO", "empleados", nombre, "Baja de empleado")
            self._ref_emp()

    def _importar_empleados(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccione el Excel con la lista de empleados", "",
            "Excel (*.xlsx *.xlsm);;Todos (*.*)")
        if not ruta:
            return
        try:
            total, agregados = db.importar_empleados_excel(ruta)
        except Exception as ex:
            C.error(self, "Importar empleados", "No se pudo leer el Excel:\n\n%s" % ex)
            return
        self._ref_emp()
        self._bitacora("IMPORTÓ EMPLEADOS", "empleados", ruta.replace("\\", "/").split("/")[-1],
                       "Filas leídas %d · nuevos %d" % (total, agregados))
        C.informar(self, "Importar empleados",
                   "Filas leídas: %d\nEmpleados nuevos: %d" % (total, agregados))

    # --------------------------------------------------------------- clientes
    def _tab_clientes(self):
        panel = _PanelLista(
            boton_agregar="Agregar cliente", al_agregar=self._add_cli,
            al_eliminar=self._del_cli, al_importar=self._importar_clientes,
            ayuda="Clientes / proyectos que se eligen al crear un viático. "
                  "Puede importar la lista desde un Excel.")
        self.pestanas.addTab(panel, "🧑‍💼 Clientes")
        self.lst_cli = panel.lista
        self.txt_cli = panel.entrada
        self._ref_cli()

    def _ref_cli(self):
        self.lst_cli.clear()
        for nombre in db.listar_clientes():
            self.lst_cli.addItem(nombre)

    def _add_cli(self):
        nombre = (self.txt_cli.text() or "").strip().upper()
        if not nombre:
            return
        db.agregar_cliente(nombre)
        self._bitacora("AGREGÓ CLIENTE", "clientes", nombre, "Nuevo cliente/proyecto")
        self.txt_cli.clear()
        self._ref_cli()

    def _del_cli(self):
        item = self.lst_cli.currentItem()
        if item is None:
            return
        nombre = item.text()
        if C.confirmar(self, "Clientes", "¿Eliminar a %s?" % nombre, si="Sí, eliminar"):
            db.eliminar_cliente(nombre)
            self._bitacora("ELIMINÓ CLIENTE", "clientes", nombre, "Baja de cliente")
            self._ref_cli()

    def _importar_clientes(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccione el Excel con la lista de clientes", "",
            "Excel (*.xlsx *.xlsm);;Todos (*.*)")
        if not ruta:
            return
        try:
            total, agregados = db.importar_clientes_excel(ruta)
        except Exception as ex:
            C.error(self, "Importar clientes", "No se pudo leer el Excel:\n\n%s" % ex)
            return
        self._ref_cli()
        self._bitacora("IMPORTÓ CLIENTES", "clientes", ruta.replace("\\", "/").split("/")[-1],
                       "Filas leídas %d · nuevos %d" % (total, agregados))
        C.informar(self, "Importar clientes",
                   "Filas leídas: %d\nClientes nuevos: %d" % (total, agregados))

    # -------------------------------------------------------------- vehículos
    def _tab_vehiculos(self):
        panel = QWidget()
        lay = C.margenes(QVBoxLayout(panel), 14, 14, 14, 14, 8)
        self.lst_veh = QListWidget()
        self.lst_veh.setAlternatingRowColors(True)
        lay.addWidget(self.lst_veh, 1)
        barra = C.margenes(QHBoxLayout(), esp=6)
        self.txt_placa = C.campo("", ancho=120, mayusculas=True, placeholder="Placa")
        self.cb_tipo = C.combo(TIPOS_VEHICULO_UI, TIPOS_VEHICULO_UI[0], ancho=150)
        self.txt_chofer = C.campo("", ancho=240, mayusculas=True, placeholder="Chofer")
        barra.addWidget(self.txt_placa)
        barra.addWidget(self.cb_tipo)
        barra.addWidget(self.txt_chofer)
        barra.addWidget(C.boton_primario("Agregar / actualizar", self._add_veh))
        barra.addWidget(C.boton_peligro("Eliminar", self._del_veh))
        barra.addStretch(1)
        lay.addLayout(barra)
        self.pestanas.addTab(panel, "🚗 Vehículos")
        self._ref_veh()

    def _ref_veh(self):
        self.lst_veh.clear()
        for v in db.listar_vehiculos():
            self.lst_veh.addItem("%s  |  %s  |  %s" % (v["placa"], v["tipo"], v["chofer"]))

    def _add_veh(self):
        placa = (self.txt_placa.text() or "").strip().upper()
        if not placa:
            return
        chofer = (self.txt_chofer.text() or "").strip().upper()
        db.agregar_vehiculo(placa, self.cb_tipo.currentText(), chofer)
        self._bitacora("AGREGÓ VEHÍCULO", "vehículos", placa,
                       "%s · chofer %s" % (self.cb_tipo.currentText(), chofer or "-"))
        self.txt_placa.clear()
        self.txt_chofer.clear()
        self._ref_veh()

    def _del_veh(self):
        item = self.lst_veh.currentItem()
        if item is None:
            return
        placa = item.text().split()[0]
        if C.confirmar(self, "Vehículos", "¿Eliminar %s?" % placa, si="Sí, eliminar"):
            db.eliminar_vehiculo(placa)
            self._bitacora("ELIMINÓ VEHÍCULO", "vehículos", placa, "Baja de vehículo")
            self._ref_veh()

    # ------------------------------------------------ provincias / rutas / km
    def _tab_rutas(self):
        panel = QWidget()
        lay = C.margenes(QVBoxLayout(panel), 14, 14, 14, 14, 8)

        form = C.Tarjeta("Actualizar kilómetros desde Cuenca",
                         "Elija la provincia y el cantón (o escríbalos), ponga los km y "
                         "guarde. Con «📥 Importar Excel» se carga de una sola vez toda "
                         "la tabla del Excel de tiempos de viaje que va con el sistema "
                         "(«TIEMPOS DE VIAJE MIEMPRESA (NUEVO).xlsx», en la carpeta "
                         "excel\\ del programa): cantón, km y horas de viaje; queda "
                         "guardada en la base de datos, así que la ven todas las "
                         "computadoras.\n"
                         "Las horas de viaje se pueden dejar vacías: en ese caso el sistema "
                         "estima el tiempo con los km y la velocidad del vehículo, y le suma "
                         "una hora por cada comida que cae dentro del viaje (desayuno, "
                         "almuerzo y merienda).")
        fila1 = C.margenes(QHBoxLayout(), esp=8)
        self.cb_prov_ruta = C.combo_auto(db.listar_provincias, ancho=230)
        self.cb_canton_ruta = C.combo_auto(self._cantones_ruta, ancho=250)
        self.txt_km_ruta = C.campo("", ancho=100, placeholder="Km")
        self.txt_horas_ruta = C.campo("", ancho=100, placeholder="Horas: 5:40")
        fila1.addWidget(C.etiqueta("Provincia:", clave=True))
        fila1.addWidget(self.cb_prov_ruta)
        fila1.addWidget(C.etiqueta("Cantón / ciudad:", clave=True))
        fila1.addWidget(self.cb_canton_ruta)
        fila1.addWidget(C.etiqueta("Km aprox.:", clave=True))
        fila1.addWidget(self.txt_km_ruta)
        fila1.addWidget(C.etiqueta("Horas de viaje (ida):", clave=True))
        fila1.addWidget(self.txt_horas_ruta)
        fila1.addWidget(C.boton_primario("💾  Guardar km y horas", self._guardar_ruta))
        fila1.addWidget(C.boton_amarillo("📥  Importar Excel", self._importar_distancias))
        fila1.addStretch(1)
        form.agregar_fila(fila1)
        self.cb_prov_ruta.currentTextChanged.connect(lambda _t: self._cargar_cantones_ruta())
        self.cb_canton_ruta.currentTextChanged.connect(lambda _t: self._km_ruta_seleccionado())
        lay.addWidget(form)

        lista = C.Tarjeta("Distancias registradas",
                          "Haga clic en una distancia para llevarla al formulario")
        self.lst_rutas = QListWidget()
        self.lst_rutas.setAlternatingRowColors(True)
        self.lst_rutas.currentRowChanged.connect(lambda _i: self._ruta_a_formulario())
        lista.agregar(self.lst_rutas, 1)
        lay.addWidget(lista, 1)

        self.pestanas.addTab(panel, "🗺️ Provincias y km")
        self._ref_rutas()

    def _cantones_ruta(self):
        """Cantones de la provincia elegida (para la lista desplegable)."""
        return db.listar_cantones((self.cb_prov_ruta.valor() or "").strip().upper())

    def _cargar_cantones_ruta(self):
        cantones = self._cantones_ruta()
        self.cb_canton_ruta.refrescar_opciones()
        if (self.cb_canton_ruta.valor() or "").strip().upper() not in cantones:
            self.cb_canton_ruta.set_valor("")
            self.txt_km_ruta.clear()

    def _km_ruta_seleccionado(self):
        """Pone los km y las horas de viaje que ya tiene registrados el cantón."""
        canton = (self.cb_canton_ruta.valor() or "").strip().upper()
        km = db.km_para(canton)
        self.txt_km_ruta.setText("" if km is None else str(int(km)))
        horas = db.horas_para(canton)
        self.txt_horas_ruta.setText(horas_texto(horas, sufijo=False))

    def _guardar_ruta(self):
        canton = (self.cb_canton_ruta.valor() or "").strip().upper()
        if not canton:
            C.aviso(self, "Rutas", "Seleccione o escriba el cantón/ciudad.")
            return
        try:
            km = float((self.txt_km_ruta.text() or "").strip())
            if km < 0:
                raise ValueError
        except ValueError:
            C.error(self, "Rutas", "Ingrese un valor válido de kilómetros.")
            return
        horas = None
        escrito = (self.txt_horas_ruta.text() or "").strip()
        if escrito:
            horas = horas_de_texto(escrito)
            if horas is None or horas <= 0:
                C.error(self, "Rutas", "Las horas de viaje tienen que ser mayores que 0.\n"
                                       "Escriba el tiempo como se lee (por ejemplo 5:40) o "
                                       "en horas (5.67).")
                return
        db.set_distancia(canton, km, horas)
        # Si el cantón se escribió a mano y todavía no estaba en el catálogo, se agrega a la
        # provincia elegida: así queda en la lista desplegable del formulario de viáticos y
        # no hay que volver a escribirlo cada vez (es lo que pasó con YANTZAZA).
        provincia = (self.cb_prov_ruta.valor() or "").strip().upper()
        agregado = db.asegurar_canton(provincia, canton)
        self._bitacora("CAMBIÓ DISTANCIA", "rutas", canton,
                       "%g km desde Cuenca%s"
                       % (km, " · %s de viaje" % horas_texto(horas) if horas else ""))
        if agregado:
            self._bitacora("AGREGÓ CANTÓN", "rutas", canton,
                           "Se agregó %s a la provincia %s (lista del formulario)"
                           % (canton, provincia))
        self.cb_prov_ruta.refrescar_opciones()
        self._cargar_cantones_ruta()
        self._ref_rutas()
        C.informar(self, "Rutas", "Guardado: %s = %g km%s%s"
                   % (canton, km,
                      " · %s de viaje (ida)" % horas_texto(horas) if horas else "",
                      "\n\nEl cantón no estaba en la lista del sistema: se agregó a %s, "
                      "así que ya aparece en el formulario de viáticos." % provincia
                      if agregado else ""))

    def _importar_distancias(self):
        """Importa los km y las horas de viaje desde el Excel de tiempos de viaje."""
        ruta, _filtro = QFileDialog.getOpenFileName(
            self, "Seleccione el Excel con los tiempos de viaje", "",
            "Excel (*.xlsx *.xlsm);;Todos (*.*)")
        if not ruta:
            return
        try:
            total, guardadas = db.importar_distancias_excel(ruta)
        except Exception as ex:
            C.error(self, "Importar tiempos de viaje",
                    "No se pudo leer el Excel:\n\n%s" % ex)
            return
        self._ref_rutas()
        self._bitacora("IMPORTÓ TIEMPOS DE VIAJE", "rutas",
                       ruta.replace("\\", "/").split("/")[-1],
                       "Filas leídas %d · cantones actualizados %d" % (total, guardadas))
        C.informar(self, "Importar tiempos de viaje",
                   "Filas leídas: %d\nCantones actualizados: %d\n\n"
                   "Los tiempos quedan guardados en la base de datos, así que los ven\n"
                   "todas las computadoras." % (total, guardadas))

    def _ref_rutas(self):
        self.lst_rutas.clear()
        for r in db.listar_distancias():
            texto = "%-35s %8.1f km" % (r["canton"], r["km"])
            de_viaje = horas_texto(r.get("horas"))
            if de_viaje:
                texto += "  %13s" % de_viaje        # «5 h 40 min», nunca 5.67
            self.lst_rutas.addItem(texto)

    def _ruta_a_formulario(self):
        """Lleva al formulario la distancia que se eligió en la lista.

        El cantón son los primeros 35 caracteres de la línea y los km y las horas se
        vuelven a leer de la base: así la lista puede mostrar las horas como se leen
        —«5 h 40 min»— sin que se pierda el valor que está guardado.
        """
        item = self.lst_rutas.currentItem()
        if item is None:
            return
        self.cb_canton_ruta.set_valor(item.text()[:35].strip())
        self._km_ruta_seleccionado()

    # -------------------------------------------------- utilidad para el menú
    def actualizar(self):
        """Vuelve a leer todos los catálogos (por si cambiaron desde otra PC)."""
        self._ref_emp()
        self._ref_cli()
        self._ref_veh()
        self._ref_rutas()

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
