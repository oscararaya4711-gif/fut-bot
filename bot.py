import requests
import time

# ==========================================
# CONFIGURACIÓN — COMPLETA ESTOS 3 VALORES
# ==========================================
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")

# Ligas a monitorear (puedes agregar o quitar)
LIGAS = [
        # ======= EUROPA - PRIMER ORDEN =======
    39,   # Premier League (Inglaterra)
    140,  # La Liga (España)
    135,  # Serie A (Italia)
    78,   # Bundesliga (Alemania)
    61,   # Ligue 1 (Francia)
    2,    # UEFA Champions League
    3,    # UEFA Europa League
    848,  # UEFA Conference League

    # ======= EUROPA - SEGUNDO ORDEN =======
    40,   # Championship (Inglaterra 2ª)
    141,  # Segunda División (España)
    136,  # Serie B (Italia)
    79,   # 2. Bundesliga (Alemania)
    62,   # Ligue 2 (Francia)
    88,   # Eredivisie (Holanda 1ª)
    89,   # Eerste Divisie (Holanda 2ª)
    144,  # Jupiler Pro League (Bélgica)
    207,  # Super League (Suiza)
    208,  # Challenge League (Suiza 2ª)
    113,  # Allsvenskan (Suecia)
    114,  # Superettan (Suecia 2ª)
    103,  # Eliteserien (Noruega)
    104,  # Primera División (Noruega 2ª)
    119,  # Superliga (Dinamarca)
    120,  # 1st Division (Dinamarca 2ª)
    106,  # Ekstraklasa (Polonia)
    107,  # I Liga (Polonia 2ª)
    179,  # Premiership (Escocia)
    180,  # Championship (Escocia 2ª)
    271,  # Fortuna Liga (República Checa)
    345,  # HNL (Croacia)
    218,  # Super Liga (Serbia)
    286,  # Süper Lig (Turquía)
    333,  # Premier League (Austria)
    197,  # Super League (Grecia)
    235,  # Premier Liga (Rusia)
    373,  # Nemzeti Bajnokság (Hungría)
    382,  # Fortuna Liga (Eslovaquia)
    210,  # Primeira Liga (Portugal)
    211,  # Liga Portugal 2 (Portugal 2ª)

    # ======= SUDAMÉRICA =======
    128,  # Primera División (Chile)
    129,  # Primera B (Chile 2ª)
    71,   # Brasileirao Serie A (Brasil)
    72,   # Brasileirao Serie B (Brasil 2ª)
    239,  # Liga Profesional (Argentina)
    240,  # Primera Nacional (Argentina 2ª)
    11,   # Copa Libertadores
    13,   # Copa Sudamericana
    242,  # Primera División (Uruguay)
    281,  # Primera División (Paraguay)
    300,  # Primera División (Bolivia)
    266,  # Liga 1 (Perú)
    314,  # Serie A (Ecuador)
    332,  # Primera División (Colombia)
    253,  # Primera División (Venezuela)

    # ======= NORTEAMÉRICA Y CENTROAMÉRICA =======
    253,  # MLS (Estados Unidos)
    262,  # Liga MX (México)
    263,  # Liga de Expansión (México 2ª)
    164,  # Canadian Premier League (Canadá)
    348,  # Liga Nacional (Honduras)
    286,  # Liga Mayor (Guatemala)
    322,  # Primera División (Costa Rica)
    358,  # LPF (Panamá)
    369,  # Primera División (El Salvador)

    # ======= ASIA =======
    169,  # AFC Champions League
    292,  # Saudi Pro League (Arabia Saudita)
    307,  # Qatar Stars League (Qatar)
    188,  # Pro League (Emiratos Árabes)
    323,  # Persian Gulf Pro League (Irán)
    268,  # J1 League (Japón)
    269,  # J2 League (Japón 2ª)
    292,  # K League 1 (Corea del Sur)
    293,  # K League 2 (Corea del Sur 2ª)
    154,  # Chinese Super League (China)
    296,  # Indian Super League (India)
    334,  # Thailand League 1 (Tailandia)

    # ======= OCEANÍA =======
    188,  # A-League (Australia)
    490,  # New Zealand National League
]

tarjetas_notificadas = set()

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": mensaje,
            "parse_mode": "HTML"
        })
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

def obtener_partidos_en_vivo():
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params = {"live": "all"}
    r = requests.get(url, headers=headers, params=params)
    return r.json().get("response", [])

def revisar_tarjetas_rojas(partidos):
    for partido in partidos:
        liga_id = partido["league"]["id"]
        if liga_id not in LIGAS:
            continue

        fixture_id  = partido["fixture"]["id"]
        equipo_local   = partido["teams"]["home"]["name"]
        equipo_visita  = partido["teams"]["away"]["name"]
        nombre_liga    = partido["league"]["name"]
        pais           = partido["league"]["country"]

        # ⬇️ Resultado actual
        goles_local   = partido["goals"]["home"]
        goles_visita  = partido["goals"]["away"]
        if goles_local  is None: goles_local  = 0
        if goles_visita is None: goles_visita = 0
        marcador = f"{goles_local} - {goles_visita}"

        # Minuto actual del partido
        minuto_actual = partido["fixture"]["status"]["elapsed"] or "?"

        eventos = partido.get("events", [])
        for evento in eventos:
            es_roja = (
                evento.get("type") == "Card" and
                evento.get("detail") in ["Red Card", "Second Yellow card"]
            )
            if not es_roja:
                continue

            minuto_evento = evento["time"]["elapsed"]
            jugador       = evento["player"]["name"] or "Desconocido"
            equipo        = evento["team"]["name"]
            clave         = f"{fixture_id}-{jugador}-{minuto_evento}"

            if clave not in tarjetas_notificadas:
                tarjetas_notificadas.add(clave)

                tipo = "🟥 TARJETA ROJA" if evento["detail"] == "Red Card" else "🟨🟥 SEGUNDA AMARILLA"

                mensaje = (
                    f"{tipo}\n\n"
                    f"🏆 {nombre_liga} ({pais})\n"
                    f"⚽ <b>{equipo_local} {marcador} {equipo_visita}</b>\n"
                    f"⏱️ Minuto: {minuto_evento}'\n"
                    f"👤 Jugador: <b>{jugador}</b>\n"
                    f"🏃 Equipo: {equipo}"
                )
                enviar_telegram(mensaje)
                print(f"✅ Notificado: {jugador} ({equipo}) min {minuto_evento} | {marcador}")

def main():
    print("🤖 Bot iniciado. Monitoreando partidos...")
    enviar_telegram("✅ <b>Bot de tarjetas rojas activado</b>\nTe avisaré cada vez que haya una expulsión 🟥")

    while True:
        try:
            print("🔍 Revisando partidos en vivo...")
            partidos = obtener_partidos_en_vivo()
            print(f"   Partidos encontrados: {len(partidos)}")
            revisar_tarjetas_rojas(partidos)
        except Exception as e:
            print(f"❌ Error: {e}")

        print("⏳ Esperando 60 segundos...")
        time.sleep(60)

if __name__ == "__main__":
    main()
