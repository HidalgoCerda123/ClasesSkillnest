BANCO_DE_PROMPT = [
    {
            "nombre": "estimar_respuesta_y_tiempo",
            "system_instruction": (
                "Responde unicamente con JSON con las claves 'respuesta' (texto directo), "
                "'tiempo_estimado' (ej.'Inmediato','5-10 min'),'nivel_complejidad' "
                "('Bajo','Medio','Alto') y 'requiere_soporte_humano' (boolean)."
            ),
            "ejemplo_usuario": "¿Como solicito el reembolso de un pedido cancelado?",
            "claves_esperadas": ["respuesta", "tiempo_estimado", "nivel_complejidad", "requiere_soporte_humano"],
            "response_schema": {
                "type": "OBJECT",
                "properties": {
                    "respuesta": {"type": "STRING"},
                    "tiempo_estimado": {"type": "STRING"},
                    "nivel_complejidad": {"type": "STRING"},
                    "requiere_soporte_humano": {"type": "BOOLEAN"}
                },
                "required": ["respuesta", "tiempo_estimado", "nivel_complejidad", "requiere_soporte_humano"]
            }
        },
        {
            "nombre": "extraer_entidades",
            "system_instruction": (
                "Extrae del texto las personas, los lugares y las organizaciones "
                "que se mencionen. Responde unicamente con JSON con las claves 'personas', 'lugares' y 'organizaciones', cada una conteniendo una lista de textos (vacía si no hay elementos)."
            ),
            "ejemplo_usuario": (
                "Elena de Troya y Juana de arco viajaron de Roma a Grecia para reunirse con la guerrilla"
            ),
            "claves_esperadas": ["personas", "lugares", "organizaciones"],
            "response_schema": {
                "type": "OBJECT",
                "properties": {
                    "personas": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "lugares": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "organizaciones": {"type": "ARRAY", "items": {"type": "STRING"}}
                },
                "required": ["personas", "lugares", "organizaciones"]
            }
        },
        {
            "nombre": "analizar_sentimiento",
            "system_instruction": (
                "Analiza el sentimiento del texto del usuario. Responde unicamente con JSON con las claves "
                "'sentimiento' ('Positivo','Neutro','Negativo'), 'intensidad' (numero entre 0 y 1) "
                "y 'justificacion' (una frase corta)."
            ),
            "ejemplo_usuario": "El servicio fue pesimo, esperé una hora y nadie me atendió.",
            "claves_esperadas": ["sentimiento", "intensidad", "justificacion"],
            "response_schema": {
                "type": "OBJECT",
                "properties": {
                    "sentimiento": {"type": "STRING"},
                    "intensidad": {"type": "NUMBER"},
                    "justificacion": {"type": "STRING"}
                },
                "required": ["sentimiento", "intensidad", "justificacion"]
            }
        },
        {
            "nombre": "resumir_en_puntos",
            "system_instruction": (
                "Resume el texto del usuario. Responde unicamente con JSON con las claves 'titulo' "
                "(maximo 8 palabras), 'puntos_clave' (lista de 3 a 5 textos breves) "
                "y 'palabras_originales' (cantidad aproximada de palabras del texto original)."
            ),
            "ejemplo_usuario": (
                "La empresa anunció que abrirá tres nuevas sucursales en el norte del país durante el próximo año. "
                "La inversión total será de 2 millones de dólares y se crearán cerca de 150 empleos. "
                "Además, planean lanzar una aplicación móvil para pedidos en línea."
            ),
            "claves_esperadas": ["titulo", "puntos_clave", "palabras_originales"],
            "response_schema": {
                "type": "OBJECT",
                "properties": {
                    "titulo": {"type": "STRING"},
                    "puntos_clave": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "palabras_originales": {"type": "NUMBER"}
                },
                "required": ["titulo", "puntos_clave", "palabras_originales"]
            }
        },
        {
            "nombre": "clasificar_ticket_soporte",
            "system_instruction": (
                "Clasifica el ticket de soporte del usuario. Responde unicamente con JSON con las claves "
                "'area' ('Facturacion','Tecnico','Envios','Otro'), 'prioridad' ('Baja','Media','Alta') "
                "y 'requiere_escalamiento' (boolean)."
            ),
            "ejemplo_usuario": "Me cobraron dos veces la suscripción este mes y necesito que lo corrijan hoy.",
            "claves_esperadas": ["area", "prioridad", "requiere_escalamiento"],
            "response_schema": {
                "type": "OBJECT",
                "properties": {
                    "area": {"type": "STRING"},
                    "prioridad": {"type": "STRING"},
                    "requiere_escalamiento": {"type": "BOOLEAN"}
                },
                "required": ["area", "prioridad", "requiere_escalamiento"]
            }
        }
]