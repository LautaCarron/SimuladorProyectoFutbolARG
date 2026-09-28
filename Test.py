 # === MODO TEST: FORZAR RESULTADOS A DEDO ===
    if S_LIGA["fecha"] == S_LIGA["total"] and not ya_se_jugo:
        
        # TEST 1: Cuadrangular por el campeonato (Descomentá estas 3 líneas)
        # for i in [0, 1, 2, 3]:
        #     S_LIGA["g"][ids[i]] = 30; S_LIGA["e"][ids[i]] = 0
            

        # TEST 2: Triangular por el segundo ascenso (1ro cortado, 2do-3ro-4to empatados)
        # S_LIGA["g"][ids[0]] = 35; S_LIGA["e"][ids[0]] = 0
        # for i in [1, 2, 3]:
        #     S_LIGA["g"][ids[i]] = 25; S_LIGA["e"][ids[i]] = 0
            

        # TEST 3: Empate por el descenso (17mo y 18vo con mismos puntos)
        # if nombre_liga == "Primera B" and len(ids) >= 18:
            # # Igualamos las estadísticas del 18° exactamente con las del 17°
            # S_LIGA["g"][ids[17]] = S_LIGA["g"][ids[16]]
            # S_LIGA["e"][ids[17]] = S_LIGA["e"][ids[16]]           
            # # Hundimos a los que están del 19° para abajo para que no estorben
            # for i in range(18, len(ids)):
            #     S_LIGA["g"][ids[i]] = 0
            #     S_LIGA["e"][ids[i]] = 0


        # TEST 4: Triangular por el campeonato (1ro, 2do y 3ro empatados)
        # for i in [0, 1, 2]:
        #     S_LIGA["g"][ids[i]] = 30; S_LIGA["e"][ids[i]] = 0


        # TEST 5: Triangular por el descenso (16to, 17to y 18vo empatados)
        if nombre_liga == "Primera B" and len(ids) >= 18:
            # Igualamos las estadísticas del 16°, 17° y 18° exactamente entre sí
            S_LIGA["g"][ids[17]] = S_LIGA["g"][ids[16]] = S_LIGA["g"][ids[15]]
            S_LIGA["e"][ids[17]] = S_LIGA["e"][ids[16]] = S_LIGA["e"][ids[15]]
            # Hundimos a los que están del 19° para abajo para que no estorben
            for i in range(18, len(ids)):
                S_LIGA["g"][ids[i]] = 0
                S_LIGA["e"][ids[i]] = 0



        # Refresca la tabla y los puntos en memoria para que el sistema se coma el amague
        df = fn_tabla(S_LIGA)
        pts = df["Pts"].to_numpy()
        ids = df["id"].to_numpy()
    # ===========================================