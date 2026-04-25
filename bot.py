import requests
import time

# ==========================================
# CONFIGURACIÓN — COMPLETA ESTOS 3 VALORES
# ==========================================
TELEGRAM_TOKEN = "8705951702:AAFbjPPtAtnPP2cHQd-K97fWui05F2SKRWs"
CHAT_ID = "811308319"
API_FOOTBALL_KEY = "57959cae9503fbf6f0cdef93dbd0cb5c"

# Ligas a monitorear (puedes agregar o quitar)
LIGAS = [
    39,   # Premier League
    140,  # La Liga (España)
    135,  # Serie A (Italia)
    78,   # Bundesliga (Alemania)
    61,   # Ligue 1 (Francia)
    2,    # Champions League
    128,  # Liga Chilena (Primera División)
]

tarjetas_notificadas = set()

def enviar_telegram(mensaje):
    """Envía un mensaje a tu Telegram"""
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
    """Consulta los partidos que están jugándose ahora"""
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params = {"live": "all"}
    r = requests.get(url, headers=headers, params=params)
    datos = r.json()
    return datos.get("response", [])

def revisar_tarjetas_rojas(partidos):
    """Busca tarjetas rojas nuevas y notifica"""
    for partido in partidos:
        liga_id = partido["league"]["id"]
        if liga_id not in LIGAS:
            continue

        fixture_id = partido["fixture"]["id"]
        equipo_local = partido["teams"]["home"]["name"]
        equipo_visita = partido["teams"]["away"]["name"]
        nombre_liga = partido["league"]["name"]
        pais = partido["league"]["country"]

        eventos = partido.get("events", [])
        for evento in eventos:
            es_tarjeta_roja = (
                evento.get("type") == "Card" and
                evento.get("detail") in ["Red Card", "Second Yellow card"]
            )
            if not es_tarjeta_roja:
                continue

            minuto = evento["time"]["elapsed"]
            jugador = evento["player"]["name"] or "Desconocido"
            equipo = evento["team"]["name"]
            clave = f"{fixture_id}-{jugador}-{minuto}"

            if clave not in tarjetas_notificadas:
                tarjetas_notificadas.add(clave)

                tipo = "🟥 TARJETA ROJA" if evento["detail"] == "Red Card" else "🟨🟥 SEGUNDA AMARILLA"

                mensaje = (
                    f"{tipo}\n\n"
                    f"🏆 {nombre_liga} ({pais})\n"
                    f"⚽ {equipo_local} vs {equipo_visita}\n"
                    f"👤 Jugador: <b>{jugador}</b>\n"
                    f"🏃 Equipo: {equipo}\n"
                    f"⏱️ Minuto: {minuto}'"
                )
                enviar_telegram(mensaje)
                print(f"✅ Notificado: {jugador} ({equipo}) min {minuto}")

def main():
    print("🤖 Bot iniciado. Monitoreando partidos...")
    enviar_telegram("✅ <b>Bot de tarjetas rojas activado</b>\nTe avisaré cada vez que haya una expulsión 🟥")

    while True:
        try:
            print(f"\n🔍 Revisando partidos en vivo...")
            partidos = obtener_partidos_en_vivo()
            print(f"   Partidos encontrados: {len(partidos)}")
            revisar_tarjetas_rojas(partidos)
        except Exception as e:
            print(f"❌ Error: {e}")

        print("⏳ Esperando 60 segundos...")
        time.sleep(60)

if __name__ == "__main__":
    main()