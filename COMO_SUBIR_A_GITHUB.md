<!--
  Sistema de Viáticos Miempresa
  Autor:    Richard Esteban Salazar Guillén
  Contacto: richards0101789@gmail.com  ·  +593 981239086
  (c) 2026 Richard Esteban Salazar Guillén — Todos los derechos reservados.
-->

# Cómo subir esta carpeta a GitHub

Todo lo que hay **dentro de esta carpeta** es lo que va al repositorio. El `.gitignore` ya deja fuera
los datos de la empresa y la configuración de cada PC.

## 1. Crear el repositorio en GitHub

1. Entre a GitHub → **New repository**.
2. Nombre sugerido: `sistema-viaticos-miempresa`.
3. **No** marque *Add a README* (ya lo lleva esta carpeta).
4. Elija **Private** (recomendado: lleva el nombre de la empresa y la lógica de sus viáticos).
5. **Create repository** y copie la URL que aparece (por ejemplo
   `https://github.com/usuario/sistema-viaticos-miempresa.git`).

## 2. Subirlo (una sola vez)

Abra una consola **dentro de esta carpeta** (`PARA_GITHUB`) y ejecute:

```bat
git init
git branch -M main
git add .
git commit -m "Entrega inicial: Sistema de Viáticos Miempresa v6.2"
git remote add origin https://github.com/usuario/sistema-viaticos-miempresa.git
git push -u origin main
```

Si GitHub pide la clave, escriba un **token** (GitHub → *Settings → Developer settings →
Personal access tokens*), no la contraseña de la cuenta.

## 3. Subir los próximos cambios

```bat
git add .
git commit -m "Descripción corta de lo que cambió"
git push
```

## 4. Antes de subir, revisar

- [ ] Que **no** aparezcan `excel\`, `data\`, `respaldos_base\` ni `config.json`
      (compruebe con `git status` antes del commit).
- [ ] Que **no** se suba el `.exe` ni la carpeta `build\` (ya están ignorados).
- [ ] Si el repositorio es **público**, mirar las capturas de `capturas\`: están tomadas del sistema
      real y pueden mostrar datos de la empresa.
- [ ] Que `LICENCIA.md` y `CREDITOS.md` estén en la raíz (así GitHub muestra la autoría).

## 5. Qué NO debe ir al repositorio (para recordar)

| Se queda **fuera** | Por qué |
| --- | --- |
| `excel\` (Excel de empleados y clientes) | Datos personales y de la empresa |
| `data\` (SQLite + PDF de facturas) | Datos reales de viáticos |
| `respaldos_base\*.sql` | Copias completas de la base |
| `config.json` | IP, usuario, clave y zoom de cada computadora |
| `dist\` y `build\` (el `.exe`) | Se regenera con `EMPAQUETAR_EXE_SERVIDOR.bat` |
