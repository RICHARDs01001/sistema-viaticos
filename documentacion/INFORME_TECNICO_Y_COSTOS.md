<!--
  Sistema de Viáticos Miempresa
  Autor:    Richard Esteban Salazar Guillén
  Contacto: richards0101789@gmail.com  ·  +593 981239086
  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
-->

# Informe técnico y de costos — Sistema de Viáticos MIEMPRESA

> **Nota importante sobre los valores:** los montos son **estimaciones** hechas con
> tarifas típicas de mercado (Ecuador y remoto internacional) para comparar
> escenarios. No son cotizaciones ni valores garantizados: dependen del país, la
> experiencia, la urgencia y si se contrata por horas o por proyecto cerrado.

---

## 1. Qué es el sistema (alcance real desarrollado)

Aplicación de escritorio (Python + Tkinter + SQLite/PostgreSQL) para manejar todo el
ciclo del viático, replicando el manejo manual en Excel de la empresa:

| Módulo | Qué resuelve |
| --- | --- |
| Generación de viáticos | encargado, chofer, pasajeros, km desde Cuenca, combustible sugerido, peajes, recibos |
| Cálculo automático | desayuno/almuerzo/merienda por horas, hospedaje por noche, agua, taxis, combustible por km o efectivo, redondeo de cajero |
| Ajustes de viático | días adicionales, combustible extra, peaje y otros; varios ajustes por viático |
| Justificación | gastos por concepto, facturas adjuntas, explicación cuando el valor respaldado difiere de la factura, devolución/compensación, cierre |
| Facturas | carga de PDF/imágenes (convierte a PDF), unión automática en **un solo PDF por viático** |
| Informes | PDF/HTML con el formato del Excel: original, ajuste y general |
| Usuarios y seguridad | login, roles (vendedoras / justificación / superusuario oculto), bitácora de **toda** la actividad, alta/baja de usuarios |
| Respaldos y auditoría | ventana de respaldos, informe de actividad exportable a Excel/CSV |
| Base central | PostgreSQL en el servidor para 5 máquinas + migración de datos + pantalla de conexión |
| Numeración | automática por año (1, 2, 3… cada año) con arranque configurable por el superusuario |
| Empaquetado | `.exe` de un solo archivo con todas las dependencias |

**Tamaño del código entregado:** ~6.700 líneas en 18 módulos, más guías de uso,
empaquetado y respaldos automáticos de la base.

---

## 2. Estimación de horas (si se hiciera de nuevo, profesionalmente)

| # | Fase | Horas (mín–máx) |
| --- | --- | --- |
| 1 | Levantamiento de las reglas del Excel y diseño del modelo | 24 – 32 |
| 2 | Base de datos, capa de datos y migraciones | 36 – 48 |
| 3 | Motor de cálculo del viático (comidas, hospedaje, km, redondeo) | 16 – 20 |
| 4 | Generación / edición / ajustes / historial (pantalla grande) | 56 – 70 |
| 5 | Justificación completa (gastos, facturas, cierre) | 48 – 60 |
| 6 | Reportes PDF/HTML con el formato exacto del Excel | 28 – 36 |
| 7 | Usuarios, roles, superusuario, auditoría | 28 – 36 |
| 8 | Respaldos de archivos (adjuntos, conversión y unión de PDF) | 18 – 24 |
| 9 | Base central PostgreSQL + el servidor + migración + pantalla de conexión | 36 – 48 |
| 10 | Numeración por año y ajustes finos de negocio | 10 – 14 |
| 11 | Empaquetado `.exe`, pruebas en varias máquinas, instalación | 18 – 24 |
| 12 | Pruebas funcionales, corrección de errores y documentación | 36 – 48 |
| | **Total** | **354 – 460 h** |

Complejidad: **media-alta**. Lo que la sube de nivel no es la interfaz sino las
**reglas de negocio** (horas límite, ajustes por días adicionales, devolución vs
compensación, formato exacto del informe de la justificación, consolidación de
facturas) y la parte **multi-usuario con base central** (concurrencia, migración,
auditoría).

Reparto aproximado: 40 % lógica de negocio y datos · 35 % interfaz · 15 % informes
y archivos · 10 % pruebas y empaquetado.

---

## 3. Cuánto costaría en el mercado (estimado)

| Escenario | Tarifa típica por hora | Total por 354–460 h |
| --- | --- | --- |
| Practicante / junior (como tú) | USD 5 – 8 | **USD 1.800 – 3.700** |
| Freelance semi-senior (Ecuador) | USD 15 – 25 | **USD 5.300 – 11.500** |
| Casa de software / microempresa (Ecuador–LatAm) | USD 25 – 40 | **USD 8.900 – 18.400** |
| Freelance remoto internacional (LatAm para EE.UU.) | USD 40 – 70 | **USD 14.200 – 32.200** |
| Consultora / proyecto cerrado con soporte | — | **USD 18.000 – 45.000** |

Si se cotizara **por proyecto** con margen de riesgo, garantía y soporte, el rango
razonable para una empresa es **USD 12.000 – 25.000**.

---

## 4. Comparación con alternativas del mercado

| Opción | Costo aproximado | Ventajas | Limitaciones para Miempresa |
| --- | --- | --- | --- |
| **Este sistema (hecho a medida)** | 1 vez (rango de arriba) + mantenimiento | Reglas exactas del Excel, ajustes de viático, informe con el formato propio, sin licencias, datos propios | Hay que mantenerlo |
| SaaS tipo Concur / Expensify / Zoho Expense | USD 5 – 15 por usuario/mes → 5–10 usuarios = **USD 300 – 1.800 al año** (USD 900 – 5.400 a 3 años) | Nube, app móvil, actualizaciones incluidas | No replica las reglas ni el formato; se paga siempre; los datos quedan fuera |
| Facturación/ERP local (Odoo u otros) | Implementación **USD 3.000 – 12.000** + módulos | Varias áreas en un solo sistema | Los viáticos hay que adaptarlos igual (consultoría aparte) |
| Seguir en Excel manual | “Gratis” | Ninguno nuevo | Errores de cálculo, sin control de quién cambió qué, sin respaldo ordenado de facturas |

**Costo recurrente del sistema en producción**

| Concepto | Estimado |
| --- | --- |
| Servidor (PC existente o VPS) | USD 0 (PC de la empresa) a USD 15 – 30/mes (VPS) |
| Respaldos (`.sql` diario + copia externa) | incluido (script `respaldar_base_nativo.bat`) |
| Mantenimiento (ajustes, soporte, actualizaciones) | 2 – 6 h/mes → USD 40 – 150/mes según tarifa |

---

## 5. Cuánto ahorras programándolo tú

- Si la empresa hubiera contratado esto afuera: **USD 5.300 – 18.400** (Ecuador) o
  **USD 14.200 – 32.200** (internacional), más soporte mensual.
- Con tu trabajo: **el ahorro directo estimado es de USD 5.000 – 18.000**, y el
  sistema queda con las reglas exactas de la casa, sin cuotas ni licencias.
- Valor adicional para ti: es un proyecto de portafolio completo (escritorio, base
  de datos central con el servidor, auditoría, informes PDF, empaquetado `.exe`,
  migración de datos). En el mercado es de nivel **semi-senior**: sirve como carta
  de presentación o para negociar un bono/contrato al terminar la práctica.

---

## 6. Lo que falta para producción (recomendado)

| Pendiente | Horas estimadas |
| --- | --- |
| Montaje final en el servidor y pruebas con las 5 máquinas | 6 – 10 |
| Capacitación a las 4 vendedoras y a Paola (1 hora por grupo) | 4 – 6 |
| Respaldo automático programado + prueba de restauración | 2 – 4 |
| Limpieza de los viáticos de prueba y arranque de la numeración real | 1 – 2 |
| **Total pendiente** | **13 – 22 h** |

Con eso el sistema queda operativo para el día a día de la empresa.
