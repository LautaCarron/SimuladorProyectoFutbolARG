# SimuladorProyectoFutbolARG

Simulador del fútbol argentino (Proyecto AFA): Primera División, categorías de ascenso, copas nacionales e
internacionales, con modo Simulador, modo Manager y Modo dios. Hecho con [Streamlit](https://streamlit.io) y
también publicable como web estática con [stlite](https://github.com/whitphx/stlite) (`index.html`).

## Qué simula

| Nivel | Competencias |
|---|---|
| Ligas | Primera División, Primera Nacional, Federal A, Federal B (opcional, se crea desde el Modo dios), Primera B, Primera C, Promocional Amateur (con 25 clubes o más se juega en dos zonas) y Regional Amateur |
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

### Mi club (club propio)

En la pestaña **Partidas**, debajo de guardar y cargar, está **Mi club** (`ui/crear_club.py`): se crea **un solo club** propio.
Los campos están armados con lo que ya existe en el Regional Amateur: **provincia** y **liga** se eligen de las listas y la
**región** se completa sola a partir de la liga (Liga Marplatense → Pampeana Sur). También se cargan nombre, ciudad, un nivel
inicial (20 a 33, como los clubes del Regional) y una foto del **escudo** (PNG, JPG o WEBP de hasta 1 MB; se achica a 192 px).

* **Entra en la temporada siguiente**: al crearlo queda pendiente (se puede cancelar) y se suma al Regional Amateur cuando
  empieza la temporada que viene. Después aparece en *Clubes*, en las tablas y en *Elegir un equipo* del Manager.
* **Dar de baja**: lo que le quede por jugar esta temporada (en cualquier competencia) lo pierde **3-0** y desaparece al
  cerrar la temporada. Su lugar **no se cubre solo**: la liga queda con un club menos (si era de Primera, juega con 29) y, para
  reponerlo, se suma un ascenso o se cambia el tamaño desde el Modo dios. Si dejó títulos, en el palmarés quedan su nombre y su
  escudo. Mientras tanto ya se puede crear otro.
* **Palmarés**: los títulos se anotan por nombre, así que si el club se llama como uno que ya existe (Aldosivi) entra como
  *Aldosivi (propio)* y sus títulos no se suman a los del club real (ni a los de un club propio anterior).
* **Es de la partida**: vive en `S` (`club_pendiente`, `club_propio`, `clubes_ex`), se guarda en el `.afa` y *Reiniciar* lo borra.

Cómo está hecho: `motor/club_usuario.py` (crear, dar de baja, entrar y salir al cerrar la temporada), `datos/club_propio.py`
(provincias, ligas, regiones, validación y escudo) y, para los 3-0, `motor.nucleo.jugar`, que le da por perdido 0-3 a quien
tenga la media `WO_RATING`. Como las funciones de datos no reciben `S`, `club_usuario.activar(S)` deja el club disponible por
hilo en cada pasada de la app, sin mezclar partidas de distintas personas. La web estática (`index.html`) usa los mismos
archivos, pero no se probó ahí.

### Guardar y cargar partidas

La pestaña **Partidas** (al lado de Historial) descarga la partida en un archivo `.afa` y la vuelve a cargar:

* **Guardar**: botón *Descargar partida*. El archivo incluye todo: ligas, copas, calendario, historial y, en modo
  Manager, la carrera. Se puede ponerle un nombre.
* **Cargar**: se elige el archivo `.afa`, se ve de qué partida se trata (temporada, día, modo, club) y se confirma.
  Reemplaza la partida actual.
* **Antes de empezar a simular**: se entra al simulador y se carga desde esta pestaña.
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
simuladorafa.py      Punto de entrada: sólo arma la página y reparte el contexto a las pestañas
config.py            Parámetros fijos (sorpresa, volatilidad) y detección del entorno (PC / web estática)
motor/               Lógica de simulación pura (sin Streamlit)
  nucleo.py            goles, penales, fixtures, tablas y cruces genéricos
  temporada.py         estado de la partida y paso de una temporada a la siguiente
  simulacion.py        cómo se juega cada competencia (tabla de despacho) y "Simular todo"
  progreso.py          qué terminó, porcentajes y avisos de la temporada (clase Progreso)
  calendario.py        qué día se juega cada fecha / ronda
  consultas.py         partidos jugados y por jugar de cada competencia (reciben S por parámetro)
  manager.py           lógica del modo Manager sin interfaz (sincronización, relaciones, simular día por día)
  fechas.py            días de juego base de cada liga
  incidentes.py        suspensiones y sanciones
  ofertas.py, eventos.py, relaciones.py   modo Manager
  guardado.py          formato .afa: guardar y cargar partidas
  club_usuario.py      club propio: crear, dar de baja y entrada / salida al cerrar la temporada
ligas/               Una liga por módulo (formato, desempates, ascensos, cómo se juega cada fecha)
  primera.py, apertura_clausura.py, nacional.py, federal.py, federal_b.py, simples.py, regional.py
  desempates.py        piezas comunes de los desempates por puntos (bloque empatado, duelo o liguilla)
copas/               Competencias por rondas y copas internacionales
  argentina.py         Copa Argentina y Supercopa
  conmebol.py          Libertadores, Sudamericana y Recopa
  mundial.py           Mundial de Clubes
  registro.py          Registro de competencias por rondas (clases Competencia, PorRondas, CopaArgentina,
                       SupercopaArgentina y MundialDeClubes)
datos/               Datos separados del código: los .py solo leen datos/json/*.json y exponen los mismos nombres de siempre
  json/                equipos.json (medias por categoría), escudos.json, geografia.json (origen y regiones), palmares.json,
                       logos.json, clubes_interior.json, clubes_int.json, clubes_mundial.json,
                       regional.json (clubes con zona, regiones, finales) y regional_extra.json (clubes sueltos a mano)
  club_propio.py       el club propio: provincias, ligas y regiones disponibles, validación del nombre y del escudo
  cargador.py          cargar("nombre") lee datos/json/<nombre>.json (si está mal escrito, avisa archivo y línea)
ui/                  Pestañas de la interfaz Streamlit; cada una expone render(ctx)
  contexto.py          clase Contexto: lo que reciben las pestañas (estado, progreso, pestañas, avisos)
  pestanas.py          arma las pestañas de arriba, las de ligas y las de copas
  acciones.py          botones globales: Próximo día, Simular todo, Nueva temporada, Reiniciar
  ui_guardado.py       pestaña Partidas (descargar / cargar)
  crear_club.py        sección "Mi club" de la pestaña Partidas (crear y dar de baja el club propio)
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

* **Una liga nueva que se juega por fechas**: sumarla a `_JUGADORES` en `motor/simulacion.py` (y a `_LIGAS_RESTANTES`
  para que entre en "Simular todo"). "Próximo día" y "Simular todo" usan esa misma tabla.
* **Una competencia por rondas nueva**: escribir su lógica en un módulo de `copas/`, agregar una clase en
  `copas/registro.py` (hereda de `PorRondas` o de `Competencia`) y sumarla a `REGISTRO`.
* **Cambiar planteles, medias o escudos**: `datos/json/equipos.json` (medias por categoría) y `datos/json/escudos.json`.
  Los `.py` de `datos/` ya no tienen datos, solo los leen.
* **Sumar clubes al Regional Amateur sin zona**: una entrada más en `datos/json/regional_extra.json` (`nombre`, `region`,
  `provincia`, `ciudad`, `liga` y, si hay, `escudo`). Entra con media 10 en "<región> · Sin zona". Si el club es del interior y
  no está en el Regional, también necesita su ciudad/provincia/liga en `datos/json/clubes_interior.json`.
* **Una pestaña nueva**: crear `ui/ui_<nombre>.py` con `render(ctx)` (`ctx` es un `Contexto`, ver `ui/contexto.py`),
  sumar su contenedor a `Pestanas` en `ui/pestanas.py` y engancharla en `PESTANAS_UI` de `simuladorafa.py`.
* **Una consulta o vista nueva**: las funciones de `ui/vista` y de `motor/consultas.py` reciben `S` por parámetro;
  no leer `st.session_state.S` desde la vista. Lo mismo con el club del manager
  (`ctx.club`) y el modo (`ctx.modo_mgr`): viajan por parámetro, no por claves ocultas de la sesión.
* **Un archivo `.py` o `.json` nuevo**: sumarlo a `ARCHIVOS` de `index.html` (si no, la web estática no lo carga).
  `tests/test_datos.py` avisa si falta algún JSON de datos.
* **Cambió la estructura del estado guardado**: subir `VERSION_ESTADO` en `motor/temporada.py` (las partidas `.afa`
  guardadas con la versión anterior dejan de poder cargarse).
* **Un tipo nuevo dentro del estado** (algo que no sea número, texto, lista, diccionario, fecha, array o DataFrame):
  sumarlo a `_PERMITIDOS` en `motor/guardado.py`, o no se va a poder cargar.

## Más documentación y pruebas

* `docs/FORMATOS.md`: cómo funciona cada competencia (formatos, ascensos, descensos, copas).
* `tests/golden.py`: herramienta para refactorizar el motor sin cambiar su comportamiento (compara el estado completo
  de dos versiones con la misma semilla; ver el docstring).
* `tests/test_humo.py`: prueba rápida (una temporada del motor y la app completa con el test headless de Streamlit).
  Correr con `python -m pip install -r requirements-dev.txt` y `python -m pytest`.
