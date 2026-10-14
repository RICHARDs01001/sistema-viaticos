# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""pruebas_qt.py — Prueba rápida de la interfaz nueva, SIN abrir ventanas.

Se ejecuta así (no necesita Postgres ni tocar los datos reales):

    python pruebas_qt.py

Revisa el tema, los componentes (tablas, tarjetas, campos de fecha/hora, listas con
autocompletado), las ventanas del ingreso y del menú principal, las **claves
cifradas** y el **ingreso por área** (cada ventana pide su clave y su rol). Sirve
para saber si la interfaz nueva está completa en esta máquina.

La prueba trabaja con una base SQLite dentro de una carpeta temporal: se crea al
empezar y se borra al terminar, así no toca los datos de trabajo.
"""
import os
import shutil
import sys
import tempfile
from datetime import datetime

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")   # sin pantalla
# Base de prueba aislada: local (SQLite), en una carpeta temporal desechable.
_TEMP = tempfile.mkdtemp(prefix="viaticos_pruebas_")
os.environ["VIATICOS_MOTOR"] = "sqlite"
os.environ["VIATICOS_DATA"] = _TEMP
os.environ["VIATICOS_RESPALDOS"] = "carpeta"

_resultados = []


def revisar(nombre, condicion, detalle=""):
    ok = bool(condicion)
    _resultados.append(ok)
    print(("OK    " if ok else "FALLA ") + nombre
          + (("  ->  %s" % (detalle,)) if detalle != "" else ""))
    return ok


def main():
    import database as db
    import q_login
    import q_menu
    import qt_comunes as C
    import qt_tema as T

    app = q_login.crear_app()
    revisar("El tema se aplica (hoja de estilo)", len(app.styleSheet()) > 5000,
            "%d caracteres" % len(app.styleSheet()))
    revisar("Escala de la interfaz (config.json)", T.factor() > 0, T.factor())
    revisar("Colores de insignia por estado", T.color_estado("JUSTIFICADO")[0] == T.VERDE,
            T.color_estado("justificado"))
    revisar("Formato de moneda y fecha", T.formato_moneda(12.5) == "$12.50"
            and T.formato_fecha("2026-09-23") == "23/09/2026",
            "%s / %s" % (T.formato_moneda(12.5), T.formato_fecha("2026-09-23")))

    # Los avisos y confirmaciones son ventanas modales: en una prueba automática se
    # reemplazan por nada (si no, la prueba se quedaría esperando un clic).
    C.informar = lambda *a, **k: None
    C.aviso = lambda *a, **k: None
    C.error = lambda *a, **k: None
    C.confirmar = lambda *a, **k: True

    # --- tabla con datos de prueba ---
    tabla = C.TablaDatos([("n", "N°", 70), ("persona", "PERSONA", 200),
                          ("total", "TOTAL", 90)],
                         titulo="Prueba", nombre="prueba")
    tabla.set_datos([{"n": "001", "persona": "ANA", "total": 10.0},
                     {"n": "002", "persona": "LUIS", "total": 5.5}])
    revisar("Tabla: contador «n de n» al cargar",
            tabla.lbl_contador.text() == "2 de 2", tabla.lbl_contador.text())
    tabla.buscar("ana")
    revisar("Tabla: buscar en todo filtra", tabla.lbl_contador.text() == "1 de 2",
            tabla.lbl_contador.text())
    tabla.limpiar_filtros()
    revisar("Tabla: limpiar filtros vuelve a mostrar todo",
            tabla.lbl_contador.text() == "2 de 2", tabla.lbl_contador.text())
    tabla.tabla.selectRow(1)
    revisar("Tabla: selección devuelve el registro completo",
            (tabla.seleccion() or {}).get("persona") == "LUIS", tabla.seleccion())
    revisar("Tabla: la celda numérica ordena por valor",
            C.Item("9.0", 9.0) < C.Item("10.0", 10.0))

    # --- campos ---
    revisar("CampoFecha: valor vacío y valor puesto",
            C.CampoFecha().valor() == "" and C.CampoFecha("2026-09-23").valor() == "2026-09-23")
    revisar("CampoHora: tolera «930», «9:30» y vacío",
            C.CampoHora("930").valor() == "09:30" and C.CampoHora("9:30").valor() == "09:30"
            and C.CampoHora("").valor() == "")
    auto = C.combo_auto(lambda: ["CUENCA", "GIRÓN"])
    revisar("ComboAuto: lee las opciones de la función", auto.opciones() == ["CUENCA", "GIRÓN"],
            auto.opciones())
    revisar("Insignia: color según estado",
            "background" in C.Insignia().set_estado("ANULADO").styleSheet())
    tarjeta = C.Tarjeta("Título", "Subtítulo")
    franja = C.Aviso("Aviso", "Texto del aviso")
    kpi = C.Kpi("Rótulo", "1", "nota")
    revisar("Tarjeta / Aviso / Kpi se construyen",
            tarjeta.lbl_titulo.text() == "Título" and franja.lbl_texto.text() == "Texto del aviso"
            and kpi.lbl_valor.text() == "1" and kpi.lbl_rotulo.text() == "Rótulo",
            "%s · %s · %s" % (tarjeta.lbl_titulo.text(), franja.lbl_titulo.text(),
                              kpi.lbl_valor.text()))

    # --- claves de los usuarios: siempre cifradas (sha256 + sal) ---
    cifrada = db.cifrar_clave("1234")
    revisar("Claves: se guardan cifradas con sha256 + sal",
            db.es_clave_cifrada(cifrada) and cifrada.startswith("sha256$"),
            cifrada[:26] + "…")
    revisar("Claves: la cifrada valida la clave buena y rechaza la mala",
            db.clave_correcta(cifrada, "1234") and not db.clave_correcta(cifrada, "12345"))
    revisar("Claves: una clave vieja guardada en texto se sigue aceptando",
            db.clave_correcta("1234", "1234") and not db.clave_correcta("1234", "0000"))
    revisar("Claves: la misma clave da cifrados distintos (sal al azar)",
            db.cifrar_clave("1234") != db.cifrar_clave("1234"))

    # --- base de prueba (local y temporal) ---
    try:
        db.init_db()
        listo = "listo"
    except Exception as ex:
        listo = "FALLA: %s" % ex
    revisar("Base local de prueba creada en una carpeta temporal", "FALLA" not in listo, listo)
    if "FALLA" not in listo:
        usuarios = db.listar_usuarios()
        revisar("Usuarios: la lista no muestra ninguna clave",
                bool(usuarios) and all(not u.get("clave") for u in usuarios)
                and all(u.get("tiene_clave") for u in usuarios),
                "%d usuarios" % len(usuarios))
        conn = db.conectar()
        claves = [r["clave"] for r in conn.execute("SELECT clave FROM usuarios")]
        conn.close()
        revisar("Usuarios: en la base no queda ninguna clave legible",
                all(db.es_clave_cifrada(c) for c in claves), "%d claves" % len(claves))
        revisar("Ingreso: la clave de fábrica de una vendedora funciona",
                (db.login("VENDEDOR1", "1234") or {}).get("rol") == db.ROL_VENDEDOR)
        revisar("Ingreso: la clave del superusuario funciona y la errada no",
                (db.login("MIEMPRESA", "miempresa") or {}).get("rol") == db.ROL_SUPER
                and db.login("MIEMPRESA", "clave-mala") is None)

        # --- horas de viaje: el recorrido + las comidas que caen en el camino ---
        import q_admin
        import q_viaje
        parametros = db.cargar_parametros()
        revisar("Parámetros: la merienda del camino tiene sus horas (parámetro nuevo)",
                float(parametros.get("horas_merienda_viaje") or 0) == 1.0,
                parametros.get("horas_merienda_viaje"))
        revisar("Parámetros: la fila de la merienda del camino está en la pantalla",
                any(clave == "horas_merienda_viaje" for clave, _e, _t in q_admin.PARAMS_UI))
        p = dict(parametros)
        p.update({"hora_limite_desayuno": "06:00", "hora_limite_almuerzo": "13:00",
                  "hora_limite_merienda": "21:00", "horas_desayuno_viaje": 1.0,
                  "horas_almuerzo_viaje": 1.0, "horas_merienda_viaje": 1.0})
        horas = {texto: datetime(2026, 9, 24, *[int(x) for x in texto.split(":")])
                 for texto in ("02:00", "10:00", "18:00")}
        # 10:00 + 3 h de recorrido = 13:00 → 14:00 por el almuerzo
        revisar("Viaje: sale 10:00 y llega 13:00 -> 14:00 (una hora por el almuerzo)",
                q_viaje.duracion_de_viaje(0, 0, p, horas["10:00"], 3) == 4)
        # 18:00 + 4 h = 22:00 → 23:00 por la merienda del camino
        revisar("Viaje: el que vuelve a las 22:00 llega a las 23:00 (la merienda)",
                q_viaje.duracion_de_viaje(0, 0, p, horas["18:00"], 4) == 5)
        # 02:00 + 12 h = 14:00 → 16:00 por el desayuno y el almuerzo
        revisar("Viaje: el viaje largo de madrugada suma desayuno y almuerzo",
                q_viaje.duracion_de_viaje(0, 0, p, horas["02:00"], 12) == 14)

        # --- catálogo de cantones: los cantones que entraron después (YANTZAZA) ---
        revisar("Rutas: YANTZAZA está en el catálogo (la lista del formulario)",
                "YANTZAZA" in db.listar_cantones("ZAMORA CHINCHIPE"),
                db.listar_cantones("ZAMORA CHINCHIPE"))
        revisar("Rutas: YANTZAZA queda con los km y las horas de la empresa (215 km · 5 h)",
                db.km_para("YANTZAZA") == 215 and db.horas_para("YANTZAZA") == 5.0,
                "%s km · %s h" % (db.km_para("YANTZAZA"), db.horas_para("YANTZAZA")))
        agregado = db.asegurar_canton("AZUAY", "CAMILO PONCE ENRÍQUEZ")
        revisar("Rutas: un cantón escrito a mano entra al catálogo (y no se duplica)",
                agregado and "CAMILO PONCE ENRÍQUEZ" in db.listar_cantones("AZUAY")
                and db.asegurar_canton("AZUAY", "CAMILO PONCE ENRÍQUEZ") is False)
        import bd
        with bd.conectar() as c:
            c.execute("DELETE FROM cantones WHERE nombre='YANTZAZA'")
            c.execute("DELETE FROM seq WHERE nombre='catalogo_cantones_8_4'")
        db.olvidar_cache("provincias", "cantones:")
        with bd.conectar() as c:
            db._reparar_catalogo_cantones(c)
        revisar("Rutas: la reparación del catálogo la vuelve a meter (una sola vez por base)",
                "YANTZAZA" in db.listar_cantones("ZAMORA CHINCHIPE")
                and db.km_para("YANTZAZA") == 215)
        revisar("Catálogos: el Excel de tiempos de viaje que se usa es el de la herramienta",
                str(db._archivo_de_recursos("TIEMPOS DE VIAJE") or "").endswith(
                    "TIEMPOS DE VIAJE MIEMPRESA (NUEVO).xlsx"),
                db._archivo_de_recursos("TIEMPOS DE VIAJE"))

        # --- distancias: la semilla de fábrica y los Excel de la carpeta tienen que decir
        # --- lo mismo que el documento (si no, una base nueva nacería con datos viejos)
        del_documento = db._leer_excel_distancias(db._archivo_de_recursos("TIEMPOS DE VIAJE"))
        desfasados = [c for c, km, horas in del_documento
                      if db.KM_CUENCA.get(c) != km
                      or float(db.HORAS_CUENCA.get(c) or 0) != float(horas or 0)]
        revisar("Rutas: la semilla de fábrica trae los km y las horas del documento",
                del_documento and not desfasados,
                "cantones %d · desfasados %s" % (len(del_documento), desfasados[:6]))
        otro_excel = db._archivo_de_recursos("TIEMPOS DE VIAJE MIEMPRESA.xlsx")
        del_documento = {c: (k, h) for c, k, h in del_documento}
        del_otro = ({c: (k, h) for c, k, h in db._leer_excel_distancias(otro_excel)}
                    if otro_excel else {})
        comunes = sorted(set(del_documento) & set(del_otro))
        choques = [c for c in comunes
                   if abs(del_documento[c][0] - del_otro[c][0]) > 0.5
                   or abs((del_documento[c][1] or 0) - (del_otro[c][1] or 0)) > 0.005]
        revisar("Rutas: los dos Excel de tiempos de viaje de la carpeta dicen lo mismo",
                comunes and not choques,
                "%d cantones en los dos · se contradicen %s" % (len(comunes), choques[:6]))

        # --- memoria temporal: que nadie pierda lo que estaba llenando ---
        revisar("Memoria temporal: lo que se deja a medias se guarda y se vuelve a leer",
                db.guardar_borrador("VENDEDOR1", {"encargado": "PERSONAL DE EJEMPLO UNO",
                                                "km": "215"})
                and ((db.leer_borrador("VENDEDOR1") or {}).get("datos")
                     or {}).get("km") == "215"
                and [b["usuario"] for b in db.usuarios_con_borrador()] == ["VENDEDOR1"],
                db.usuarios_con_borrador())
        revisar("Memoria temporal: al guardar el viático el borrador se borra",
                db.borrar_borrador("VENDEDOR1") == 1 and db.leer_borrador("VENDEDOR1") is None)
        with bd.conectar() as c:
            c.execute("INSERT INTO borradores(usuario, pantalla, datos, actualizado_el) "
                      "VALUES (?,?,?,?)", ("VIEJO", "viatico", "{}", "2026-01-01 08:00:00"))
        db.borrar_borradores_viejos(30)
        revisar("Memoria temporal: los borradores viejos se descartan solos",
                db.leer_borrador("VIEJO") is None)

    # --- ventanas: ingreso ---
    from PySide6.QtWidgets import QLabel, QLineEdit
    login = q_login.LoginWindow()
    revisar("Ingreso: campos listos y clave oculta",
            login.txt_usuario.text() == ""
            and login.txt_clave.echoMode() == QLineEdit.EchoMode.Password,
            login.windowTitle())
    login.close()
    login_area = q_login.LoginWindow(roles=(db.ROL_SUPER,), pedir_recordar=True)
    textos = " ".join(l.text() for l in login_area.findChildren(QLabel))
    revisar("Ingreso por área: limita el rol, ofrece recordar y no dice quién entra",
            login_area.roles == (db.ROL_SUPER,) and login_area.chk_recordar is not None
            and not login_area.chk_recordar.isChecked()
            and "Puede ingresar" not in textos
            and db.ETIQUETA_ROL[db.ROL_SUPER].upper() not in textos.upper(),
            login_area.windowTitle())
    login_area.close()

    # --- menú: se abre sin clave y cada ventana pide la suya ---
    menu = q_menu.MenuPrincipal()
    esperados = {"inicio", "viaje", "ajustes", "respaldos", "admin", "bitacora",
                 "usuarios", "conexion"}
    revisar("Menú: abre sin sesión, con los 7 módulos y el botón Inicio",
            menu.usuario.get("usuario") == "" and set(menu.botones) == esperados,
            sorted(menu.botones))
    revisar("Menú: la base de datos tiene su botón y el atajo Ctrl+Alt+B sigue",
            "conexion" in menu.botones and q_menu.ATAJO_CONEXION == "Ctrl+Alt+B",
            menu.botones["conexion"].toolTip())
    revisar("Menú: el botón de la conexión avisa que es del superusuario",
            "superusuario" in menu.botones["conexion"].toolTip().lower())
    revisar("Menú: la barra avisa que cada ventana pide la clave",
            "cada ventana" in menu._texto_rol() and menu.es_super is False,
            menu._texto_sesion())
    grupos = q_menu.grupos_de_modulos()
    revisar("Menú: los parámetros y catálogos van con el trabajo del día",
            [m[0] for m in grupos[0][2]] == ["viaje", "ajustes", "respaldos", "admin"]
            and [m[0] for m in grupos[1][2]] == ["bitacora", "usuarios", "conexion"],
            [m[0] for _t, _a, ms in grupos for m in ms])
    revisar("Menú: el botón de Parámetros avisa que el cambio queda para todas las PC",
            "demás computadoras" in menu.botones["admin"].toolTip())
    revisar("Permisos: justificar viáticos ya no es para las vendedoras",
            db.ROL_VENDEDOR not in q_menu.PERMISOS_MODULO["ajustes"]
            and db.ROL_JUSTIFICA in q_menu.PERMISOS_MODULO["ajustes"])
    revisar("Permisos: auditoría, usuarios y conexión solo del superusuario",
            all(q_menu.PERMISOS_MODULO[k] == (db.ROL_SUPER,)
                for k in ("bitacora", "usuarios", "conexion")))
    revisar("Permisos: los parámetros y catálogos los abre cualquier usuario",
            q_menu.PERMISOS_MODULO["admin"] == (db.ROL_VENDEDOR, db.ROL_JUSTIFICA,
                                                db.ROL_SUPER))
    revisar("Permisos: viáticos y respaldos para todos los roles",
            all(q_menu.PERMISOS_MODULO[k] == (db.ROL_VENDEDOR, db.ROL_JUSTIFICA, db.ROL_SUPER)
                for k in ("viaje", "respaldos")))

    pedidos = []
    original = q_login.pedir_sesion
    try:
        q_login.pedir_sesion = lambda *a, **k: (pedidos.append(k.get("roles")),
                                               ({"usuario": "VENDEDOR1",
                                                 "nombre": "PERSONAL DE EJEMPLO UNO",
                                                 "rol": db.ROL_VENDEDOR}, False))[1]
        revisar("Menú: una vendedora abre Parámetros con su propia clave",
                menu.autorizar("admin") is True and pedidos
                and pedidos[-1] == (db.ROL_VENDEDOR, db.ROL_JUSTIFICA, db.ROL_SUPER),
                pedidos[-1] if pedidos else None)
        revisar("Menú: la sesión del área queda puesta en el menú",
                menu.usuario.get("usuario") == "VENDEDOR1" and menu.es_super is False)
        menu.olvidar_sesion()
        revisar("Menú: «olvidar la clave» deja el menú sin sesión",
                menu.usuario.get("usuario") == "" and menu._sesion_guardada is None)
        q_login.pedir_sesion = lambda *a, **k: (None, False)
        revisar("Menú: si se cancela la clave no se abre la ventana",
                menu.autorizar("viaje") is False)
        # Con «no volver a pedir la clave» no se vuelve a preguntar dentro del mismo rol.
        menu2 = q_menu.MenuPrincipal()
        q_login.pedir_sesion = lambda *a, **k: ({"usuario": "VENDEDOR1", "nombre": "PERSONAL DE EJEMPLO UNO",
                                                 "rol": db.ROL_VENDEDOR}, True)
        menu2.autorizar("viaje")
        pedidos2 = []
        q_login.pedir_sesion = lambda *a, **k: (pedidos2.append(1), (None, False))[1]
        revisar("Menú: con «no volver a pedir la clave» no pregunta otra vez",
                menu2.autorizar("respaldos") is True and not pedidos2)
        revisar("Menú: pero a las áreas del superusuario les sigue pidiendo la clave",
                menu2.autorizar("bitacora") is False
                and menu2.autorizar("conexion") is False)
        menu2.close()
    finally:
        q_login.pedir_sesion = original
    menu.close()

    # --- memoria temporal: la ventana de viáticos guarda y devuelve lo que se escribió ---
    # (Es lo que pasa cuando alguien cierra el sistema por error a mitad de la captura.)
    import q_viaje
    vendedora = {"usuario": "VENDEDOR1", "nombre": "PERSONAL DE EJEMPLO UNO",
                 "rol": db.ROL_VENDEDOR}
    empleados = db.listar_empleados()
    ventana = q_viaje.ViajeWindow(None, vendedora)
    ventana.cb_encargado.set_valor(empleados[0])
    ventana.txt_km.setText("215")
    ventana.pasajeros = [{"nombre": empleados[1], "medio": "AUTO", "extra": 0.0}]
    ventana._refrescar_pas()
    guardado = ventana._guardar_borrador()
    datos = (db.leer_borrador(vendedora) or {}).get("datos") or {}
    revisar("Memoria temporal: la ventana guarda sola lo escrito (encargado, km y acompañantes)",
            guardado and datos.get("km") == "215" and len(datos.get("pasajeros") or []) == 1,
            "%s · %s km" % (datos.get("encargado"), datos.get("km")))
    ventana.close()                       # se cierra la ventana con la captura a medias
    otra = q_viaje.ViajeWindow(None, vendedora)
    revisar("Memoria temporal: al volver a entrar con el mismo usuario se recupera igual",
            otra._recuperar_borrador() and otra.txt_km.text() == "215"
            and (otra.cb_encargado.valor() or "") == empleados[0]
            and len(otra.pasajeros) == 1,
            "%s · %s km · %d acompañante(s)"
            % (otra.cb_encargado.valor(), otra.txt_km.text(), len(otra.pasajeros)))
    revisar("Memoria temporal: solo el dueño la recupera (otro usuario no ve nada)",
            db.leer_borrador({"usuario": "VENDEDOR4"}) is None)
    otra.limpiar()
    revisar("Memoria temporal: al limpiar el formulario el borrador se borra",
            db.leer_borrador(vendedora) is None)
    otra.close()

    # --- módulos que todavía no están migrados ---
    faltan = []
    for clave, (archivo, clase) in q_menu.ARCHIVOS_MODULO.items():
        try:
            modulo = __import__(archivo)
            if not hasattr(modulo, clase):
                faltan.append("%s sin %s" % (archivo, clase))
        except Exception as ex:
            faltan.append("%s (%s)" % (archivo, type(ex).__name__))
    print("\nMódulos pendientes de migrar: %s" % (", ".join(faltan) if faltan else "ninguno"))

    # La prueba no deja rastro: se borra la base temporal que se creó al empezar.
    shutil.rmtree(_TEMP, ignore_errors=True)

    total, bien = len(_resultados), sum(1 for r in _resultados if r)
    print("\n%d de %d comprobaciones correctas." % (bien, total))
    print("(La base de prueba se creó y se borró en %s: los datos de trabajo no se tocaron.)"
          % _TEMP)
    return 0 if bien == total else 1


if __name__ == "__main__":
    sys.exit(main())

# ---------------------------------------------------------------------
#  (c) 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
