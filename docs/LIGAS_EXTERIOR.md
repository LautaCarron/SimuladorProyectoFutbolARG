# Ligas de otros países

Módulo para simular la primera división de otros países junto con el fútbol argentino. Hoy están **Uruguay**, **Brasil**, **Chile** y **Colombia**; las demás se suman con datos (ver "Cómo sumar un país"). En la pestaña **Mundo** se elige el país activo (ver `datos/paises.py`); la liga se ve en **Ligas** cuando ese país está activo.

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
3. **Palmarés histórico (opcional)**: crear `datos/json/palmares_<clave>.json` (por ejemplo, `palmares_uy.json` para la clave `uy`). Cada entrada usa como clave el identificador de historial de la competencia (`hist_ext_uy`, `hist_copa_uy`, etc.) y contiene `descripcion` y `titulos` (club: cantidad). El cargador lo incorpora automáticamente; si el archivo no existe, el palmarés empieza vacío. Agregar también el JSON a `ARCHIVOS` en `index.html` para que esté disponible en la versión web.
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
  **tercera división falsa** (ver más abajo) y suben 2 de ella (el campeón y el subcampeón de la Primera Amateur). Las series se sortean al azar.
  Los clubes están en `segunda` de `liga_uruguay.json` con medias de 49 a 55 (orientativas, sin escudo); Rampla Juniors,
  Sud América y Villa Española se sacaron porque en 2026 no están en la Segunda.
* El calendario usa sábados fijos (Apertura desde el 7/2, Intermedio desde el 13/6, Clausura desde el 8/8, definiciones desde
  el 21/11); no copia las fechas reales.

## Brasil: Série C y Série D (`ligas/brasil_d.py`)

`liga_brasil.json` trae `tercera` (20 clubes de la Série C 2026) y `cuarta` (96 de la Série D 2026, con su grupo A1 a A16),
más `tercera_liga` y `cuarta_liga`. La cadena queda A (20) → B (20) → C (20) → D (96): bajan y suben 4 en cada escalón
(`datos/ligas_ext.py` arma las ligas de `divisional` 3 y 4; `LigaExterior.cerrar` mueve a las cuatro; los cambios C↔D van a
`S["ext_mov4"]`). Columnas del Historial: `"Brasil · D3"` y `"Brasil · D4"`.

* **Série C**: formato simple, todos contra todos a ida y vuelta (38 fechas, desde el 29/3) con el motor `todos_contra_todos`. Suben los 4 primeros y bajan los 4 últimos. (El real de 2026 es primera fase + cuadrangulares + final, y baja sólo 2.)
* **Série D** (formato real 2026): 16 grupos de 6 a doble rueda; pasan 4 de cada uno (64) a un cuadro de eliminación directa a ida y
  vuelta (segunda fase, tercera fase, octavos, cuartos, semifinales, final). Suben los 4 semifinalistas. La Llaves muestra de octavos a
  la final; lo anterior está en Fixture y resultados.
* **Grupos de la D**: la primera temporada son los reales; el club que sube a la C deja su lugar al que baja (`mover_clubes_en_lugar`),
  sin criterio geográfico.
* **Simplificaciones**: el real de 2026 baja 2 de la C y sube 6 de la D (la C crece a 24 en 2027 y a 28 en 2028, y la D tiene un
  playoff entre los eliminados en cuartos); acá la pirámide está cerrada y son 4 y 4. El cuadro de la D es fijo por siembra.
  Las medias son orientativas (C: 52 a 62, D: 38 a 54) y los clubes nuevos no tienen escudo (se dibujan las iniciales).
* La Série B de `liga_brasil.json` tenía a Paysandu, que en 2026 juega la C: se lo pasó a la C y entró São Bernardo (subió de la C).
* Se guarda en el `.afa` (subió `VERSION_ESTADO` a 26: las partidas guardadas con la versión anterior ya no se cargan).

## Chile: Liga de Primera, Primera B y Segunda División Profesional (`datos/json/liga_chile.json`)

Tres ligas con el motor `todos_contra_todos` (sin formato nuevo ni código nuevo: sólo datos). La Liga de Primera tiene los 16 clubes de 2026, la
Primera B de Chile (`clave` `cl2`) los 16 de su temporada 2026 y la Segunda División Profesional (`clave` `cl3`, tercera categoría) los 14 de 2026; la pirámide está cerrada: entre Primera y B bajan y suben 2, entre B y Segunda baja y sube 1.

* **Liga de Primera** (clave `cl`): doble rueda, 30 fechas, viernes desde el 30/1. Campeón el que más puntos suma; bajan los 2 últimos.
  Columna del Historial: `"Chile"`.
* **Primera B de Chile** (clave `cl2`): doble rueda, 30 fechas, viernes desde el 20/2. Suben los 2 primeros y baja el último a la Segunda División
  Profesional. Columna del Historial: `"Chile · D2"`.
* **Segunda División Profesional de Chile** (clave `cl3`, `divisional` 3): 14 clubes de 2026 (Zona Norte: Atlético Colina, Brujas de Salamanca, Concón National,
  Provincial Ovalle, Real San Joaquín, Trasandino y Santiago City; Zona Sur: Deportes Colchagua, Deportes Linares, Deportes Rengo, General Velásquez,
  Lota Schwager, Provincial Osorno y Santiago Morning), `tercera` y `tercera_liga` en el JSON. Doble rueda, 26 fechas, sábados desde el 21/3. Sube el
  campeón a la Primera B y ocupa su lugar el último de la B. No baja nadie (la Tercera División A no se simula). Columna del Historial: `"Chile · D3"`.
* **Cupos CONMEBOL**: salen de las constantes que ya tenía Chile en `copas/conmebol.py` (2 a grupos, 2 a la Fase 2 y 4 a la Sudamericana) y se
  reparten por la tabla final, no por sorteo. Los clubes de Primera salieron de `clubes_int.json`: siguen jugando las copas con la misma media.
* **Simplificaciones a revisar**: en la realidad la Primera B da un ascenso directo (el 1°) y otro por la Liguilla de Ascenso (2° a 8°); acá suben
  los 2 primeros. Los cupos reales son 1°-2° a grupos, 3° contra el campeón de la Copa Chile por la Fase 2 y 4°-6° a la Sudamericana (no hay Copa
  Chile). El calendario es semanal y no copia las fechas reales. Los de la Primera B tienen medias orientativas (49 a 58) y los de la Segunda División Profesional (41 a 48) también; estos últimos no tienen
  escudo (se dibujan las iniciales). El formato real de la Segunda 2026 es otro: dos zonas de 7 (Norte y Sur) a doble rueda, una llave entre los
  cuartos de cada zona, y después Liguilla de Campeón (3 primeros de cada zona + el ganador de la llave) y Liguilla de Descenso (los demás), cada
  una a doble rueda; el campeón de la Liguilla sube y los 2 peores de la de Descenso bajan a la Tercera A. Acá es una sola tabla de 14 con todos
  contra todos a ida y vuelta, y no hay descenso. Palmarés histórico en `palmares_cl.json` (Primera 1933-2025 y Primera B 1952-2025; los conteos de la B cambian según la fuente) y logos de las dos ligas en `logos.json`.
* Se guarda en el `.afa` (subió `VERSION_ESTADO` a 27: las partidas guardadas con la versión anterior ya no se cargan).
* Al sumar la Segunda División Profesional `VERSION_ESTADO` subió a 29 (nueva liga en el estado): las partidas guardadas con la versión anterior ya no se cargan.


## Supercopa de Chile (`SupercopaChile` en `copas/registro.py`, `ui/ui_supercopa_cl.py`)

Final Four a partido único y en cancha neutral, con penales directos (formato estrenado en 2026): el 1° y el 2° de la Liga de Primera y el campeón y el
subcampeón de la Copa Chile. Semifinales: 1° de la liga contra el subcampeón de la copa y 2° de la liga contra el campeón de la copa; después, la final.
Si un club clasifica por dos vías, su lugar lo toma el que sigue en la tabla de la liga (y no esté ya clasificado). Como las otras supercopas del simulador,
se juega una semana después de que terminan la liga y la copa y cierra la temporada actual (en la realidad abre la siguiente). Las semifinales se juegan en un
día y la final cuatro días después. Palmarés: `hist_supercopa_cl` en `palmares_cl.json` (14 ediciones, 2013-2026; verificar contra la ANFP). Logo: clave
`"Supercopa de Chile"` en `logos.json` (opcional). No hay Copa de la Liga (torneo nuevo de 2026) ni cupos por la Supercopa.

## Colombia: Liga BetPlay y Torneo BetPlay (`datos/json/liga_colombia.json`)

La **Liga BetPlay** (clave `co`) tiene los 20 clubes de 2026 y el **Torneo BetPlay** (clave `co2`, segunda división) tiene 16 clubes.
Los de Primera ya estaban en `clubes_int.json` y se movieron al archivo del país; los de segunda tienen medias orientativas (49 a 57).

* **Apertura 2026**: todos contra todos a una rueda (19 fechas); los ocho primeros disputan cuartos, semifinales y final, todas las series a ida y vuelta.
* **Clausura 2026**: todos contra todos a una rueda (19 fechas); los ocho primeros se dividen en dos cuadrangulares a ida y vuelta (seis fechas), y los
  ganadores de grupo juegan la final a ida y vuelta.
* **Campeón anual del simulador**: partido único en cancha neutral entre los campeones del Apertura y del Clausura. Si el mismo club gana ambos torneos,
  no se juega esa final y queda como campeón anual. Sólo este campeón suma un título anual en `hist_ext_co`; los ganadores semestrales se guardan en Campeones.
* **Descenso**: dos clubes por el promedio de puntos/partidos, con hasta las tres últimas temporadas que el simulador tenga registradas para cada club.
  Los recién ascendidos empiezan a acumular promedio al llegar a Primera. La tabla se ve como **Tabla de descenso · promedio**. Como la partida no trae
  resultados históricos reales 2024-25, una partida nueva comienza acumulando temporadas simuladas; al tercer año ya dispone de tres temporadas completas.
* **Reclasificación y copas**: la tabla **Reclasificación total · cupos internacionales** suma los partidos de los dos semestres y muestra los cupos de
  Libertadores y Sudamericana. El campeón de Copa Colombia ocupa uno de los cuatro cupos de Sudamericana si juega en Primera; si ya tiene cupo por Liga,
  se corre al siguiente club de la reclasificación.
* **Torneo BetPlay**: dos torneos semestrales, cada uno con 15 fechas todos contra todos, cuadrangulares semifinales de seis fechas y final ida/vuelta.
  El ascenso sigue los escenarios de campeones semestrales, reclasificación, Gran Final y repechaje del reglamento 2026. No hay descenso a una tercera división
  porque no está simulada. Columna del Historial: `"Colombia · D2"`.
* Calendario semanal orientativo. Un club figura como "Independiente Yumbo" (ex Atlético Huila), aunque fuentes posteriores de 2026 lo llaman
  "Independiente Valle del Cauca". No hay Superliga.
* `VERSION_ESTADO` subió a 34 por los nuevos acumuladores de reclasificación y promedio; los guardados anteriores no se pueden cargar.

## Copa Chile (`copas/chile.py`, `ui/ui_copa_chile.py`, `datos/json/copa_chile.json`)

Copa nacional de Chile (`clave` `copa_cl`), 32 clubes: los 16 de la Liga de Primera y los 16 de la Primera B (la Segunda División Profesional
queda afuera, como en 2026). Se sortea al armar la temporada, después de las dos ligas, y se juega los miércoles.

* **Fase de grupos**: 8 grupos de 4 (dos de Primera y dos de B), Zona Norte (A a D) y Zona Sur (E a H). Los clubes se ordenan de norte a sur
  con la lista de `copa_chile.json` (si un club nuevo no está, va al final): la mitad más norteña de cada división forma la Zona Norte y dentro
  de cada zona se sortea quién va con quién. Pasan los 2 primeros.
* **Octavos, cuartos y semifinales** a ida y vuelta (penales si el global empata); **final** única en cancha neutral. Octavos: 1° contra 2° de
  otro grupo (A1-B2, C1-D2, E1-F2, G1-H2 y B1-A2, D1-C2, F1-E2, H1-G2); desde ahí el cuadro es fijo.
* **Cupo**: el campeón tiene el Chile 4 (Libertadores · Fase 2) si juega en Primera; si ya clasificó por la liga, sigue la tabla
  (`CUPOS_COPA["Chile"]` en `copas/conmebol.py`). La liga reparte entonces 2 a grupos, 1 a la Fase 2 y 4 a la Sudamericana.
* Simplificaciones: en el grupo los dos de la B juegan entre sí a ida y vuelta (fechas 1 y 2, febrero) y cada uno de Primera juega a ida y
  vuelta contra cada uno de la B (fechas 3 a 6, desde junio); los dos de Primera no se enfrentan (10 partidos por grupo). Es una lectura del
  calendario publicado, no del reglamento. En el reglamento real el campeón juega un partido contra el 3° de la liga por ese cupo y, si
  pierde, va a la Sudamericana; acá el cupo es directo. La Supercopa de Chile está más abajo.
* Palmarés: `hist_copa_cl` en `palmares_cl.json` (opcional). Logo: clave `"Copa Chile"` en `logos.json` (opcional).
* `VERSION_ESTADO` subió a 30 (nueva copa en el estado): las partidas guardadas con la versión anterior ya no se cargan.

## Qué falta (próximos pasos)

* **Brasil** (`datos/json/liga_brasil.json`): Série A y Série B de 20 clubes, todos contra todos a doble rueda; bajan y suben 4 (la C y la D, más abajo). La A arranca el 31/1 y la B el 28/3 (semanal, sin copiar fechas reales). Los clubes de la B que no tenían datos (Ceará, Botafogo-SP, Vila Nova, etc.) van con medias orientativas y sin escudo. Sin Copa do Brasil ni estaduales.
* **Supercopa Uruguaya** (campeón vs. ganador del Intermedio): sin simular.
* En la primera temporada de la partida las copas siguen armándose con el sorteo ponderado por media: todavía no hay tabla.
* Palmarés histórico real: las ligas del exterior sólo cuentan las temporadas simuladas.
* Modo Manager: sólo se dirigen clubes argentinos; las ligas del exterior se juegan solas con el calendario.
* Se guarda en el `.afa` (subió `VERSION_ESTADO` a 22: las partidas guardadas con la versión anterior ya no se cargan).

## Primera Amateur (tercera división de Uruguay)

`datos/json/liga_uruguay.json` trae `tercera` (20 clubes con nombre, media y escudo) y `tercera_liga` (`nombre` "Primera Amateur",
`formato` `uruguay_amateur`, `ascensos`, `descensos` y `calendario`). `datos/ligas_ext.py` suma una tercera liga (`clave` + "3",
`divisional` 3, `superior` = la segunda). Sin `tercera_liga`, la tercera sigue siendo una lista de clubes que no se juega y de la que
suben al azar (`LigaExterior._sortear_tercera`).

Formato (`ligas/uruguay_amateur.py`, propio del simulador: el real de la AUF es otro):

* **Fase regular**: dos series de 10 clubes (se sortean cada temporada), todos contra todos a doble rueda (18 fechas, domingos desde el 5/4).
* **Fase final**: pasan los 4 primeros de cada serie. Cuartos (1° contra 4° y 2° contra 3° de la otra serie), semifinales y final,
  todo a partido único con penales si empatan. Local el mejor ubicado de la tabla general de la fase regular; la final es en cancha neutral.
* **Campeón**: el ganador de la final. **Ascienden a la Segunda** el campeón y el subcampeón. No hay descenso.
* **Con la Segunda**: bajan sus 2 últimos de la Tabla Anual y ocupan los lugares de los 2 que suben, así la Primera Amateur sigue con
  20 clubes (`LigaExterior.cerrar` de la primera). Lo último que pasó vive en `S["ext_mov3"]["Uruguay"]` (Historial) y la lista, en
  `S["ext_clubes"]["Uruguay|3"]`. Su columna del Historial es `"Uruguay · D3"`.
* **Interfaz**: pestaña Ligas con Serie A, Serie B y **Llaves** (cuadro de cuartos a la final, como el de la Libertadores).
* Sus clubes también son los **amateurs de la Copa AUF Uruguay**. Los nombres y las medias (35 a 49) son orientativos: hay que revisarlos.
* Se guarda en el `.afa` (subió `VERSION_ESTADO` a 25: las partidas guardadas con la versión anterior ya no se cargan).

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
* **Llaves**: la pestaña Llaves de la copa dibuja el cuadro de octavos a la final (como el de la Libertadores) y, debajo, los
  dieciseisavos de profesionales y de amateurs (`copas/uruguay.py`, `llaves`; `cuadro_llaves_html` en `ui/vista/cuadros.py`).
* **Logo**: `datos/json/logos.json` (clave "Copa AUF Uruguay"); se ve en la cabecera de la copa y en la pestaña.
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

## Copa do Brasil (`copas/brasil.py`, `copas/registro.py::CopaBrasil`, `ui/ui_copa_brasil.py`)

Formato 2026 de la CBF: 126 clubes y nueve fases. Primera (28 clubes → 14), segunda (14 + 74 = 88 → 44), tercera (44 + 4 = 48 → 24)
y cuarta (24 → 12) a partido único; quinta (12 + los 20 de la Série A = 32 → 16), octavos, cuartos y semifinales a ida y vuelta
(global empatado: penales); final única en cancha neutral.

Simplificaciones: no hay estaduales, Copa Verde ni Copa do Nordeste. Los 106 clubes que no son de la Série A salen de la B, la C y
la D (los de mejor media; los 28 peores abren en la primera fase). A la tercera fase entran los campeones de la C y de la D del
año anterior y los dos de mejor media que quedan. Cruces al azar; local el de menor media (en las series, la ida).

Cupos internacionales: campeón → grupos de la Libertadores; subcampeón → Fase 2. La Série A queda con 4 a grupos + 1 a Fase 2 y 6 a
Sudamericana (6° al 11°). Si el campeón o el subcampeón ya clasificaron por la liga, el cupo pasa al que sigue en la tabla
(`copas/conmebol.py`: `CUPOS_COPA`, `cupos_liga`, `primero=` en `_sortear_pais`). Brasil sigue teniendo 7 cupos en la Libertadores.

Estado: `S["copa_br"]`; al cerrar escribe `S["ext_copa"]["Brasil"]` y `S["ext_copa_sub"]["Brasil"]`. `VERSION_ESTADO` subió a 28
(las partidas guardadas anteriores no cargan).

## Copa Colombia (`copas/colombia.py`, `ui/ui_copa_colombia.py`)

Copa nacional de Colombia (`clave` `copa_co`, clase `CopaColombia` en `copas/registro.py`), 36 clubes: los 20 de la Liga BetPlay y los 16 del Torneo BetPlay.
Formato 2026 de la Dimayor:

* **Fase 1A (grupos)**: 20 clubes (12 de la Liga y 8 del Torneo), cuatro grupos de cinco (tres de la Liga y dos del Torneo), una sola rueda de cuatro
  partidos por club (cinco fechas, cada uno descansa una). Pasan los 2 primeros de cada grupo.
* **Fase 1B (series)**: los otros 16 (8 de la Liga y 8 del Torneo), ocho series a ida y vuelta de un club de la Liga contra uno del Torneo; el del Torneo es
  local en la vuelta. Pasan 8.
* **Octavos y cuartos**: partido único (cambio de la Dimayor de agosto de 2026). Si se enfrentan las dos divisiones es local el del Torneo; si no, el de mayor media.
* **Semifinales y final**: ida y vuelta, sin alargue (penales si el global empata). Palmarés: `hist_copa_co` en `palmares_co.json`.
* **Cupo internacional**: el campeón va a la Sudamericana (Fase 1) si juega en Primera; si ya clasificó por la liga, el cupo sigue por la tabla
  (`COPA_A_SUD` en `copas/conmebol.py`).
* Clasificación a la Copa: el sorteo queda pendiente hasta que terminen el Apertura de Primera y el Torneo BetPlay I. Los ocho primeros del Apertura y los
  ocho clasificados a cuadrangulares del Torneo entran a la Fase 1B; los otros 12 de Primera y ocho del Torneo juegan la Fase 1A.
* Simplificaciones: los grupos se sortean sin zonificación geográfica y las series/octavos se sortean al azar; desde octavos el cuadro es fijo y el 1° y el 2°
  de un mismo grupo quedan en mitades distintas. La localía en cruces de la misma división se aproxima por media, ya que el simulador no conserva una tabla
  independiente del Apertura para todos esos cruces. Los días son miércoles: fase de grupos desde agosto, series en septiembre, octavos en octubre, cuartos
  en octubre, semifinales en noviembre y final entre noviembre y diciembre.
* Palmarés cargado: 22 títulos (1951 a 2025), con las ediciones anteriores a 2008 que la Dimayor pone en duda; verificar contra la Dimayor.

## Estaduales de Brasil (`copas/estaduales.py`, `Estaduales` en `copas/registro.py`, `ui/ui_estaduales.py`, `datos/json/estaduales.json`)

27 campeonatos estaduales (Paulista, Carioca, Mineiro, Gaúcho, Paranaense, Catarinense, Baiano, Pernambucano, Cearense, Goiano, Paraense y los de los demás estados), siempre activos (sin interruptor). Motor derivado de los Regionales argentinos; mismo estado (`S["estaduales"]`).

* **Quién juega**: los clubes de la Série A a la D, cada uno en el torneo de su estado (`clubes` del JSON: club -> estado; los 156 clubes están cargados). Cada torneo tiene un tamaño `tam` (SP 16, RJ/MG/RS/PR 12, SC/BA/PE/CE/GO/PA/MT/DF 10, el resto 8). Entran primero los de la división más alta y, dentro de ella, los de mayor media. Si el estado tiene de más, quedan afuera los de peor división y media (SP: Noroeste, Velo Clube y Água Santa); si tiene de menos, se completa con **clubes complementarios** (`extras` del JSON: media fija ±1,5 por temporada, sin escudo, no juegan ninguna liga nacional ni suben ni bajan).
* **Formato**: una tabla todos contra todos a una rueda; el Paulistão tiene 4 grupos de 4 y cada club juega una vez contra los de los otros grupos (`cruzado`). Llave de 8 (cuartos, semifinales y final: SP, MG, RS, PR) o de 4 (semifinales y final: el resto), a partido único con penales; final en cancha neutral.
* **Calendario**: desde el 10 de enero, una ronda cada 4 días (el Paulistão termina el 19/3, antes de la Série B y la C). Columna del Historial: `"Estaduales"` (un dict {torneo: campeón} por temporada) y palmarés por estado en un desplegable del Historial de Brasil.
* **Simplificaciones a revisar**: el real tiene formatos propios (Taça Guanabara/Taça Rio, finales a ida y vuelta, fases por grupos distintas, series estaduales de ascenso); acá la fase de grupos es una sola y la llave es a partido único. Los clubes complementarios y las medias (41 a 48) son orientativos. Mapeo de estados a revisar: **Decisão** (puesto en Paraíba, sin confirmar). **No dan cupos** a la Copa do Brasil, Copa Verde ni Copa do Nordeste, ni hay palmarés histórico de cada estadual (sólo cuentan las temporadas simuladas).
* `VERSION_ESTADO` subió a 35 (nueva copa en el estado, sobre el 34 de la Colombia con reclasificación): las partidas guardadas con la versión anterior ya no se cargan.
