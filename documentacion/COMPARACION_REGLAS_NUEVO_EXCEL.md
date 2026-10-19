# Regla contra regla: Excel nuevo de viáticos vs. el programa

| Dato | Valor |
|---|---|
| Archivo leído | `C:\Users\richi\Desktop\PROGRAMA VIATICOS\MIEMPRESA_VIATICOS\herramientas\excels_de_trabajo\VIATICO 2 2026.xlsx` |
| Filas de viático leídas | 80 |
| Base de parámetros usada | `C:\Users\richi\Desktop\PROGRAMA VIATICOS\MIEMPRESA_VIATICOS\herramientas\prueba_excel\data_reglas\viaticos.db` (local, la comparación **no** toca el servidor) |
| Parámetros del programa | merienda hasta 21:00 · km $0.25 · redondeo $5.00 |

## 1. Tarifas y horas límite

| Concepto | Excel nuevo | Programa | ¿Igual? |
|---|---:|---:|---|
| Desayuno | $3.00 · 06:00 | $3.00 · 06:00 | sí |
| Almuerzo | $3.00 · 13:00 | $3.00 · 13:00 | sí |
| Merienda | $3.00 · 21:00 | $3.00 · 21:00 | sí |
| Taxi De Salida | (vacío) | $3.00 · 06:00 | sí |
| Taxi De Regreso | (vacío) | $3.00 · 21:00 | sí |
| Hospedaje | $15.00 | $15.00 | sí |
| Agua | $1.00 | $1.00 | sí |
| Combustible | $0.25 | $0.25 | sí |
| Parqueadero | $10.00 | $10.00 | sí |
| Redondeo | (vacío) | $5.00 | sí |

Lo que dicen las hojas «Parámetros» y «Notas» del Excel nuevo:

- Las reglas de las dos partes son las mismas: $3 por comida, $3 por taxi, $15 por
  noche, $1 por agua y **combustible = km × $0.25** (con la advertencia «AJUSTAR:
  valor de ejemplo, confirme con política de la empresa»).
- El **parqueadero/peaje** figura como $10.00 fijos por viaje, pero en las hojas
  semanales esa columna se escribe a mano (en este archivo hay valores de $3 a $35):
  por eso aquí se compara contra el valor de cada fila.
- Las «Notas» hablan de «**otros gastos** de $10.00 fijos por viaje», pero el formato
  no tiene esa columna: el único concepto extra es «**Transporte**», también escrito
  a mano y que el programa no paga (en el sistema entraría en «otros gastos»).
- La fila del **redondeo del cajero** está en blanco, así que la columna «VALOR A
  RETIRAR EN CAJERO» del Excel no calcula nada.

## 2. Viático por viático (columnas calculadas del Excel vs. el programa)

| Hoja | Empleado | Días E/P | Desayuno E/P | Almuerzo E/P | Merienda E/P | Taxi E/P | Hospedaje E/P | Agua E/P | Comb. E/P | TOTAL Excel | TOTAL programa | Diferencia |
|---|---|---|---|---|---|---|---|---|---|---:|---:|---:|
| 27 AL 2 DE AGOST | HERNANDEZ REGALADO BRAND | 0/2 | -3.00/3.00 | -3.00/3.00 | -3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 0.00/2.00 | 0.00/0.00 | $6.00 | $26.00 | $-20.00 |
| 27 AL 2 DE AGOST | MERCHAN DURAN CHRISTIAN  | 2/2 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 0.00/0.00 | $26.00 | $26.00 | $0.00 |
| 27 AL 2 DE AGOST | ZUÑIGA GAVILANES BRUNO S | 2/2 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 0.00/0.00 | $26.00 | $26.00 | $0.00 |
| 27 AL 2 DE AGOST | REYES MENENDEZ JUAN BRYA | 1/1 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 6.00/6.00 | 0.00/0.00 | 1.00/1.00 | 22.00/55.00 | $43.00 | $76.00 | $-33.00 |
| 27 AL 2 DE AGOST | HERNANDEZ REGALADO BRAND | 1/1 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 6.00/6.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $16.00 | $16.00 | $0.00 |
| 27 AL 2 DE AGOST | MERCHAN DURAN CHRISTIAN  | 1/1 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 6.00/6.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $35.00 | $16.00 | $19.00 |
| 27 AL 2 DE AGOST | ZUÑIGA GAVILANES BRUNO S | 1/1 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 6.00/6.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $16.00 | $16.00 | $0.00 |
| 27 AL 2 DE AGOST | SAENZ MORA ESTEBAN DANIE | 2/2 | 3.00/3.00 | 6.00/6.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 29.00/72.50 | $81.00 | $124.50 | $-43.50 |
| 27 AL 2 DE AGOST | JUAN GUILLERMO ZAMBRANO  | 2/2 | 3.00/3.00 | 6.00/6.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 0.00/0.00 | $29.00 | $29.00 | $0.00 |
| 27 AL 2 DE AGOST | SAENZ MORA ESTEBAN DANIE | 2/2 | 3.00/3.00 | 6.00/6.00 | 6.00/6.00 | 3.00/3.00 | 15.00/15.00 | 2.00/2.00 | 29.00/72.50 | $85.00 | $128.50 | $-43.50 |
| 27 AL 2 DE AGOST | JUAN GUILLERMO ZAMBRANO  | 2/2 | 3.00/3.00 | 6.00/6.00 | 6.00/6.00 | 3.00/3.00 | 15.00/15.00 | 2.00/2.00 | 0.00/0.00 | $35.00 | $35.00 | $0.00 |
| 3 AL 10 DE AGOST | HERNANDEZ REGALADO BRAND | 0/2 | -3.00/3.00 | -3.00/3.00 | -3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 0.00/2.00 | 0.00/0.00 | $6.00 | $26.00 | $-20.00 |
| 3 AL 10 DE AGOST | MERCHAN DURAN CHRISTIAN  | 2/2 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 0.00/0.00 | $26.00 | $26.00 | $0.00 |
| 3 AL 10 DE AGOST | ZUÑIGA GAVILANES BRUNO S | 2/2 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 0.00/0.00 | $26.00 | $26.00 | $0.00 |
| 3 AL 10 DE AGOST | HERNANDEZ REGALADO BRAND | 1/1 | 0.00/0.00 | 3.00/3.00 | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $6.00 | $6.00 | $0.00 |
| 3 AL 10 DE AGOST | ZUÑIGA GAVILANES BRUNO S | 1/1 | 0.00/0.00 | 3.00/3.00 | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $4.00 | $4.00 | $0.00 |
| 3 AL 10 DE AGOST | GONZALEZ OCHOA FAUSTO SA | 1/1 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 6.00/6.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $20.00 | $18.00 | $2.00 |
| 3 AL 10 DE AGOST | REYES MENENDEZ JUAN BRYA | 4/4 | 12.00/12.00 | 12.00/12.00 | 12.00/12.00 | 6.00/6.00 | 45.00/45.00 | 4.00/4.00 | 51.50/128.75 | $168.00 | $239.75 | $-71.75 |
| 3 AL 10 DE AGOST | PEREZ SINCHI EDISSON PAU | 4/4 | 12.00/12.00 | 12.00/12.00 | 12.00/12.00 | 6.00/6.00 | 45.00/45.00 | 4.00/4.00 | 0.00/0.00 | $91.00 | $91.00 | $0.00 |
| 3 AL 10 DE AGOST | JUAN GUILLERMO ZAMBRANO  | 4/4 | 12.00/12.00 | 12.00/12.00 | 12.00/12.00 | 6.00/6.00 | 45.00/45.00 | 4.00/4.00 | 0.00/0.00 | $91.00 | $91.00 | $0.00 |
| 10 AL 16 DE AGOS | HERNANDEZ REGALADO BRAND | 0/2 | -3.00/3.00 | -3.00/3.00 | -3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 0.00/2.00 | 0.00/0.00 | $6.00 | $26.00 | $-20.00 |
| 10 AL 16 DE AGOS | MERCHAN DURAN CHRISTIAN  | 2/2 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 0.00/0.00 | $26.00 | $26.00 | $0.00 |
| 10 AL 16 DE AGOS | ZUÑIGA GAVILANES BRUNO S | 2/2 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 0.00/0.00 | $26.00 | $26.00 | $0.00 |
| 10 AL 16 DE AGOS | REYES MENENDEZ JUAN BRYA | 1/1 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 6.00/6.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $45.00 | $20.00 | $25.00 |
| 10 AL 16 DE AGOS | ZUÑIGA GAVILANES BRUNO S | 2/2 | 3.00/3.00 | 3.00/6.00 | 6.00/6.00 | 3.00/3.00 | 15.00/15.00 | 1.00/2.00 | 47.00/117.50 | $113.00 | $187.50 | $-74.50 |
| 10 AL 16 DE AGOS | JUAN GUILLERMO ZAMBRANO  | 2/2 | 3.00/3.00 | 3.00/6.00 | 6.00/6.00 | 3.00/3.00 | 15.00/15.00 | 1.00/2.00 | 0.00/0.00 | $31.00 | $35.00 | $-4.00 |
| 10 AL 16 DE AGOS | PEREZ SINCHI EDISSON PAU | 2/2 | 3.00/3.00 | 3.00/6.00 | 6.00/6.00 | 3.00/3.00 | 15.00/15.00 | 1.00/2.00 | 0.00/0.00 | $31.00 | $35.00 | $-4.00 |
| 17 AL 23 DE AGOS | REYES MENENDEZ JUAN BRYA | 3/3 | 9.00/9.00 | 9.00/9.00 | 9.00/9.00 | 6.00/6.00 | 30.00/30.00 | 3.00/3.00 | 51.50/128.75 | $144.00 | $221.25 | $-77.25 |
| 17 AL 23 DE AGOS | ZUÑIGA GAVILANES BRUNO S | 3/3 | 9.00/9.00 | 9.00/9.00 | 9.00/9.00 | 6.00/6.00 | 30.00/30.00 | 3.00/3.00 | 0.00/0.00 | $66.00 | $66.00 | $0.00 |
| 17 AL 23 DE AGOS | GONZALEZ OCHOA FAUSTO SA | 3/3 | 9.00/9.00 | 9.00/9.00 | 6.00/6.00 | 3.00/3.00 | 30.00/30.00 | 3.00/3.00 | 17.50/43.75 | $105.00 | $131.25 | $-26.25 |
| 17 AL 23 DE AGOS | YOHANDER HERNANDEZ | 3/3 | 9.00/9.00 | 9.00/9.00 | 6.00/6.00 | 3.00/3.00 | 30.00/30.00 | 3.00/3.00 | 0.00/0.00 | $60.00 | $60.00 | $0.00 |
| 17 AL 23 DE AGOS | HERNANDEZ REGALADO BRAND | 5/5 | 15.00/15.00 | 15.00/15.00 | 15.00/15.00 | 6.00/6.00 | 60.00/60.00 | 5.00/5.00 | 26.00/65.00 | $178.00 | $217.00 | $-39.00 |
| 17 AL 23 DE AGOS | PEREZ SINCHI EDISSON PAU | 5/5 | 15.00/15.00 | 15.00/15.00 | 15.00/15.00 | 6.00/6.00 | 60.00/60.00 | 5.00/5.00 | 0.00/0.00 | $116.00 | $116.00 | $0.00 |
| 17 AL 23 DE AGOS | JUAN GUILLERMO ZAMBRANO  | 5/5 | 15.00/15.00 | 15.00/15.00 | 15.00/15.00 | 6.00/6.00 | 60.00/60.00 | 5.00/5.00 | 0.00/0.00 | $116.00 | $116.00 | $0.00 |
| 17 AL 23 DE AGOS | NAVA MUJICA GILMER MANUE | 5/5 | 15.00/15.00 | 15.00/15.00 | 15.00/15.00 | 6.00/6.00 | 60.00/60.00 | 5.00/5.00 | 0.00/0.00 | $150.00 | $116.00 | $34.00 |
| 17 AL 23 DE AGOS | GONZALEZ OCHOA FAUSTO SA | 1/1 | 0.00/0.00 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 1.00/1.00 | 21.00/52.50 | $50.00 | $81.50 | $-31.50 |
| 17 AL 23 DE AGOS | YOHANDER HERNANDEZ | 1/1 | 0.00/0.00 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $10.00 | $10.00 | $0.00 |
| 17 AL 23 DE AGOS | REYES MENENDEZ JUAN BRYA | 1/1 | 0.00/0.00 | 3.00/3.00 | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 | 1.00/1.00 | 16.00/40.00 | $86.00 | $60.00 | $26.00 |
| 17 AL 23 DE AGOS | ZUÑIGA GAVILANES BRUNO S | 1/1 | 0.00/0.00 | 3.00/3.00 | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $4.00 | $4.00 | $0.00 |
| 17 AL 23 DE AGOS | HERNANDEZ REGALADO BRAND | 1/1 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 0.00/3.00 | 0.00/0.00 | 1.00/1.00 | 9.00/5.00 | $24.00 | $23.00 | $1.00 |
| 17 AL 23 DE AGOS | PEREZ SINCHI EDISSON PAU | 1/1 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 0.00/3.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $7.00 | $10.00 | $-3.00 |
| 17 AL 23 DE AGOS | JUAN GUILLERMO ZAMBRANO  | 1/1 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 0.00/3.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $7.00 | $10.00 | $-3.00 |
| 17 AL 23 DE AGOS | NAVA MUJICA GILMER MANUE | 1/1 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 0.00/3.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $7.00 | $10.00 | $-3.00 |
| 17 AL 23 DE AGOS | HERNANDEZ REGALADO BRAND | 1/1 | 0.00/0.00 | 0.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 1.00/1.00 | 65.00/65.00 | $79.00 | $82.00 | $-3.00 |
| 17 AL 23 DE AGOS | PEREZ SINCHI EDISSON PAU | 1/1 | 0.00/0.00 | 0.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $7.00 | $10.00 | $-3.00 |
| 17 AL 23 DE AGOS | JUAN GUILLERMO ZAMBRANO  | 1/1 | 0.00/0.00 | 0.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $7.00 | $10.00 | $-3.00 |
| 17 AL 23 DE AGOS | NAVA MUJICA GILMER MANUE | 1/1 | 0.00/0.00 | 0.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $7.00 | $10.00 | $-3.00 |
| 17 AL 23 DE AGOS | GONZALEZ OCHOA FAUSTO SA | 1/1 | 3.00/3.00 | 3.00/3.00 | 3.00/0.00 | 3.00/3.00 | 0.00/0.00 | 1.00/1.00 | 50.00/50.00 | $69.00 | $66.00 | $3.00 |
| 17 AL 23 DE AGOS | YOHANDER HERNANDEZ | 1/1 | 3.00/3.00 | 3.00/3.00 | 3.00/0.00 | 3.00/3.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $13.00 | $10.00 | $3.00 |
| 17 AL 23 DE AGOS | JUAN GUILLERMO ZAMBRANO  | 1/1 | 3.00/3.00 | 3.00/3.00 | 3.00/0.00 | 3.00/3.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $13.00 | $10.00 | $3.00 |
| 17 AL 23 DE AGOS | REYES MENENDEZ JUAN BRYA | 2/2 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 50.00/50.00 | $83.00 | $83.00 | $0.00 |
| 17 AL 23 DE AGOS | ZUÑIGA GAVILANES BRUNO S | 2/2 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 0.00/0.00 | $26.00 | $26.00 | $0.00 |
| 17 AL 23 DE AGOS | MIRABA ZAMBRANO ALDRY SE | 2/2 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 0.00/0.00 | $26.00 | $26.00 | $0.00 |
| 17 AL 23 DE AGOS | GONZALEZ OCHOA FAUSTO SA | 3/3 | 6.00/6.00 | 6.00/9.00 | 9.00/9.00 | 3.00/3.00 | 30.00/30.00 | 3.00/3.00 | 43.75/43.75 | $121.00 | $124.00 | $-3.00 |
| 17 AL 23 DE AGOS | YOHANDER HERNANDEZ | 3/3 | 6.00/6.00 | 6.00/9.00 | 9.00/9.00 | 3.00/3.00 | 30.00/30.00 | 3.00/3.00 | 0.00/0.00 | $57.00 | $60.00 | $-3.00 |
| 17 AL 23 DE AGOS | JUAN GUILLERMO ZAMBRANO  | 3/3 | 6.00/6.00 | 6.00/9.00 | 9.00/9.00 | 3.00/3.00 | 30.00/30.00 | 3.00/3.00 | 0.00/0.00 | $57.00 | $60.00 | $-3.00 |
| 24 AL 30 DE AGOS | REYES MENENDEZ JUAN BRYA | 2/2 | 3.00/3.00 | 3.00/6.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 120.00/120.00 | $174.00 | $177.00 | $-3.00 |
| 24 AL 30 DE AGOS | ZUÑIGA GAVILANES BRUNO S | 2/2 | 3.00/3.00 | 3.00/6.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 0.00/0.00 | $26.00 | $29.00 | $-3.00 |
| 24 AL 30 DE AGOS | NARVAEZ ORTEGA ELVIS ALE | 4/4 | 12.00/12.00 | 12.00/12.00 | 12.00/12.00 | 6.00/6.00 | 45.00/45.00 | 4.00/4.00 | 62.50/62.50 | $198.00 | $182.00 | $16.00 |
| 24 AL 30 DE AGOS | NAVA MUJICA GILMER MANUE | 4/4 | 12.00/12.00 | 12.00/12.00 | 12.00/12.00 | 6.00/6.00 | 45.00/45.00 | 4.00/4.00 | 0.00/0.00 | $91.00 | $91.00 | $0.00 |
| 24 AL 30 DE AGOS | MENENDEZ ZAMBRANO RAMON  | 4/4 | 12.00/12.00 | 12.00/12.00 | 12.00/12.00 | 6.00/6.00 | 45.00/45.00 | 4.00/4.00 | 0.00/0.00 | $91.00 | $91.00 | $0.00 |
| 24 AL 30 DE AGOS | REYES MENENDEZ JUAN BRYA | 1/1 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 3.00/3.00 | 0.00/0.00 | 1.00/1.00 | 20.00/20.00 | $42.00 | $42.00 | $0.00 |
| 24 AL 30 DE AGOS | ZUÑIGA GAVILANES BRUNO S | 1/1 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 3.00/3.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $10.00 | $10.00 | $0.00 |
| 24 AL 30 DE AGOS | HERNANDEZ REGALADO BRAND | 3/3 | 9.00/9.00 | 9.00/9.00 | 9.00/9.00 | 6.00/6.00 | 30.00/30.00 | 3.00/3.00 | 62.50/62.50 | $145.00 | $145.00 | $0.00 |
| 24 AL 30 DE AGOS | REYES MENENDEZ JUAN BRYA | 2/2 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 50.00/50.00 | $89.00 | $89.00 | $0.00 |
| 24 AL 30 DE AGOS | ZUÑIGA GAVILANES BRUNO S | 2/2 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 0.00/0.00 | $26.00 | $26.00 | $0.00 |
| 24 AL 30 DE AGOS | REYES MENENDEZ JUAN BRYA | 2/2 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 50.00/50.00 | $89.00 | $89.00 | $0.00 |
| 24 AL 30 DE AGOS | ZUÑIGA GAVILANES BRUNO S | 2/2 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 15.00/15.00 | 2.00/2.00 | 0.00/0.00 | $26.00 | $26.00 | $0.00 |
| 24 AL 30 DE AGOS | NARVAEZ ORTEGA ELVIS ALE | 5/5 | 12.00/12.00 | 15.00/15.00 | 15.00/15.00 | 3.00/3.00 | 60.00/60.00 | 5.00/5.00 | 50.00/50.00 | $190.00 | $190.00 | $0.00 |
| 24 AL 30 DE AGOS | YORDANO TERÁN | 5/5 | 12.00/12.00 | 15.00/15.00 | 15.00/15.00 | 3.00/3.00 | 60.00/60.00 | 5.00/5.00 | 0.00/0.00 | $110.00 | $110.00 | $0.00 |
| 24 AL 30 DE AGOS | REYES MENENDEZ JUAN BRYA | 1/1 | 0.00/0.00 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 1.00/1.00 | 30.00/30.00 | $55.00 | $55.00 | $0.00 |
| 24 AL 30 DE AGOS | ZUÑIGA GAVILANES BRUNO S | 1/1 | 0.00/0.00 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $10.00 | $10.00 | $0.00 |
| 24 AL 30 DE AGOS | HERNANDEZ REGALADO BRAND | 3/3 | 9.00/9.00 | 9.00/9.00 | 9.00/9.00 | 6.00/6.00 | 30.00/30.00 | 3.00/3.00 | 115.75/115.75 | $199.00 | $199.00 | $0.00 |
| 24 AL 30 DE AGOS | MENENDEZ ZAMBRANO RAMON  | 3/3 | 9.00/9.00 | 9.00/9.00 | 9.00/9.00 | 6.00/6.00 | 30.00/30.00 | 3.00/3.00 | 0.00/0.00 | $66.00 | $66.00 | $0.00 |
| 24 AL 30 DE AGOS | GONZALEZ OCHOA FAUSTO SA | 2/2 | 6.00/6.00 | 6.00/6.00 | 6.00/6.00 | 6.00/6.00 | 15.00/15.00 | 2.00/2.00 | 50.00/50.00 | $109.00 | $109.00 | $0.00 |
| 24 AL 30 DE AGOS | MIRABA ZAMBRANO ALDRY SE | 2/2 | 6.00/6.00 | 6.00/6.00 | 6.00/6.00 | 6.00/6.00 | 15.00/15.00 | 2.00/2.00 | 0.00/0.00 | $41.00 | $41.00 | $0.00 |
| 31 AGOSTO AL 6 D | NARVAEZ ORTEGA ELVIS ALE | 1/1 | 3.00/3.00 | 3.00/3.00 | 3.00/0.00 | 6.00/3.00 | 0.00/0.00 | 1.00/1.00 | 45.00/45.00 | $94.00 | $88.00 | $6.00 |
| 31 AGOSTO AL 6 D | MENENDEZ ZAMBRANO RAMON  | 1/1 | 3.00/3.00 | 3.00/3.00 | 3.00/0.00 | 6.00/3.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $16.00 | $10.00 | $6.00 |
| 31 AGOSTO AL 6 D | NARVAEZ ORTEGA ELVIS ALE | 1/1 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 6.00/6.00 | 0.00/0.00 | 1.00/1.00 | 57.50/57.50 | $99.00 | $99.00 | $0.00 |
| 31 AGOSTO AL 6 D | GUZMAN ESPINOZA FAUSTO L | 0/1 | 3.00/3.00 | 3.00/3.00 | 3.00/3.00 | 6.00/6.00 | 0.00/0.00 | 1.00/1.00 | 0.00/0.00 | $16.00 | $16.00 | $0.00 |
| **TOTAL** | **80 filas** | | 363.00 / 381.00 | 405.00 / 459.00 | 393.00 / 396.00 | 237.00 / 243.00 | 1335.00 / 1335.00 | 160.00 / 169.00 | 1241.50 / 1703.25 | **$4821.00** | **$5221.25** | **$-400.25** |

### 2.1 Totales generales (lo que cuesta el conjunto)

Suma de las **80 filas** comparadas (columnas «E/P» = Excel / programa):

| Concepto | Excel nuevo | Programa | Diferencia |
|---|---:|---:|---:|
| **Total de viáticos** | **$4821.00** | **$5221.25** | **$-400.25** |
| Valor a retirar en cajero | $0.00 | $5390.00 | $-5390.00 |
| Desayunos | $363.00 | $381.00 | $-18.00 |
| Almuerzos | $405.00 | $459.00 | $-54.00 |
| Meriendas | $393.00 | $396.00 | $-3.00 |
| Taxis (salida + regreso) | $237.00 | $243.00 | $-6.00 |
| Hospedaje | $1335.00 | $1335.00 | $0.00 |
| Agua | $160.00 | $169.00 | $-9.00 |
| Combustible | $1241.50 | $1703.25 | $-461.75 |
| Transporte | $151.50 | $0.00 | $151.50 |
| Parqueadero / peaje | $535.00 | $535.00 | $0.00 |

Diferencia total del conjunto (Excel nuevo − programa): **$-400.25** en el total de viáticos. La suma de las diferencias por concepto da **$-400.25**, así que el cuadro explica el total.

Ojo con el cajero: la columna «VALOR A RETIRAR EN CAJERO» del Excel nuevo está
**vacía en las 80 filas** comparadas (siempre $0.00), así que ahí no hay nada que
comparar. El programa sí calcula ese valor (redondeo hacia arriba al múltiplo de
$5): por eso el cuadro dice $0.00 contra $5390.00.

Positivo = el formato nuevo paga más que las reglas del programa; negativo = paga
menos. Ni el parqueadero/peaje ni el transporte del Excel son un error del programa:
el parqueadero/peaje se le pasó igual para poder comparar el resto y el transporte
el programa no lo paga (lo toma de «otros», aquí en $0).

## 3. Conclusión

- Filas comparadas regla contra regla: **80**; coinciden exactamente **42** y
  tienen alguna diferencia **38**.
- **Totales generales**: el formato nuevo suma **$4821.00** en viáticos contra **$5221.25** del programa (diferencia **$-400.25**), y por cajero el Excel no llena la columna (**$0.00**) y el programa calcula **$5390.00**.
- Las **reglas de los dos lados son las mismas**: el programa calcula igual que las
  fórmulas del Excel —(días−1) comidas + el extremo por hora, taxi por hora,
  hospedaje por noches, agua por día, combustible = km × tarifa— y los parámetros
  coinciden (sección 1). Las diferencias que quedan son **datos escritos a mano en
  el Excel**, no reglas distintas:

  1. **Combustible: $-461.75 en 11 filas** (la diferencia más grande). La columna se
     escribe a mano a **$0.10 por km** (220 km → $22.00) aunque la propia hoja
     «Parámetros» dice **$0.25 por km** (220 km → $55.00, lo que calcula el
     programa). En la fila 17 al 23 N° 94 (20 km) el Excel puso $9.00 y el programa
     calcula $5.00. **Decisión del 18/10/2026: se deja en $0.25**, que es el valor de la
     hoja «Parámetros» y el de fábrica del programa; si la empresa trabaja con otra
     tarifa, la cambia en **Parámetros → Combustible** y no hay que tocar código.
  2. **Comidas y agua: $-84.00** (desayuno $-18.00 · almuerzo $-54.00 · merienda $-3.00 · agua $-9.00), por dos motivos:
     a) **3 filas con «Días de Viaje» vacío**: las fórmulas del Excel devuelven
        números **negativos** (−$3.00 por comida, $0 de agua) porque cuentan los días
        con la celda en blanco (HERNANDEZ REGALADO, salida 23:59 → regreso 10:00);
        el programa cuenta 2 días con las fechas y paga $11.00.
     b) **Celdas sobrescritas a mano**: en 10 al 16 N° 37 al 39 (2 días, regreso
        23:00) el Excel pagó 1 almuerzo y 1 agua y el programa 2 y 2; en 17 al 23
        N° 116 al 119 (regreso 23:59) el Excel dejó el almuerzo en $0 y el programa
        paga $3.00; en 17 al 23 N° 139 al 141 (regreso 15:00) el Excel pagó $3.00 de
        merienda aunque su propia nota la paga solo desde las 21:00.
  3. **Taxis: $-6.00 en 6 filas**: en 4 (salida a las 06:00) el Excel dejó el taxi de
     salida en $0 aunque su propia fórmula lo pagaría ($3.00 por viaje); en 2 (31 de
     agosto, regreso a las 19:30) pagó $6.00 porque eligió a mano el taxi de regreso,
     que su regla paga solo desde las 21:00.
  4. **Transporte: $151.50 en 7 filas**: el Excel lo escribe a mano ($2.00 a $50.00) y el
     programa no tiene ese concepto: en el sistema entraría en «otros gastos», que en
     esta comparación quedó en $0.
  5. **Parqueadero/peaje y hospedaje coinciden** en las 80 filas ($535.00 y $1335.00): al
     programa se le pasó el parqueadero/peaje de cada fila y las noches salen iguales
     (el Excel paga $15 por noche cuando el regreso es de otro día, igual que el
     parámetro «hospedaje por fechas» del sistema).

- **«VALOR A RETIRAR EN CAJERO» está vacío en las 80 filas** del Excel ($0.00): ahí no
  hay nada que comparar (el programa sí lo calcula: redondeo hacia arriba al múltiplo
  de $5). La fila del redondeo en «Parámetros» también está en blanco.
- **4 filas tienen «Días de Viaje» vacío** aunque las fechas sí están: 27 al 2, 3 al
  10 y 10 al 16 N° 7 (salida 23:59 → regreso 10:00) y 31 de agosto N° 52 (viaje de un
  día). De ahí salen los negativos del punto 2a.

Para dejar los dos lados cuadrados: deje el combustible en **$0.25 por km** (la tarifa
ya decidida; si la empresa usa otra, se cambia en Parámetros → Combustible), deje que
las comidas, el agua y los días se calculen con las fechas (no los escriba a mano) y
registre en el sistema el parqueadero/peaje y el transporte de cada viaje (el transporte
va en «otros gastos»).

