"""Fachada de compatibilidad: reexporta todo lo que antes vivía en vista.py.

El código se repartió por tema en ui/vista/: css, base, partidos, ficha, fixture, tablas, puente, cuadros,
copas_int, formatos, mi_club y vista_calendario (este último lleva el prefijo para no repetir el nombre de
ui/ui_calendario.py ni de motor/calendario.py). Las pestañas siguen importando de acá, así que no cambian.
"""

from ui.vista.css import (
    CSS,
)
from ui.vista.base import (
    COLOR_ORO,
    COLORES_DESTINO,
    COLORES_ZONA,
    COLORES_B,
    COLORES_F,
    COLOR_COMP,
    esc,
    color_de,
    chip,
    seccion,
    aviso,
    leyenda,
    iniciales,
    crest,
    norm,
    _STOP,
    coincide,
    LEY_ZONAS,
    LEY_DESTINOS,
    LEY_B,
    LEY_F,
    _ISO,
    bandera,
    barra_estado,
)
from ui.vista.partidos import (
    marcador_html,
    tanda_html,
    fila_partido_html,
    lista_equipos_html,
    resultado_para,
)
from ui.vista.ficha import (
    render_ficha,
    ver_equipo,
)
from ui.vista.fixture import (
    render_fecha,
    _mover_fecha,
    vista_fixture,
)
from ui.vista.tablas import (
    ultimos_movs,
    color_mov,
    _COL_NUM,
    _TITULOS,
    _AYUDAS,
    _valor,
    club_link,
    _th,
    tabla_html,
    mostrar_tabla,
    colorear_fase1,
    colorear_destino,
    colorear_b,
    colorear_f,
    colorear_pb,
    colorear_reg,
    colorear_pc,
    colorear_pd,
    rachas,
    card,
    eq_html,
    partido_corto,
    render_movimientos,
)
from ui.vista.puente import (
    _PUENTE_JS,
    _instalar_puente_js,
    _club_elegido,
    puente_clubes,
)
from ui.vista.cuadros import (
    bracket_card,
    bracket_html,
    bracket_html_f,
    _nm_club,
    _fila_final,
    finales_reg_html,
    _kb_card,
    _kb_col,
    _kb_ronda,
    _kb_final,
    _kb,
    cuadro_llave_html,
    cuadro_final_copa_html,
    _ICONO_AVISO,
    avisos_html,
)
from ui.vista.copas_int import (
    _INT_CLAVE,
    _club_int,
    serie_int_html,
    series_int_html,
    grupos_int_html,
    _kb_card_serie,
    cuadro_int_html,
    grupos_mundial_html,
    _kb_card_mundial,
    cuadro_mundial_html,
    ranking_conmebol_html,
)
from ui.vista.vista_calendario import (
    _cal_partidos,
    _cal_rotulo,
    eventos_calendario,
    _cal_res,
    calendario_mes_html,
)
