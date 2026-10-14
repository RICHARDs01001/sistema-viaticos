# =====================================================================
#  Sistema de Viáticos Miempresa
#  Autor:    Richard Esteban Salazar Guillén
#  Contacto: richards0101789@gmail.com  ·  +593 981239086
#  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
#  Prohibida su copia, reproducción o distribución sin autorización escrita.
# =====================================================================
"""autor.py — Datos del autor y sello de autoría dentro del programa.

Estos datos quedan **compilados dentro del .exe** (son constantes de Python, no
comentarios) y se muestran en el autodiagnóstico. También se pueden estampar en la
bitácora con `sellar_bitacora(...)`, que deja constancia fechada de que el programa
en uso es el original del autor.

La firma completa está además en la cabecera y el pie de cada archivo de código y en
los metadatos del ejecutable (Propiedades → Detalles).

Autor: Richard Esteban Salazar Guillén · richards0101789@gmail.com · +593 981239086
"""
AUTOR = "Richard Esteban Salazar Guillén"
CORREO = "richards0101789@gmail.com"
CELULAR = "+593 981239086"
PROGRAMA = "Sistema de Viáticos Miempresa"
ANIO = "2026"
COPYRIGHT = "(c) %s %s — Todos los derechos reservados." % (ANIO, AUTOR)
MARCA = "%s · %s · %s" % (AUTOR, CORREO, CELULAR)


def creditos():
    """Una línea con la autoría (para el autodiagnóstico y los documentos)."""
    return "%s · %s · %s · %s" % (PROGRAMA, AUTOR, CORREO, CELULAR)


def firmado(objeto=None):
    """True si el crédito del autor sigue presente (en este módulo o en `objeto`)."""
    texto = ""
    if objeto is not None:
        texto = str(getattr(objeto, "__doc__", "") or "")
    return AUTOR in (MARCA + texto) or MARCA in texto


def sellar_bitacora(usuario=None, detalle=None):
    """Estampa la autoría en la bitácora (una sola vez por sesión).

    Es opcional: se llama cuando se quiere dejar constancia de que el programa en uso
    lleva la firma del autor. Devuelve True si la firma está completa.
    """
    ok = firmado()
    try:
        import database as db
        db.registrar_bitacora(usuario or "SISTEMA",
                              "PROGRAMA CON FIRMA DEL AUTOR" if ok else "AVISO: FIRMA ALTERADA",
                              "autor", PROGRAMA,
                              detalle or MARCA)
    except Exception:
        pass
    return ok


# ---------------------------------------------------------------------
#  © 2026 Richard Esteban Salazar Guillén
#  richards0101789@gmail.com  ·  +593 981239086  ·  Sistema de Viáticos Miempresa
# ---------------------------------------------------------------------
