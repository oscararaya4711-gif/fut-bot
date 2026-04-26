import requests
import time
import os
import json
from datetime import datetime

# ==========================================
# CONFIGURACIÓN
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.environ.get("CHAT_ID")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")

TU_USUARIO_TELEGRAM = "@oaraya555" 
LIMITE_GRATUITO = 10  # Notificaciones diarias para usuarios gratuitos

LIGAS = [

    # ======= UEFA - COMPETICIONES EUROPEAS =======
    2,    # Champions League
    3,    # Europa League
    848,  # Conference League

    # ======= INGLATERRA - 5 DIVISIONES =======
    39,   # Premier League (1ª)
    40,   # Championship (2ª)
    41,   # League One (3ª)
    42,   # League Two (4ª)
    43,   # National League (5ª)

    # ======= ESPAÑA =======
    140,  # La Liga (1ª)
    141,  # Segunda División (2ª)
    142,  # Segunda Federación (3ª)

    # ======= ALEMANIA =======
    78,   # Bundesliga (1ª)
    79,   # 2. Bundesliga (2ª)
    80,   # 3. Liga (3ª)

    # ======= ITALIA =======
    135,  # Serie A (1ª)
    136,  # Serie B (2ª)
    137,  # Serie C (3ª)

    # ======= FRANCIA =======
    61,   # Ligue 1 (1ª)
    62,   # Ligue 2 (2ª)
    63,   # National (3ª)

    # ======= PORTUGAL =======
    94,   # Primeira Liga (1ª)
    95,   # Liga Portugal 2 (2ª)
    96,   # Liga 3 (3ª)

    # ======= HOLANDA =======
    88,   # Eredivisie (1ª)
    89,   # Eerste Divisie (2ª)
    90,   # Derde Divisie (3ª)

    # ======= BÉLGICA =======
    144,  # Jupiler Pro League (1ª)
    145,  # First Amateur (2ª)

    # ======= SUIZA =======
    207,  # Super League (1ª)
    208,  # Challenge League (2ª)
    209,  # Promotion League (3ª)

    # ======= AUSTRIA =======
    116,  # Bundesliga (1ª)
    117,  # 2. Liga (2ª)

    # ======= SUECIA =======
    113,  # Allsvenskan (1ª)
    114,  # Superettan (2ª)
    115,  # Division 1 (3ª)

    # ======= NORUEGA =======
    103,  # Eliteserien (1ª)
    104,  # Primera División (2ª)
    105,  # Segunda División (3ª)

    # ======= DINAMARCA =======
    119,  # Superliga (1ª)
    120,  # 1st Division (2ª)
    121,  # 2nd Division (3ª)

    # ======= ESCOCIA =======
    179,  # Premiership (1ª)
    180,  # Championship (2ª)
    181,  # League One (3ª)

    # ======= POLONIA =======
    106,  # Ekstraklasa (1ª)
    107,  # I Liga (2ª)
    108,  # II Liga (3ª)

    # ======= TURQUÍA =======
    203,  # Süper Lig (1ª)
    204,  # TFF First League (2ª)
    205,  # TFF Second League (3ª)

    # ======= GRECIA =======
    197,  # Super League (1ª)
    198,  # Super League 2 (2ª)

    # ======= RUSIA =======
    235,  # Premier Liga (1ª)
    236,  # FNL (2ª)

    # ======= CROACIA =======
    210,  # HNL (1ª)
    211,  # Prva NL (2ª)

    # ======= SERBIA =======
    286,  # Super Liga (1ª)
    287,  # First League (2ª)

    # ======= REPÚBLICA CHECA =======
    345,  # Czech Liga (1ª)
    346,  # FNL (2ª)

    # ======= HUNGRÍA =======
    373,  # OTP Bank Liga (1ª)
    374,  # Merkantil Bank Liga (2ª)

    # ======= ESLOVAQUIA =======
    382,  # Fortuna Liga (1ª)
    383,  # Segunda División (2ª)

    # ======= RUMANIA =======
    283,  # Liga 1 (1ª)
    284,  # Liga 2 (2ª)

    # ======= UCRANIA =======
    333,  # Premier League (1ª)
    334,  # Persha Liga (2ª)

    # ======= SUDAMÉRICA =======
    11,   # Copa Libertadores
    13,   # Copa Sudamericana
    128,  # Primera División Chile (1ª)
    129,  # Primera B Chile (2ª)
    130,  # Segunda División Chile (3ª)
    71,   # Brasileirao Serie A (1ª)
    72,   # Brasileirao Serie B (2ª)
    73,   # Brasileirao Serie C (3ª)
    239,  # Liga Profesional Argentina (1ª)
    240,  # Primera Nacional Argentina (2ª)
    242,  # Primera División Uruguay (1ª)
    243,  # Segunda División Uruguay (2ª)
    281,  # Primera División Paraguay (1ª)
    282,  # División Intermedia Paraguay (2ª)
    266,  # Liga 1 Perú (1ª)
    267,  # Liga 2 Perú (2ª)
    314,  # Serie A Ecuador (1ª)
    315,  # Serie B Ecuador (2ª)
    332,  # Primera A Colombia (1ª)
    334,  # Primera B Colombia (2ª)
    300,  # División Profesional Bolivia (1ª)

    # ======= NORTEAMÉRICA =======
    253,  # MLS (1ª)
    254,  # USL Championship (2ª)
    262,  # Liga MX (1ª)
    263,  # Liga de Expansión MX (2ª)
    164,  # Canadian Premier League

    # ======= ASIA =======
    169,  # AFC Champions League
    292,  # Saudi Pro League
    307,  # Qatar Stars League
    268,  # J1 League Japón (1ª)
    269,  # J2 League Japón (2ª)
    270,  # J3 League Japón (3ª)
    293,  # K League 1 Corea (1ª)
    294,  # K League 2 Corea (2ª)
    154,  # Chinese Super League

    # ======= OCEANÍA =======
    188,  # A-League Australia
]

tarjetas_notificadas = set()
ultimo_update_id = 0

# ==========================================
# BASE DE DATOS - MONGODB
# ==========================================
from pymongo import MongoClient

MONGO_URL = os.environ.get("MONGO_URL")
cliente_mongo = MongoClient(MONGO_URL)
db = cliente_mongo["botfutbol"]
coleccion_usuarios = db["usuarios"]

def cargar_usuarios():
    """Carga todos los usuarios desde MongoDB"""
    usuarios = {}
    for u in coleccion_usuarios.find():
        chat_id = u["chat_id"]
        u.pop("_id", None)
        usuarios[chat_id] = u
    return usuarios

def guardar_usuario(chat_id, datos):
    """Guarda o actualiza un usuario en MongoDB"""
    coleccion_usuarios.update_one(
        {"chat_id": chat_id},
        {"$set": datos},
        upsert=True
    )

def guardar_usuarios(usuarios):
    """Guarda todos los usuarios (compatibilidad)"""
    for chat_id, datos in usuarios.items():
        datos["chat_id"] = chat_id
        guardar_usuario(chat_id, datos)

def registrar_usuario(chat_id, nombre, username):
    chat_id = str(chat_id)
    hoy = datetime.now().strftime("%Y-%m-%d")
    existe = coleccion_usuarios.find_one({"chat_id": chat_id})

    if not existe:
        datos = {
            "chat_id": chat_id,
            "nombre": nombre,
            "username": username or "sin_username",
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "plan": "gratuito",
            "activo": True,
            "pausado": False,
            "notificaciones_recibidas": 0,
            "notificaciones_hoy": 0,
            "ultima_actividad": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "fecha_conteo": hoy,
        }
        guardar_usuario(chat_id, datos)
        enviar_mensaje(
            ADMIN_CHAT_ID,
            f"👤 <b>Nuevo usuario registrado</b>\n\n"
            f"Nombre: {nombre}\n"
            f"Username: @{username or 'sin_username'}\n"
            f"ID: {chat_id}\n"
            f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        return True
    else:
        coleccion_usuarios.update_one(
            {"chat_id": chat_id},
            {"$set": {
                "ultima_actividad": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "nombre": nombre
            }}
        )
        return False
            
def resetear_conteo_si_es_nuevo_dia(chat_id, usuarios):
    """Resetea el contador diario si cambió el día"""
    hoy = datetime.now().strftime("%Y-%m-%d")
    if usuarios[chat_id].get("fecha_conteo") != hoy:
        usuarios[chat_id]["notificaciones_hoy"] = 0
        usuarios[chat_id]["fecha_conteo"] = hoy
    return usuarios

def puede_recibir_notificacion(chat_id):
    """Verifica si el usuario puede recibir más notificaciones hoy"""
    usuarios = cargar_usuarios()
    chat_id = str(chat_id)

    if chat_id not in usuarios:
        return False

    # Admin y premium siempre pueden
    if usuarios[chat_id].get("plan") == "premium" or chat_id == str(ADMIN_CHAT_ID):
        return True

    # Resetear si es nuevo día
    usuarios = resetear_conteo_si_es_nuevo_dia(chat_id, usuarios)
    guardar_usuarios(usuarios)

    return usuarios[chat_id]["notificaciones_hoy"] < LIMITE_GRATUITO

def sumar_notificacion(chat_id, usuarios):
    chat_id = str(chat_id)
    usuarios[chat_id]["notificaciones_recibidas"] = usuarios[chat_id].get("notificaciones_recibidas", 0) + 1
    usuarios[chat_id]["notificaciones_hoy"] = usuarios[chat_id].get("notificaciones_hoy", 0) + 1
    return usuarios

def es_admin(chat_id):
    return str(chat_id) == str(ADMIN_CHAT_ID)

# ==========================================
# TELEGRAM
# ==========================================
def enviar_mensaje(chat_id, mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "HTML"
        })
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

def notificar_todos(mensaje):
    usuarios = cargar_usuarios()
    hoy = datetime.now().strftime("%Y-%m-%d")

    for chat_id, datos in usuarios.items():
        if not datos.get("activo") or datos.get("pausado"):
            continue

        # Resetear conteo si es nuevo día
        usuarios = resetear_conteo_si_es_nuevo_dia(chat_id, usuarios)
        es_premium = datos.get("plan") == "premium" or chat_id == str(ADMIN_CHAT_ID)
        notifs_hoy = usuarios[chat_id].get("notificaciones_hoy", 0)

        if es_premium:
            # Premium: recibe todo sin límite
            enviar_mensaje(chat_id, mensaje)
            usuarios = sumar_notificacion(chat_id, usuarios)

        elif notifs_hoy < LIMITE_GRATUITO:
            # Gratuito con cupo disponible
            restantes = LIMITE_GRATUITO - notifs_hoy - 1
            enviar_mensaje(chat_id, mensaje)
            usuarios = sumar_notificacion(chat_id, usuarios)

            # Aviso cuando le queda solo 1
            if restantes == 1:
                enviar_mensaje(chat_id,
                    f"⚠️ Te queda <b>1 notificación gratuita</b> por hoy.\n\n"
                    f"¿Quieres recibir alertas ilimitadas? Contáctanos:\n"
                    f"👉 {TU_USUARIO_TELEGRAM}"
                )
            # Aviso cuando llega al límite
            elif restantes == 0:
                enviar_mensaje(chat_id,
                    f"🔒 <b>Límite diario alcanzado</b>\n\n"
                    f"Los usuarios gratuitos reciben {LIMITE_GRATUITO} alertas por día.\n\n"
                    f"Para recibir alertas <b>ilimitadas</b>, actualiza a Premium:\n"
                    f"👉 {TU_USUARIO_TELEGRAM}"
                )
        else:
            # Ya superó el límite, no recibe nada
            print(f"⛔ Usuario {chat_id} alcanzó límite gratuito hoy")

    guardar_usuarios(usuarios)

# ==========================================
# COMANDOS
# ==========================================
def manejar_comando(chat_id, texto, nombre, username):
    usuarios = cargar_usuarios()
    chat_id_str = str(chat_id)
    texto = texto.strip().lower()

    if texto == "/start":
        es_nuevo = registrar_usuario(chat_id, nombre, username)
        if es_nuevo:
            enviar_mensaje(chat_id,
                f"👋 ¡Hola <b>{nombre}</b>! Bienvenido al bot de tarjetas rojas 🟥\n\n"
                f"Recibirás alertas en tiempo real de expulsiones en las principales ligas del mundo.\n\n"
                f"🆓 <b>Plan gratuito:</b> {LIMITE_GRATUITO} alertas por día\n"
                f"⭐ <b>Plan premium:</b> Alertas ilimitadas\n\n"
                f"Para más info sobre Premium:\n"
                f"👉 {TU_USUARIO_TELEGRAM}\n\n"
                f"<b>Comandos:</b>\n"
                f"/estado — Ver tu plan y notificaciones de hoy\n"
                f"/pausar — Pausar notificaciones\n"
                f"/reanudar — Reanudar notificaciones\n"
                f"/premium — Info sobre plan premium"
            )
        else:
            enviar_mensaje(chat_id, f"👋 ¡Hola de nuevo <b>{nombre}</b>! Escribe /estado para ver tu plan.")

    elif texto == "/ayuda":
        enviar_mensaje(chat_id,
            "📋 <b>Comandos disponibles:</b>\n\n"
            "/estado — Ver tu plan y alertas de hoy\n"
            "/pausar — Pausar notificaciones\n"
            "/reanudar — Reanudar notificaciones\n"
            f"/premium — Info sobre plan premium\n"
            f"/ayuda — Ver esta lista"
        )

    elif texto == "/premium":
        enviar_mensaje(chat_id,
            f"⭐ <b>Plan Premium</b>\n\n"
            f"✅ Alertas ilimitadas cada día\n"
            f"✅ Sin interrupciones\n"
            f"✅ Todas las ligas del mundo\n"
            f"✅ Tarjetas rojas + segundas amarillas\n\n"
            f"Para contratar o consultar precio:\n"
            f"👉 {TU_USUARIO_TELEGRAM}"
        )

    elif texto == "/pausar":
        if chat_id_str in usuarios:
            usuarios[chat_id_str]["pausado"] = True
            guardar_usuarios(usuarios)
        enviar_mensaje(chat_id, "⏸️ Notificaciones pausadas. Escribe /reanudar cuando quieras volver.")

    elif texto == "/reanudar":
        if chat_id_str in usuarios:
            usuarios[chat_id_str]["pausado"] = False
            guardar_usuarios(usuarios)
        enviar_mensaje(chat_id, "▶️ ¡Notificaciones reactivadas! 🟥")

    elif texto == "/estado":
        u = usuarios.get(chat_id_str, {})
        pausado   = "⏸️ Pausado" if u.get("pausado") else "▶️ Activo"
        plan      = "⭐ Premium" if u.get("plan") == "premium" else "🆓 Gratuito"
        hoy       = u.get("notificaciones_hoy", 0)
        total     = u.get("notificaciones_recibidas", 0)
        es_prem   = u.get("plan") == "premium" or es_admin(chat_id)
        limite    = "∞" if es_prem else f"{hoy}/{LIMITE_GRATUITO}"

        enviar_mensaje(chat_id,
            f"📊 <b>Tu estado:</b>\n\n"
            f"Estado: {pausado}\n"
            f"Plan: {plan}\n"
            f"Alertas hoy: {limite}\n"
            f"Total recibidas: {total}\n"
            f"Miembro desde: {u.get('fecha_registro', 'desconocido')}\n\n"
            + ("" if es_prem else
            f"¿Quieres alertas ilimitadas?\n"
            f"👉 @oaraya555")
        )

    # --- Solo ADMIN ---
    elif texto == "/usuarios" and es_admin(chat_id):
        usuarios = cargar_usuarios()
        total   = len(usuarios)
        activos = sum(1 for u in usuarios.values() if u.get("activo") and not u.get("pausado"))
        pausados = sum(1 for u in usuarios.values() if u.get("pausado"))
        premium = sum(1 for u in usuarios.values() if u.get("plan") == "premium")
        enviar_mensaje(chat_id,
            f"📊 <b>Estadísticas:</b>\n\n"
            f"👥 Total usuarios: {total}\n"
            f"▶️ Activos: {activos}\n"
            f"⏸️ Pausados: {pausados}\n"
            f"⭐ Premium: {premium}\n"
            f"🆓 Gratuitos: {total - premium}"
        )

    elif texto == "/lista" and es_admin(chat_id):
        if not usuarios:
            enviar_mensaje(chat_id, "No hay usuarios aún.")
            return
        msg = "👥 <b>Lista de usuarios:</b>\n\n"
        for uid, u in usuarios.items():
            plan = "⭐" if u.get("plan") == "premium" else "🆓"
            msg += f"{plan} {u['nombre']} (@{u['username']}) — <code>{uid}</code>\n"
        enviar_mensaje(chat_id, msg)

    elif texto.startswith("/premium ") and es_admin(chat_id):
        target_id = texto.split(" ")[1]
        usuarios = cargar_usuarios()
        if target_id in usuarios:
            usuarios[target_id]["plan"] = "premium"
            guardar_usuarios(usuarios)
            enviar_mensaje(chat_id, f"✅ Usuario {target_id} ahora es Premium.")
            enviar_mensaje(target_id,
                "⭐ ¡Tu cuenta fue actualizada a <b>Premium</b>!\n\n"
                "Ahora recibes alertas <b>ilimitadas</b> 🟥\n"
                "¡Gracias por tu apoyo!"
            )
        else:
            enviar_mensaje(chat_id, "❌ Usuario no encontrado.")

    elif texto.startswith("/quitar_premium ") and es_admin(chat_id):
        target_id = texto.split(" ")[1]
        usuarios = cargar_usuarios()
        if target_id in usuarios:
            usuarios[target_id]["plan"] = "gratuito"
            guardar_usuarios(usuarios)
            enviar_mensaje(chat_id, f"✅ Listo, volvió a plan gratuito.")
        else:
            enviar_mensaje(chat_id, "❌ Usuario no encontrado.")

    elif texto.startswith("/bloquear ") and es_admin(chat_id):
        target_id = texto.split(" ")[1]
        usuarios = cargar_usuarios()
        if target_id in usuarios:
            usuarios[target_id]["activo"] = False
            guardar_usuarios(usuarios)
            enviar_mensaje(chat_id, f"🚫 Usuario {target_id} bloqueado.")
        else:
            enviar_mensaje(chat_id, "❌ Usuario no encontrado.")

    elif texto.startswith("/desbloquear ") and es_admin(chat_id):
        target_id = texto.split(" ")[1]
        usuarios = cargar_usuarios()
        if target_id in usuarios:
            usuarios[target_id]["activo"] = True
            guardar_usuarios(usuarios)
            enviar_mensaje(chat_id, f"✅ Usuario {target_id} desbloqueado.")
        else:
            enviar_mensaje(chat_id, "❌ Usuario no encontrado.")

    elif texto.startswith("/mensaje ") and es_admin(chat_id):
        contenido = texto.replace("/mensaje ", "", 1)
        usuarios = cargar_usuarios()
        for uid in usuarios:
            enviar_mensaje(uid, f"📢 <b>Mensaje del administrador:</b>\n\n{contenido}")
        enviar_mensaje(chat_id, f"✅ Mensaje enviado a {len(usuarios)} usuarios.")

# ==========================================
# LEER COMANDOS
# ==========================================
def obtener_comandos():
    global ultimo_update_id
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"offset": ultimo_update_id + 1, "timeout": 1}
    try:
        r = requests.get(url, params=params)
        updates = r.json().get("result", [])
        for update in updates:
            ultimo_update_id = update["update_id"]
            mensaje  = update.get("message", {})
            texto    = mensaje.get("text", "")
            chat_id  = mensaje.get("chat", {}).get("id")
            nombre   = mensaje.get("from", {}).get("first_name", "Usuario")
            username = mensaje.get("from", {}).get("username", "")
            if texto.startswith("/"):
                manejar_comando(chat_id, texto, nombre, username)
    except Exception as e:
        print(f"Error leyendo comandos: {e}")

# ==========================================
# FÚTBOL
# ==========================================
def obtener_partidos_en_vivo():
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params = {"live": "all"}
    r = requests.get(url, headers=headers, params=params)
    return r.json().get("response", [])

def revisar_tarjetas_rojas(partidos):
    for partido in partidos:
        if partido["league"]["id"] not in LIGAS:
            continue

        fixture_id    = partido["fixture"]["id"]
        equipo_local  = partido["teams"]["home"]["name"]
        equipo_visita = partido["teams"]["away"]["name"]
        nombre_liga   = partido["league"]["name"]
        pais          = partido["league"]["country"]
        goles_local   = partido["goals"]["home"] or 0
        goles_visita  = partido["goals"]["away"] or 0
        marcador      = f"{goles_local} - {goles_visita}"

        for evento in partido.get("events", []):
            tipo_evento  = evento.get("type", "")
            detalle      = evento.get("detail", "")
            minuto       = evento["time"]["elapsed"]
            jugador      = evento["player"]["name"] or "Desconocido"
            equipo       = evento["team"]["name"]
            clave        = f"{fixture_id}-{tipo_evento}-{detalle}-{jugador}-{minuto}"

            if clave in tarjetas_notificadas:
                continue

            mensaje = None

            # --- TARJETA ROJA ---
            if tipo_evento == "Card" and detalle == "Red Card":
                tarjetas_notificadas.add(clave)
                mensaje = (
                    f"🟥 TARJETA ROJA\n\n"
                    f"🏆 {nombre_liga} ({pais})\n"
                    f"⚽ <b>{equipo_local} {marcador} {equipo_visita}</b>\n"
                    f"⏱️ Minuto: {minuto}'\n\n"
                    f"👤 Jugador: <b>{jugador}</b>\n"
                    f"🏃 Equipo: {equipo}"
                )

            # --- SEGUNDA AMARILLA ---
            elif tipo_evento == "Card" and detalle == "Second Yellow card":
                tarjetas_notificadas.add(clave)
                mensaje = (
                    f"🟨🟥 SEGUNDA AMARILLA\n\n"
                    f"🏆 {nombre_liga} ({pais})\n"
                    f"⚽ <b>{equipo_local} {marcador} {equipo_visita}</b>\n"
                    f"⏱️ Minuto: {minuto}'\n\n"
                    f"👤 Jugador: <b>{jugador}</b>\n"
                    f"🏃 Equipo: {equipo}"
                )

            # --- GOL ANULADO POR VAR ---
            elif tipo_evento == "Var" and detalle in [
                "Goal cancelled",
                "Goal Disallowed - offside",
                "Goal Disallowed - foul",
                "Goal Disallowed - handball",
            ]:
                tarjetas_notificadas.add(clave)
                razon = {
                    "Goal cancelled": "razón no especificada",
                    "Goal Disallowed - offside": "fuera de juego",
                    "Goal Disallowed - foul": "falta previa",
                    "Goal Disallowed - handball": "mano",
                }.get(detalle, detalle)

                mensaje = (
                    f"🚫 GOL ANULADO POR VAR\n\n"
                    f"🏆 {nombre_liga} ({pais})\n"
                    f"⚽ <b>{equipo_local} {marcador} {equipo_visita}</b>\n"
                    f"⏱️ Minuto: {minuto}'\n\n"
                    f"👤 Jugador: <b>{jugador}</b>\n"
                    f"🏃 Equipo: {equipo}\n"
                    f"📋 Motivo: {razon}"
                )

            # --- TARJETA ROJA REVISADA POR VAR ---
            elif tipo_evento == "Var" and detalle in [
                "Red card upgrade",
                "Card upgrade",
            ]:
                tarjetas_notificadas.add(clave)
                mensaje = (
                    f"📺 VAR - TARJETA ROJA\n\n"
                    f"🏆 {nombre_liga} ({pais})\n"
                    f"⚽ <b>{equipo_local} {marcador} {equipo_visita}</b>\n"
                    f"⏱️ Minuto: {minuto}'\n\n"
                    f"👤 Jugador: <b>{jugador}</b>\n"
                    f"🏃 Equipo: {equipo}\n"
                    f"📋 Amarilla cambiada a roja por VAR"
                )

            # --- PENALTI REVISADO POR VAR ---
            elif tipo_evento == "Var" and detalle in [
                "Penalty confirmed",
                "Penalty cancelled",
            ]:
                tarjetas_notificadas.add(clave)
                resultado = "✅ CONFIRMADO" if detalle == "Penalty confirmed" else "❌ ANULADO"
                mensaje = (
                    f"📺 VAR - PENALTI {resultado}\n\n"
                    f"🏆 {nombre_liga} ({pais})\n"
                    f"⚽ <b>{equipo_local} {marcador} {equipo_visita}</b>\n"
                    f"⏱️ Minuto: {minuto}'\n\n"
                    f"🏃 Equipo: {equipo}"
                )

            if mensaje:
                notificar_todos(mensaje)
                print(f"✅ Notificado: {tipo_evento} - {detalle} | {equipo} min {minuto}")

# ==========================================
# MAIN
# ==========================================
def main():
    print("🤖 Bot iniciado.")
    registrar_usuario(ADMIN_CHAT_ID, "Admin", "admin")
    enviar_mensaje(ADMIN_CHAT_ID,
        "✅ <b>Bot iniciado</b>\n\n"
        "<b>Comandos de admin:</b>\n"
        "/usuarios — Estadísticas\n"
        "/lista — Ver todos los usuarios\n"
        "/premium [id] — Dar premium\n"
        "/quitar_premium [id] — Quitar premium\n"
        "/bloquear [id] — Bloquear usuario\n"
        "/desbloquear [id] — Desbloquear\n"
        "/mensaje [texto] — Broadcast a todos"
    )

    while True:
        obtener_comandos()
        try:
            partidos = obtener_partidos_en_vivo()
            print(f"🔍 Partidos en vivo: {len(partidos)}")
            revisar_tarjetas_rojas(partidos)
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(60)

if __name__ == "__main__":
    main()
