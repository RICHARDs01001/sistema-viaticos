<!--
  Sistema de Viáticos Miempresa
  Autor:    Richard Esteban Salazar Guillén
  Contacto: richards0101789@gmail.com  ·  +593 981239086
  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
-->

# Actualización automática desde GitHub

Cómo el sistema se actualiza solo en cada computadora: el autor publica una **versión
nueva** en GitHub y en cada PC se ejecuta un `.bat` que la baja e instala **sin tocar los
datos**.

```text
   Autor (su PC)                         GitHub                     Cada PC de trabajo
┌──────────────────────┐          ┌────────────────────┐          ┌──────────────────────────┐
│ PUBLICAR_VERSION.bat │ ──push──▶│  código + version.txt │◀──baja──│ ACTUALIZAR_DESDE_GITHUB.bat │
│ (sube la versión +1) │          │  (+ .exe adjunto)     │          │ (respalda y copia el código)│
└──────────────────────┘          └────────────────────┘          └──────────────────────────┘
                                                                    data\ y config.json NO se tocan
```

## 1. Archivos que se agregaron

| Archivo | Dónde | Para qué |
| --- | --- | --- |
| `version.txt` | **raíz del repositorio** y también en la carpeta del programa de cada PC | en el repositorio dice cuál es la versión publicada; en cada PC, cuál está instalada (un número entero: `8`, `9`, `10`…) |
| `PUBLICAR_VERSION.bat` | **raíz del repositorio** (lo usa el autor) | sube la versión: la incrementa, hace commit y push |
| `ACTUALIZAR_DESDE_GITHUB.bat` | carpeta del programa, en **cada PC** | cada PC busca e instala la versión nueva |
| `herramientas\actualizar.ps1` | carpeta del programa, en **cada PC** | el trabajo real de la actualización (PowerShell) |
| `Sistema_Viaticos.exe` | **adjunto de la versión publicada** en GitHub (no va en el repositorio) | el ejecutable que se copia en cada PC al actualizar |
| `%APPDATA%\SistemaViaticos\instalacion.txt` | se crea solo, en cada PC | recuerda dónde quedó instalado el programa, para la próxima vez |
| `actualizacion.log` | se crea solo | lo que pasó en cada actualización (con fecha y hora) |
| `respaldos_actualizacion\AAAA-MM-DD_HHMM\` | se crea solo | copia de la versión anterior, por si hay que volver atrás |

## 2. La dirección del repositorio

La dirección está **en un solo lugar**: el parámetro `-Repo` de
`herramientas\actualizar.ps1`:

```powershell
param(
    [string]$Repo = "https://github.com/RICHARDs01001/sistema-viaticos",
    ...
)
```

> Ese es el repositorio real del sistema. Si algún día cambia, cambie **solo esa línea**
> (o pase la dirección por la línea de comandos sin editar nada:
> `ACTUALIZAR_DESDE_GITHUB.bat https://github.com/USUARIO/OTRO-REPOSITORIO`).

El repositorio tiene que ser **público** (o usar un *token* en la URL): el actualizador
lee `version.txt` y el `.zip` del código sin pedir usuario ni clave.

## 3. El repositorio y cómo se arma la versión que se publica

El repositorio es **`https://github.com/RICHARDs01001/sistema-viaticos`** y ya está en
marcha: su copia de trabajo es la carpeta `PARA_GITHUB_LIMPIO` (dentro de su carpeta de
trabajo), que es la que tiene el `.git` y el remoto. Para armar cada versión, en **su**
PC y en este orden:

1. **Probar**: `_revision\correr_pruebas.bat` (cálculo, taxis, reglas, ajustes, ventanas).
2. **Copiar el código y los documentos** a las carpetas de entrega:
   `python _revision\_sync.py`. Deja `PARA_GITHUB` y `PARA_SERVIDOR` completas: el
   código, los manuales, `version.txt`, `ACTUALIZAR_DESDE_GITHUB.bat` y
   `herramientas\actualizar.ps1`.
3. **Hacer la copia limpia**: `python limpiar_para_github.py`. Rehace
   `PARA_GITHUB_LIMPIO` cambiando el nombre de la empresa por `MIEMPRESA` y **conserva
   su `.git`** (borrarlo se llevaría el historial y el remoto).
4. **Publicar**: en `PARA_GITHUB_LIMPIO`, doble clic en `PUBLICAR_VERSION.bat` (§4).

Qué **no** se sube: `data\` (la base y las facturas del cliente), `config.json` (la IP y
la clave del servidor), `*.db`, `dist\`, `respaldos_actualizacion\` y `*.exe`. El
`.gitignore` de la copia limpia ya los deja fuera, y el script no copia `.db` ni `.exe`.
El ejecutable no se pierde: viaja **adjunto a la versión publicada** en GitHub (§4).

Si algún día hubiera que **crear** el repositorio desde cero (una sola vez):

```bat
cd PARA_GITHUB_LIMPIO
git init
git remote add origin https://github.com/USUARIO/REPOSITORIO.git
git add -A
git commit -m "Primera version"
git branch -M main
git push -u origin main
```

El repositorio tiene que tener en la rama `main`: **`version.txt` en la raíz** (es el que
lee `actualizar.ps1` para saber qué versión hay publicada) y el código con `main_qt.py`,
`database.py` y `calculos.py` —puede estar dentro de una subcarpeta, como
`sistema_viaticos_miempresa\`: el actualizador lo busca—, más
`ACTUALIZAR_DESDE_GITHUB.bat` y `herramientas\actualizar.ps1` dentro de esa carpeta del
programa.

## 4. Publicar una versión nueva (el autor)

1. Pruebe el sistema: `_revision\correr_pruebas.bat` (y ábralo un momento para ver que
   arranca).
2. Empaquete el ejecutable: en `sistema_viaticos_miempresa`, `EMPAQUETAR_EXE_SERVIDOR.bat`
   deja `dist\Sistema_Viaticos.exe` (unos 73 MB).
3. Arme la copia limpia (§3, pasos 2 y 3): `python _revision\_sync.py` y
   `python limpiar_para_github.py`.
4. En **`PARA_GITHUB_LIMPIO`** —la raíz del repositorio— doble clic en
   **`PUBLICAR_VERSION.bat`**. Hace todo esto:
   - lee el `version.txt` **de la raíz** y lo sube en 1 (8 → 9); si quiere un número
     exacto: `PUBLICAR_VERSION.bat 12`;
   - `git add -A` y `git commit -m "Version N - fecha hora"`;
   - `git push` a GitHub;
   - busca `dist\Sistema_Viaticos.exe`, muestra **tamaño, fecha y SHA256**, abre la
     carpeta con el `.exe` seleccionado y abre en el navegador la página
     `releases/new?tag=vN`.
5. En esa página: arrastre **`Sistema_Viaticos.exe`** a «Attach binaries…», deje el
   título `vN` y pulse **Publish release** (el ejecutable pesa 73 MB: la subida tarda).
6. Compruebe dos cosas en GitHub: que `version.txt` de la rama `main` diga `N`
   (`https://raw.githubusercontent.com/RICHARDs01001/sistema-viaticos/main/version.txt`)
   y que la última versión publicada (*Releases*) tenga el `.exe` adjunto.

> **El número manda en `version.txt`, no en la versión de GitHub.** El actualizador
> compara el `version.txt` de la rama `main` con el de la PC, y de la **última versión
> publicada** (*Releases → Latest*) saca el `.exe`. Por eso el tag tiene que ser `vN`,
> el mismo número que quedó en `version.txt`: si se publica una versión nueva sin subir
> antes `version.txt`, las PC contestan «ya está al día» y no bajan nada.
>
> Si se olvidó adjuntar el `.exe`, entre a la versión en GitHub → **Edit** → adjúntelo y
> guarde. No hace falta volver a ejecutar `PUBLICAR_VERSION.bat`: volvería a subir el
> número y las PC tendrían que actualizarse otra vez para lo mismo.
>
> El `.exe` **no** se guarda en el repositorio (`.gitignore` excluye `dist\` y `*.exe`):
> viaja como adjunto de la versión publicada.


## 5. Actualizar una computadora de trabajo

El `.bat` se puede dejar en el escritorio, en el menú de inicio, en la carpeta del
programa, en un USB o en una carpeta compartida del servidor: **encuentra el programa
esté donde esté**.

1. Doble clic en **`ACTUALIZAR_DESDE_GITHUB.bat`**. Busca la carpeta del programa en este
   orden:
   - la que se le pase: `ACTUALIZAR_DESDE_GITHUB.bat "D:\Viaticos"`;
   - la que usó la vez anterior (queda guardada en
     `%APPDATA%\SistemaViaticos\instalacion.txt`);
   - la de los accesos directos del escritorio, del menú de inicio y de la barra de
     tareas;
   - Escritorio, Documentos, Descargas, `C:\` y `D:\` (dos niveles); si aun así no la
     encuentra, **pregunta la ruta**.
2. El mensaje va contando:
   - la versión instalada y la que hay en GitHub;
   - si ya está al día, termina sin cambiar nada (con `-Forzar` se puede repetir);
   - si hay una nueva: si el programa está abierto pregunta si lo cierra; **respalda**
     la versión actual en `respaldos_actualizacion\AAAA-MM-DD_HHMM`, **baja** el código
     de la rama `main` y el **`Sistema_Viaticos.exe` de la última versión publicada**, y
     los copia encima;
   - vuelve a dejar los **accesos directos** apuntando al ejecutable nuevo (escritorio,
     menú de inicio y barra de tareas) y, si no encuentra ninguno, crea uno en el
     escritorio y otro en el menú de inicio;
   - al final dice la versión con la que quedó y deja el detalle en `actualizacion.log`.
3. Abra el programa con el acceso directo, `INICIAR.bat` o el `.exe`, y siga trabajando:
   sus datos están intactos.

Para ver qué haría sin cambiar nada:

```powershell
powershell -ExecutionPolicy Bypass -File herramientas\actualizar.ps1 -Simular
```

Otras opciones del script: `-App "D:\Viaticos"` (la carpeta del programa), `-Repo URL`,
`-Forzar` (aunque la versión sea la misma), `-SoloAccesos` (solo repara los accesos
directos) y `-Abrir` (abre el programa al terminar).

**La primera vez** en una PC que solo tiene el `.exe`: copie
`ACTUALIZAR_DESDE_GITHUB.bat` a cualquier parte y ejecútelo. Si el programa está
instalado en un sitio poco habitual, pase la ruta (`... "D:\Viaticos"`); a partir de ahí
la recuerda.



## 6. Qué se conserva y cómo volver atrás

| Se conserva (nunca se copia encima) | Se reemplaza |
| --- | --- |
| `data\` (base SQLite y facturas) | todos los `.py` |
| `config.json` (servidor, IP, zoom) | los `.bat`, los `.md`, `documentacion\` |
| cualquier `*.db` | `version.txt` |
| `actualizacion.log` y `respaldos_actualizacion\` | `herramientas\` |
| `__pycache__`, `*.pyc` | `Sistema_Viaticos.exe` (se baja de la versión publicada) |

El copiado se hace con `robocopy` excluyendo justamente esas rutas, así que **la base del
cliente no se toca**. Antes de copiar se guarda la versión anterior completa (sin datos)
en `respaldos_actualizacion\`.

**Para volver atrás** (si una versión nueva diera problemas): copie el contenido de
`respaldos_actualizacion\AAAA-MM-DD_HHMM\` encima de la carpeta del programa y listo (su
`data\` y su `config.json` no están en ese respaldo, así que tampoco se pisan).

**La base de datos no se actualiza aquí**: las columnas nuevas las agrega el propio
programa al abrir (`database.inicializar()` migra solo). Por eso conviene **abrir el
programa una vez** después de actualizar.

## 7. Requisitos y límites

- **Windows 10/11** con **PowerShell 5.1** (viene instalado) y `robocopy` (viene con
  Windows). No hace falta instalar nada más para actualizar.
- El repositorio debe ser **público**; si es privado, hay que poner un *token* en la URL
  (`https://TOKEN@github.com/usuario/repo`).
- `version.txt` es un **número entero**. Si se publica a mano, no use `8.1`.
- El **código** que se copia es el de la rama `main` (el `.zip` que arma GitHub). Tiene
  que traer `main_qt.py`, `database.py` y `calculos.py`; si no, el actualizador **no
  copia nada** y avisa. En una PC que solo tiene el `.exe` no se copia código: solo el
  ejecutable.
- El **`.exe`** se baja del **adjunto de la última versión publicada**
  (`api.github.com/.../releases/latest`); si el adjunto se llama `Sistema_Viaticos.exe`
  también funciona la dirección fija
  `https://github.com/RICHARDs01001/sistema-viaticos/releases/latest/download/Sistema_Viaticos.exe`.
  Si la PC tiene `.exe` y la versión publicada **no** trae ninguno, el actualizador avisa
  y **no cambia nada**. GitHub admite adjuntos de hasta 2 GB: los 73 MB entran sin
  problema.
- Hay que **cerrar el programa** antes de copiar el `.exe` (si está abierto, Windows no
  deja reemplazarlo). El actualizador lo pregunta y lo cierra él mismo.
- Las **librerías de Python** (`PySide6`, `openpyxl`, `Pillow`, `reportlab`,
  `psycopg2-binary`…) no se actualizan solas: si una versión nueva pide una librería
  nueva, hay que instalarla una vez en esa PC con `pip install -r requirements.txt`.

## 8. Qué se probó

| Prueba | Resultado |
| --- | --- |
| Sintaxis del script (`Parser.ParseFile`) | sin errores |
| Ejecución con un repositorio que no existe | avisa «No pude leer version.txt del repositorio…», **no copia nada** |
| Copiado sobre una carpeta de prueba (código viejo + `data\viaticos.db` + `config.json`) | el código quedó actualizado; `data\viaticos.db`, `config.json` y `actualizacion.log` **intactos** |
| Respaldo previo | guardó el código anterior y **no** incluyó `data\` |
| Códigos de `robocopy` | 1 y 3 (copió bien); el script solo se detiene con 8 o más |
| Acceso directo que apuntaba a otra carpeta | quedó re-apuntado al `.exe` de la instalación buena |
| Accesos directos que faltaban (escritorio y menú de inicio) | los creó |
| `-Simular` sobre una instalación real | mostró versión instalada, versión de GitHub, si hay código y ejecutable, y qué accesos tocaría, **sin copiar nada** |

Falta la prueba contra el repositorio real: se hace la primera vez que el autor ejecute
`PUBLICAR_VERSION.bat` y una PC ejecute `ACTUALIZAR_DESDE_GITHUB.bat`.
