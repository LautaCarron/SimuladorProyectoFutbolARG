# SimuladorProyectoFutbolARG

Simulador del fútbol argentino (Proyecto AFA): Primera División, categorías de ascenso, copas nacionales e
internacionales, con modo Simulador, modo Manager y Modo dios. Hecho con [Streamlit](https://streamlit.io) y
también publicable como web estática con [stlite](https://github.com/whitphx/stlite) (`index.html`).

## Qué simula

| Nivel | Competencias |
|---|---|
| Ligas | Primera División, Primera Nacional, Federal A, Federal B (opcional, se crea desde el Modo dios), Primera B, Primera C, Promocional Amateur y Regional Amateur |
| Copas nacionales | Copa Argentina (128 equipos) y Supercopa Argentina |
| Copas internacionales | Libertadores, Sudamericana y Recopa (CONMEBOL) y Mundial de Clubes (cada 4 temporadas) |
| Extras | Calendario con fechas reales de la temporada, historial y palmarés, incidentes (suspensiones y sanciones), avisos |

La temporada 1 es 2026. Cada equipo tiene una "media" que cambia de una temporada a otra; los partidos se simulan con
goles Poisson y una "forma del día" aleatoria. Los ascensos, descensos, promociones y clasificaciones a copas se
resuelven solos al terminar cada temporada.

### Modos

* **Simulador**: se ve todo el fútbol argentino y se avanza por día, por fecha o con "Simular todo".
* **Manager (Manager Falopa)**: se dirige un club, llegan ofertas y eventos, y hay relaciones con hinchada, dirigencia,
  plantel y economía (`ui/manager.py`, `motor/ofertas.py`, `motor/eventos.py`, `motor/relaciones.py`).
* **Modo dios**: cambia formatos, descensos, ascensos y promociones de cada liga desde la barra lateral (`ui/dios.py`).

### Guardar y cargar partidas

La pestaña **Partidas** (al lado de Historial) descarga la partida en un archivo `.afa` y la vuelve a cargar:

* **Guardar**: botón *Descargar partida*. El archivo incluye todo: ligas, copas, calendario, historial y, en modo
  Manager, la carrera. Se puede ponerle un nombre.
* **Cargar**: se elige el archivo `.afa`, se ve de qué partida se trata (temporada, día, modo, club) y se confirma.
  Reemplaza la partida actual.
* **Antes de empezar a simular**: la pantalla de inicio tiene la opción **Cargar partida**, que abre el simulador
  directo en esa pestaña. En la web estática el simulador abre directo, así que la pestaña está a un clic.
* Los archivos quedan en el dispositivo de cada persona (no en el servidor): andan igual en la PC, en Streamlit Cloud
  y en la web estática, y nadie ve las partidas de otro.
* Una partida solo se puede cargar en la misma versión de datos con la que se guardó (`VERSION_ESTADO` en
  `motor/temporada.py`); si cambia la estructura del estado, las partidas viejas se rechazan con un aviso.
* El formato está pensado para no depender de la versión de pandas / numpy y, al cargar, solo acepta tipos conocidos:
  un `.afa` ajeno no puede ejecutar código (ver `motor/guardado.py`).

## Cómo ejecutarlo

```bash
python -m pip install -r requirements.txt
python -m streamlit run simuladorafa.py
```

En Windows también sirve `ejecutabla.bat` (tiene rutas de la PC del autor: hay que ajustarlas).

La versión web estática arranca desde `index.html`: carga los `.py` en el navegador con stlite. **Si se agrega o se
renombra un `.py`, hay que reflejarlo en la lista `ARCHIVOS` de `index.html`.** `netlify.toml` solo define los
encabezados para servir esos archivos.

## Estructura del proyecto

```
simuladorafa.py      Punto de entrada: arma el estado, las pestañas y los botones globales
motor/               Lógica de simulación pura (sin Streamlit)
  nucleo.py            goles, penales, fixtures, tablas y cruces genéricos
  temporada.py         estado de la partida y paso de una temporada a la siguiente
  calendario.py        qué día se juega cada fecha / ronda
  fechas.py            días de juego base de cada liga
  incidentes.py        suspensiones y sanciones
  ofertas.py, eventos.py, relaciones.py   modo Manager
  guardado.py          formato .afa: guardar y cargar partidas
ligas/               Una liga por módulo (formato, desempates, ascensos, cómo se juega cada fecha)
  primera.py, apertura_clausura.py, nacional.py, federal.py, federal_b.py, simples.py, regional.py
copas/               Competencias por rondas y copas internacionales
  argentina.py         Copa Argentina y Supercopa
  conmebol.py          Libertadores, Sudamericana y Recopa
  mundial.py           Mundial de Clubes
  registro.py          Registro de competencias por rondas (clases Competencia, PorRondas, CopaArgentina,
                       SupercopaArgentina y MundialDeClubes)
datos/               Solo datos (equipos, medias, escudos, palmarés, clubes del exterior)
ui/                  Pestañas de la interfaz Streamlit; cada una expone render(ctx)
  ui_guardado.py       pestaña Partidas (descargar / cargar)
  vista/               Piezas de dibujo compartidas (tablas, cuadros, fixture, ficha, CSS, calendario...)
```

## Convención de nombres de módulos

Hay módulos de lógica y de interfaz que tratan del mismo tema. Para que no haya dos archivos con el mismo nombre
(y los imports y las pestañas de un editor sean inequívocos), **la versión de interfaz, y el módulo de datos del
Regional, llevan un prefijo**:

| Antes | Ahora | Qué es |
|---|---|---|
| `ui/conmebol.py` | `ui/ui_conmebol.py` | Pestaña de Libertadores, Sudamericana y Recopa |
| `ui/mundial.py` | `ui/ui_mundial.py` | Pestaña del Mundial de Clubes |
| `ui/primera.py` | `ui/ui_primera.py` | Pestaña de Primera División |
| `ui/nacional.py` | `ui/ui_nacional.py` | Pestaña de Primera Nacional |
| `ui/federal.py` | `ui/ui_federal.py` | Pestaña de Federal A |
| `ui/federal_b.py` | `ui/ui_federal_b.py` | Pestaña de Federal B |
| `ui/regional.py` | `ui/ui_regional.py` | Pestaña de Regional Amateur |
| `ui/calendario.py` | `ui/ui_calendario.py` | Pestaña de Calendario |
| `ui/vista/calendario.py` | `ui/vista/vista_calendario.py` | Grilla y lista del calendario (dibujo) |
| `datos/regional.py` | `datos/datos_regional.py` | Clubes, zonas y regiones del Regional Amateur |

La lógica queda con su nombre original: `copas/conmebol.py`, `copas/mundial.py`, `ligas/primera.py`,
`ligas/nacional.py`, `ligas/federal.py`, `ligas/federal_b.py`, `ligas/regional.py` y `motor/calendario.py`.

## Cómo sumar cosas

* **Una competencia por rondas nueva**: escribir su lógica en un módulo de `copas/`, agregar una clase en
  `copas/registro.py` (hereda de `PorRondas` o de `Competencia`) y sumarla a `REGISTRO`.
* **Cambiar planteles, medias o escudos**: `datos/equipos.py` (no tiene lógica).
* **Una pestaña nueva**: crear `ui/ui_<nombre>.py` con `render(ctx)` y engancharla en `simuladorafa.py`.
* **Cambió la estructura del estado guardado**: subir `VERSION_ESTADO` en `motor/temporada.py` (las partidas `.afa`
  guardadas con la versión anterior dejan de poder cargarse).
* **Un tipo nuevo dentro del estado** (algo que no sea número, texto, lista, diccionario, fecha, array o DataFrame):
  sumarlo a `_PERMITIDOS` en `motor/guardado.py`, o no se va a poder cargar.
