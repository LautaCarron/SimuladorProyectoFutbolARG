# Ligas de otros países

Módulo para simular la primera división de otros países junto con el fútbol argentino. Hoy están **Uruguay** y **Brasil**; las demás se suman con datos (ver "Cómo sumar un país"). En la pestaña **Mundo** se elige el país activo (ver `datos/paises.py`); la liga se ve en **Ligas** cuando ese país está activo.

## Plan (cómo está pensado)

1. **Una liga es una lista de rondas** que se juegan en orden. Cada ronda tiene sus cruces (o todavía no, si dependen de
   lo anterior), su día y a qué tabla suma. El motor genérico (`ligas/exterior.py`) sabe armar ruedas, jugar rondas
   (de liga o eliminatoria) y armar tablas.
2. **Cada formato es una clase** (`Formato`): decide qué rondas hay, cuándo se arma lo que sigue, qué tablas se muestran y
   quién campea, sube y baja. Hoy: `uruguay` (`ligas/uruguay.py`) y `todos_contra_todos` (el de Brasil; ya probado en
   `tests/test_ligas_ext.py`, todavía sin liga cargada en los datos).
3. **Se enchufa al registro de competencias** (`copas/registro.py`, clase `LigaExterior`). Por eso el calendario, "Próximo
   día", "Simular todo", el historial, el palmarés, el progreso de la temporada y las fichas de los clubes funcionan sin
   tocar nada de eso.
4. **Los datos de cada país viven en su archivo** (`datos/json/liga_<país>.json`): formato, cuántos suben y bajan,
   calendario y los clubes de primera y de segunda con su media y su escudo. Esos clubes se suman a `CLUBES_INT`
   (`datos/clubes_int.py`), así que siguen jugando las copas CONMEBOL con la misma media: un club tiene una sola media en toda
   la partida (`S["rating_int"]`), y la que se edita en la liga se guarda ahí al cerrar la temporada. Los de segunda son la
   reserva: de ahí suben los ascendidos y ahí van los que bajan. El resto de los países (Brasil, Colombia...) sigue en
   `clubes_int.json` hasta que se los mueva a su archivo.
5. **Interfaz genérica** (`ui/ui_ligas_ext.py`): cada liga se dibuja en la pestaña Ligas del país activo, con Posiciones (una tabla por torneo, con editor
   de medias con buscador), Fixture y resultados, y Definiciones. Agregar un país no pide tocar la interfaz: Mundo, Ligas, Calendario, Historial y Avisos lo toman de `datos/paises.py`, que lee `LIGAS_EXT`.

## Cómo sumar un país

1. **Archivo del país**: `datos/json/liga_<país>.json` con `clave`, `nombre`, `pais`, `formato`, `descensos`, `ascensos`,
   `calendario` (para cada etapa: `[mes, día, día de la semana]`, 0 = lunes), `oscuros` (escudos de borde oscuro, opcional) y
   las listas `primera` y `segunda`, cada club con `nombre`, `media` y `escudo` (el escudo puede ir vacío: se dibujan las
   iniciales). Es el único lugar donde viven esos clubes: si estaban en `clubes_int.json`, se sacan de ahí.
2. **Registro**: sumar el nombre del archivo a `ARCHIVOS` en `datos/ligas_ext.py` y a `ARCHIVOS` de `index.html`.
3. **Formato**: si es de los que ya existen (`todos_contra_todos`), nada más. Si no, una clase que herede de `Formato` en
   `ligas/<pais>.py`, registrada en `FORMATOS`, e importada en `formato_de` (`ligas/exterior.py`).
4. La prueba `test_datos.py` avisa si falta un JSON en `index.html`, y `tests/test_ligas_ext.py` si los datos de la liga no cierran.

Ejemplo de cabecera (Brasil, bajan 4; el calendario sólo necesita la primera fecha; las listas `primera` y `segunda` van abajo):

```json
{"clave": "br", "nombre": "Brasileirão Série A", "pais": "Brasil", "formato": "todos_contra_todos",
 "descensos": 4, "ascensos": 4, "calendario": {"Liga": [1, 31, 6]},
 "primera": [{"nombre": "Athletico-PR", "media": 64, "escudo": ""}, "..."],
 "segunda": [{"nombre": "Avaí", "media": 52, "escudo": ""}, "..."]}
```

## Uruguay: formato implementado (2026)

* **Apertura** (15 fechas, una rueda) · **Intermedio** (dos grupos de 8 armados con el Apertura: 1°, 4°, 5°, 8°, 9°, 12°,
  13° y 16° contra el resto; 7 fechas y final entre ganadores de grupo, que no suma a las tablas) · **Clausura** (15 fechas,
  localías invertidas).
* **Tabla Anual** = Apertura + Intermedio + Clausura (las finales y desempates no suman).
* **Campeón**: si un club gana Apertura, Clausura y Anual, es campeón. Si no, semifinal a partido único entre los campeones
  del Apertura y del Clausura (si es el mismo club, no hay) y su ganador juega la final a ida y vuelta contra el ganador de
  la Anual. Si el ganador de la semifinal ya era el de la Anual, es campeón.
* **Copas CONMEBOL**: la Tabla Anual muestra el destino de cada club y es lo que arma las copas de la temporada siguiente
  (`copas/conmebol.py`, `_sortear_pais`). Libertadores: campeón = Uruguay 1 y subcampeón = Uruguay 2 (grupos), y por Tabla
  Anual Uruguay 3 (Fase 2) y Uruguay 4 (Fase 1); Sudamericana: los cuatro que siguen en la Anual (Fase 1, entre clubes uruguayos). Si un club ya clasificó por
  otra vía (por ejemplo, campeón de la Libertadores), el cupo baja al que sigue. Las cantidades salen de `CUPOS_*` de
  `copas/conmebol.py`. El **campeón del Intermedio** no tiene cupo propio: juega la Supercopa contra el campeón uruguayo.
* **Descenso**: promedio de dos temporadas (puntos del año anterior + los de este, sobre partidos jugados); bajan 3 y suben 3
  de la Segunda División (los que ascienden en su tabla). En la temporada 1 sólo cuenta la actual.
* Fuentes del formato: reglamento y notas de prensa de 2026 (El Observador, ESPN, RSSSF).

### Simplificaciones y supuestos (a revisar)

* **Empate en puntos arriba** (Apertura, Clausura o Anual): juegan un partido de desempate los dos mejor ubicados (diferencia
  de gol, goles a favor), en cancha neutral y con penales. El reglamento real puede prever otra instancia.
* Semifinal y desempates a partido único en cancha neutral; en la final la ida es del ganador de la semifinal y la vuelta
  del de la Anual; global empatado = penales.
* **Sección Campeones** (pestaña de cada liga): por temporada, campeón, subcampeón, ganadores de cada torneo y los partidos decisivos (semifinal, finales, desempates). Se anota al cerrar la temporada en `S["ext_def"]` y el campeón suma al palmarés del Historial.
* **Medias**: los clubes del exterior vuelven 15 % cada año hacia su media inicial (`REVERSION_EXT` en `motor/temporada.py`) con ruido de ±1,5.
* **Cuántos suben y bajan** (3 y 3, como bajaron Plaza Colonia, River y Miramar Misiones tras 2025) y **cuántos años cuenta
  el promedio** (2): están en `liga_uruguay.json` los primeros y en `ligas/uruguay.py` el segundo. Confirmar.
* **Uruguay 4 y la Copa AUF Uruguay**: el Uruguay 4 (Libertadores · Fase 1) es del campeón de la Copa AUF Uruguay (si ya
  clasificó por la liga, el cupo vuelve a la Tabla Anual). Ver "Copa AUF Uruguay" más abajo. La columna "Destino" de la Tabla
  Anual sigue mostrando quién lo ocuparía por tabla: es el que lo recibe si el campeón de la copa ya había clasificado.
* **Segunda División Profesional** (`ligas/uruguay_segunda.py`, 14 clubes de 2026): Torneo Competencia (dos series de 7 y final
  entre ganadores; sus puntos cuentan), fase regular a doble rueda (26 fechas) y Tabla Anual = Competencia + regular. Campeón:
  primero de la Anual. Suben directo los 2 primeros; del 3° al 6° juegan el playoff por el tercer ascenso (semifinales 3° vs 6°
  y 4° vs 5° en cancha del mejor ubicado, final neutral; si el ganador de la Competencia quedó afuera, ocupa el lugar del 6°).
  Descenso: el real de 2026 se anuló (repechaje con la Divisional C), pero acá bajan los 2 últimos de la Tabla Anual a una
  **tercera división falsa** (ver más abajo) y suben 2 de ella al azar. Las series se sortean al azar.
  Los clubes están en `segunda` de `liga_uruguay.json` con medias de 49 a 55 (orientativas, sin escudo); Rampla Juniors,
  Sud América y Villa Española se sacaron porque en 2026 no están en la Segunda.
* El calendario usa sábados fijos (Apertura desde el 7/2, Intermedio desde el 13/6, Clausura desde el 8/8, definiciones desde
  el 21/11); no copia las fechas reales.

## Qué falta (próximos pasos)

* **Brasil** (`datos/json/liga_brasil.json`): Série A y Série B de 20 clubes, todos contra todos a doble rueda; bajan y suben 4. La A arranca el 31/1 y la B el 28/3 (semanal, sin copiar fechas reales). Los clubes de la B que no tenían datos (Ceará, Botafogo-SP, Vila Nova, etc.) van con medias orientativas y sin escudo. Sin Copa do Brasil ni estaduales.
* **Supercopa Uruguaya** (campeón vs. ganador del Intermedio): sin simular.
* En la primera temporada de la partida las copas siguen armándose con el sorteo ponderado por media: todavía no hay tabla.
* Palmarés histórico real: las ligas del exterior sólo cuentan las temporadas simuladas.
* Modo Manager: sólo se dirigen clubes argentinos; las ligas del exterior se juegan solas con el calendario.
* Se guarda en el `.afa` (subió `VERSION_ESTADO` a 22: las partidas guardadas con la versión anterior ya no se cargan).

## Tercera división falsa (Uruguay)

`datos/json/liga_uruguay.json` trae `tercera`: 20 clubes (nombre, media, escudo) que **no se simulan**. Es la reserva de la
Segunda División: al cerrar la temporada bajan los últimos de su Tabla Anual (`descensos` de `segunda_liga`, hoy 2) y suben, al
azar, la misma cantidad de la tercera (con un poco más de chances los de mejor media, `LigaExterior._sortear_tercera`). La lista
vive en `S["ext_clubes"]["Uruguay|3"]` y lo último que pasó, en `S["ext_mov3"]["Uruguay"]` (Historial). Sus clubes también son
los **amateurs de la Copa AUF Uruguay**. Los nombres y las medias (38 a 46) son orientativos: hay que revisarlos.

## Copa AUF Uruguay (`copas/uruguay.py`, `CopaUruguay` en `copas/registro.py`)

Formato 2026 (nuevo formato anunciado por la AUF; fuente: Montevideo Portal, lanzamiento de la Copa AUF Uruguay 2026):

* **40 clubes**: los 16 de la Liga AUF, los 8 mejores del Torneo Competencia de la Segunda y 16 amateurs (de la tercera falsa).
* **Grupos** entre los 24 profesionales: 6 de 4 (4 bombos por media), una rueda. Pasan los 2 primeros y los 4 mejores terceros.
* **Dieciseisavos**: profesionales entre sí (siembra de los grupos: 1° contra 16°) y amateurs entre sí. Desde octavos, un solo
  cuadro (sorteo libre en octavos). Semifinales y final en cancha neutral. Todo a partido único, con penales si empatan.
* **Premio**: el campeón tiene el Uruguay 4 (`S["ext_copa"]["Uruguay"]`, que usa `_sortear_pais(..., primero=...)` en
  `copas/conmebol.py`). Si ya clasificó, el cupo sigue por la Tabla Anual.
* **Cuándo**: se sortea cuando la Segunda termina el Torneo Competencia (hasta entonces no figura en el calendario) y se juega
  desde el primer miércoles de agosto, cada dos semanas (8 fechas; la final, el 11/11 de 2026).
* Estado: `S["copa_uy"]` con la misma forma que una liga del exterior (se juega con `jugar_ronda`). Campeones en
  `S["ext_def"]["copa_uy"]` y palmarés en `S["hist_copa_uy"]`.
* **Simplificaciones a revisar**: los amateurs no tienen clasificatoria (en la realidad 10 son de la OFI, 4 de la C y 2 de la D);
  los grupos son una sola rueda; las llaves previas a las semifinales son a partido único; el sorteo de grupos es por bombos de
  media. Las fuentes de 2025/2026 no coinciden del todo (otra nota habla de 32 clubes sin grupos): se tomó el formato nuevo.
* Se guarda en el `.afa` (subió `VERSION_ESTADO` a 24: las partidas guardadas con la versión anterior ya no se cargan).

## Segunda división simulada (cualquier país)

Si el archivo de la liga trae `segunda_liga` (`nombre`, `formato`, `descensos`, `calendario`), `datos/ligas_ext.py` suma una
liga más (`clave` + "2", `divisional` 2, `superior` = la primera) con los clubes de `segunda`. Quedan en el mismo país, con su
pestaña, calendario, historial y palmarés. Al cerrar la temporada, `LigaExterior.cerrar` de la primera toma de su tabla quiénes
suben (`cierre()["suben"]`) y manda a los que bajan; tienen que subir y bajar la misma cantidad. En `S["ext_clubes"]` la segunda
se guarda como `"Uruguay|2"` y su columna del Historial es `"Uruguay · D2"`. Sin `segunda_liga`, la segunda sigue siendo una
reserva de la que suben clubes al azar.
