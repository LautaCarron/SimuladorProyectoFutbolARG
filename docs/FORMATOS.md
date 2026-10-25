# Formatos de las competencias

Resumen de cómo funciona cada competencia del simulador (antes vivía como docstring de `simuladorafa.py`).

```text
PRIMERA DIVISIÓN (30 equipos) · formato "actual" (en el Modo dios también hay torneo anual a una rueda,
anual ida y vuelta, y Apertura y Clausura con llaves: ver ligas/primera.py y ligas/apertura_clausura.py)
  * Fase 1: todos contra todos, 29 fechas (una vuelta).
  * Fase 2: tres zonas de 10 según la tabla (Campeonato 1-10, Intermedia 11-20,
    Descenso 21-30), 9 fechas dentro de la zona con localía invertida.
  * Destinos: 1-5 Libertadores · 6-8 Sudamericana · 11 Fase previa Libertadores
    · 12-13 Sudamericana · 28-30 descienden · 27° juega la PROMOCIÓN.

PRIMERA NACIONAL (36 equipos)
  * Fase 1: 2 zonas de 18 (A y B), una sola rueda (17 fechas) + 8 fechas
    interzonales cruzadas entre ambas zonas antes de pasar a la fase 2.
  * Se reparten en 3 zonas de 12 y CONSERVAN los puntos acumulados:
      Campeonato: 1°-6° de cada zona · Intermedia: 7°-12° de cada zona
      Descenso: 13°-18° de cada zona.  Una sola rueda en cada una.
  * Campeonato: 1° campeón + ascenso · 2° ascenso · 3°-4° a cuartos del reducido
    · 5°-12° a octavos.   Intermedia: 1°-4° a octavos.
    Descenso: los 6 últimos descienden (al Federal A o Primera B según afiliación).
  * Reducido (14 equipos): a partido único. Localía y ventaja para el mejor
    ubicado. Final en cancha neutral con penales.
  * El campeón del reducido asciende. El perdedor de la final juega la PROMOCIÓN
    contra el 27° de Primera.

FEDERAL A (Equipos indirectamente afiliados)
  * Fase 1: 5 grupos por cercanía geográfica (Norte, Centro, Buenos Aires,
    Patagonia y Cuyo), ida y vuelta.
  * Fase 2: Pasan los 4 primeros de cada grupo a la Zona Campeonato (20 equipos).
    El resto a Zona Descenso. Puntos de vuelta a 0, una sola rueda.
  * Ascensos: 1°, 2° y 3° de la Zona Campeonato ascienden directo.
  * Reducido: Del 4° al 8° juegan eliminatorias a partido único por el cuarto
    ascenso a la Primera Nacional.
  * Descenso: los 6 últimos de la Zona Descenso bajan al Regional Amateur (a la
    región de su provincia). Si hay igualdad en puntos en el límite, desempate.

PRIMERA B (Equipos directamente afiliados)
  * Formato de liga tradicional: Todos contra todos, ida y vuelta.
  * Ascensos: Campeón y subcampeón (1° y 2°) ascienden de forma directa a la 
    Primera Nacional.
  * del 18 al ultimo bajan a la Primera C, si el campeonato son menos de
    18 equipos no hay descensos.

PRIMERA C (Equipos directamente afiliados)
  * Formato de liga tradicional: Todos contra todos, ida y vuelta.
  * Ascensos: Campeón y subcampeón (1° y 2°) ascienden de forma directa a la 
    Primera B.

PROMOCIONAL AMATEUR y REGIONAL AMATEUR
  * Promocional Amateur: liga todos contra todos con la misma mecánica que la Primera B y la Primera C
    (ligas/simples.py).
  * Regional Amateur: clubes repartidos en 12 regiones, con dos fases y una final por el ascenso
    (ligas/regional.py y datos/datos_regional.py).
      - Fase 1 · Subgrupos: cada región se divide en subgrupos de unos 5 clubes (entre 3 y 7, hasta 8 subgrupos por
        región) armados por cercanía: se juntan los clubes de la misma liga y, si no alcanza, los de la misma
        provincia. Todos contra todos, ida y vuelta. Los subgrupos se sortean de nuevo cada temporada.
      - Fase 2 · Zona regional: los 2 mejores de cada subgrupo pasan a la zona de su región (hasta 16 clubes), todos
        contra todos, ida y vuelta, con la tabla en cero. Una región chica (menos de 8 clubes) no se divide y juega
        directo la zona con todos sus clubes.
      - El título de la zona nunca se define por diferencia de gol: si el 1° puesto está igualado en puntos hay un
        desempate (partido único en cancha neutral, liguilla si son 3 o más, penales si empatan). Su ganador es el
        campeón regional.
      - Las finales por el ascenso (ida y vuelta) enfrentan a los campeones de las dos regiones de cada par.
  * Federal B: categoría opcional que se crea desde el Modo dios entre el Federal A y el Regional Amateur
    (ligas/federal_b.py).

COPAS
  * Copa Argentina y Supercopa Argentina (copas/argentina.py).
  * Libertadores, Sudamericana y Recopa de la CONMEBOL (copas/conmebol.py).
  * Mundial de Clubes, cada 4 temporadas (copas/mundial.py).
  * Las copas por rondas se registran en copas/registro.py; el calendario de todo está en motor/calendario.py.

PARTIDAS GUARDADAS: la pestaña "Partidas" (al lado de Historial) descarga la partida en un archivo .afa y la carga
de nuevo (ui/ui_guardado.py y motor/guardado.py). También se puede cargar antes de empezar a simular, desde la
pantalla de inicio ("Cargar partida").

MODOS: Simulador, Manager (ui/manager.py, motor/ofertas.py, motor/eventos.py, motor/relaciones.py) y Modo dios
(ui/dios.py). Las pestañas de la interfaz están en ui/ (las que repiten el nombre de un módulo de lógica llevan
el prefijo ui_: ui/ui_conmebol.py, ui/ui_primera.py, etc.) y las piezas compartidas de dibujo en ui/vista/.

Cada equipo tiene una "media interna" (fuerza) que cambia cada temporada.
Los partidos se simulan con goles Poisson y cada equipo tiene una "forma del
día" aleatoria: cuanto mayor es el nivel de sorpresas, más seguido gana el
que tiene menos media.
```
