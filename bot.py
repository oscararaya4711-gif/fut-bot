import requests
import time
import os
from datetime import datetime
from pymongo import MongoClient

# ==========================================
# CONFIGURACIÓN
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.environ.get("CHAT_ID")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")
MONGO_URL = os.environ.get("MONGO_URL")

TU_USUARIO_TELEGRAM = "@oaraya555"
LIMITE_GRATUITO = 15

LIGAS = [
    # ======= UEFA =======
    2, 3, 848,
    # ======= INGLATERRA - 5 DIVISIONES =======
    39, 40, 41, 42, 43,
    # ======= ESPAÑA =======
    140, 141, 142,
    # ======= ALEMANIA =======
    78, 79, 80,
    # ======= ITALIA =======
    135, 136, 137,
    # ======= FRANCIA =======
    61, 62, 63,
    # ======= PORTUGAL =======
    94, 95, 96,
    # ======= HOLANDA =======
    88, 89, 90,
    # ======= BÉLGICA =======
    144, 145,
    # ======= SUIZA =======
    207, 208, 209,
    # ======= AUSTRIA =======
    116, 117,
    # ======= SUECIA =======
    113, 114, 115,
    # ======= NORUEGA =======
    103, 104, 105,
    # ======= DINAMARCA =======
    119, 120, 121,
    # ======= ESCOCIA =======
    179, 180, 181,
    # ======= POLONIA =======
    106, 107, 108,
    # ======= TURQUÍA =======
    203, 204, 205,
    # ======= GRECIA =======
    197, 198,
    # ======= RUSIA =======
    235, 236,
    # ======= CROACIA =======
    210, 211,
    # ======= SERBIA =======
    286, 287,
    # ======= REPÚBLICA CHECA =======
    345, 346,
    # ======= HUNGRÍA =======
    373, 374,
    # ======= ESLOVAQUIA =======
    382, 383,
    # ======= RUMANIA =======
    283, 284,
    # ======= UCRANIA =======
    333, 334,
    # ======= SUDAMÉRICA =======
    11, 13,
    128, 129, 130,  # Chile
    71, 72, 73,     # Brasil
    239, 240,       # Argentina
    242, 243,       # Uruguay
    281, 282,       # Paraguay
    266, 267,       # Perú
    314, 315,       # Ecuador
    332, 335,       # Colombia
    300,            # Bolivia
    # ======= NORTEAMÉRICA =======
    253, 254,
    262, 263,
    164,
    # ======= ASIA =======
    169, 292, 307,
    268, 269, 270,
    293, 294,
    154,
    # ======= OCEANÍA =======
    188,
]

tarjetas_notificadas = set()
ultimo_update_id = 0

# ==========================================
# BASE DE DATOS - MONGODB
# ==========================================
cliente_mongo = MongoClient(MONGO_URL)
db = cliente_mongo["botfutbol"]
col = db["usuarios"]

# ==========================================
# TELEGRAM - FUNCIONES BASE
# ==========================================
def enviar_mensaje(chat_id, mensaje):
    """Envía un mensaje de texto simple"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "HTML"
        })
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

def enviar_mensaje_con_botones(chat_id, mensaje, botones):
    """Envía un mensaje con botones inline"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": chat_id,
            "text": mensaje,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": botones
            }
        })
    except Exception as e:
        print(f"Error enviando mensaje con botones: {e}")

# ==========================================
# BASE DE DATOS - FUNCIONES
# ==========================================
def guardar_usuario(chat_id, datos):
    datos["chat_id"] = str(chat_id)
    col.update_one({"chat_id": str(chat_id)}, {"$set": datos}, upsert=True)

def guardar_usuarios(usuarios):
    for chat_id, datos in usuarios.items():
        guardar_usuario(chat_id, datos)

def registrar_usuario(chat_id, nombre, username):
    chat_id = str(chat_id)
    hoy = datetime.now().strftime("%Y-%m-%d")
    existe = col.find_one({"chat_id": chat_id})
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
        # Solo avisar al admin si el nuevo usuario NO es el admin
        if chat_id != str(ADMIN_CHAT_ID):
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
        col.update_one({"chat_id": chat_id}, {"$set": {
            "ultima_actividad": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "nombre": nombre,
        }})
        return False

def resetear_si_nuevo_dia(chat_id):
    hoy = datetime.now().strftime("%Y-%m-%d")
    u = col.find_one({"chat_id": str(chat_id)})
    if u and u.get("fecha_conteo") != hoy:
        col.update_one({"chat_id": str(chat_id)}, {"$set": {
            "notificaciones_hoy": 0,
            "fecha_conteo": hoy
        }})

def es_admin(chat_id):
    return str(chat_id) == str(ADMIN_CHAT_ID)

# ==========================================
# NOTIFICACIONES
# ==========================================
def notificar_todos(mensaje):
    usuarios = col.find({"activo": True, "pausado": False})
    for u in usuarios:
        chat_id = u["chat_id"]
        resetear_si_nuevo_dia(chat_id)
        u = col.find_one({"chat_id": chat_id})
        es_premium = u.get("plan") == "premium" or chat_id == str(ADMIN_CHAT_ID)
        notifs_hoy = u.get("notificaciones_hoy", 0)

        if es_premium:
            enviar_mensaje(chat_id, mensaje)
            col.update_one({"chat_id": chat_id}, {"$inc": {
                "notificaciones_recibidas": 1,
                "notificaciones_hoy": 1
            }})
        elif notifs_hoy < LIMITE_GRATUITO:
            enviar_mensaje(chat_id, mensaje)
            col.update_one({"chat_id": chat_id}, {"$inc": {
                "notificaciones_recibidas": 1,
                "notificaciones_hoy": 1
            }})
            restantes = LIMITE_GRATUITO - notifs_hoy - 1
            if restantes == 1:
                enviar_mensaje_con_botones(chat_id,
                    f"⚠️ Te queda <b>1 notificación gratuita</b> por hoy.\n\n"
                    f"¿Quieres alertas ilimitadas?",
                    [[{"text": "⭐ Ver Plan Premium", "callback_data": "premium"}]]
                )
            elif restantes == 0:
                enviar_mensaje_con_botones(chat_id,
                    f"🔒 <b>Límite diario alcanzado</b>\n\n"
                    f"Plan gratuito: {LIMITE_GRATUITO} alertas por día.\n\n"
                    f"Actualiza a Premium para alertas ilimitadas:",
                    [[{"text": "⭐ Quiero Premium", "callback_data": "premium"}]]
                )
        else:
            print(f"⛔ Usuario {chat_id} alcanzó límite gratuito hoy")

# ==========================================
# COMANDOS
# ==========================================
def manejar_comando(chat_id, texto, nombre, username):
    chat_id_str = str(chat_id)
    texto = texto.strip().lower()

    # ======= COMANDOS PARA TODOS =======

    if texto == "/start":
        es_nuevo = registrar_usuario(chat_id, nombre, username)
        if es_nuevo:
            enviar_mensaje_con_botones(chat_id,
                f"👋 ¡Hola <b>{nombre}</b>! Bienvenido al bot de tarjetas rojas 🟥\n\n"
                f"Recibirás alertas en tiempo real de expulsiones en las principales ligas del mundo.\n\n"
                f"🆓 <b>Plan gratuito:</b> {LIMITE_GRATUITO} alertas por día\n"
                f"⭐ <b>Plan premium:</b> Alertas ilimitadas",
                [
                    [{"text": "📊 Mi estado",      "callback_data": "estado"},
                     {"text": "⭐ Ver Premium",     "callback_data": "premium"}],
                    [{"text": "⏸️ Pausar alertas", "callback_data": "pausar"},
                     {"text": "▶️ Reanudar",       "callback_data": "reanudar"}],
                    [{"text": "📋 Ayuda",           "callback_data": "ayuda"}],
                ]
            )
        else:
            enviar_mensaje_con_botones(chat_id,
                f"👋 ¡Hola de nuevo <b>{nombre}</b>!",
                [
                    [{"text": "📊 Mi estado",      "callback_data": "estado"},
                     {"text": "⭐ Ver Premium",     "callback_data": "premium"}],
                    [{"text": "⏸️ Pausar alertas", "callback_data": "pausar"},
                     {"text": "▶️ Reanudar",       "callback_data": "reanudar"}],
                ]
            )

    elif texto == "/ayuda":
        enviar_mensaje_con_botones(chat_id,
            "📋 <b>¿Qué quieres hacer?</b>",
            [
                [{"text": "📊 Mi estado",           "callback_data": "estado"}],
                [{"text": "⏸️ Pausar alertas",      "callback_data": "pausar"},
                 {"text": "▶️ Reanudar alertas",    "callback_data": "reanudar"}],
                [{"text": "⭐ Ver Premium",          "callback_data": "premium"}],
            ]
        )

    elif texto == "/premium":
        enviar_mensaje_con_botones(chat_id,
            f"⭐ <b>Plan Premium</b>\n\n"
            f"✅ {LIMITE_GRATUITO} alertas gratuitas → Ilimitadas\n"
            f"✅ Sin interrupciones\n"
            f"✅ Todas las ligas del mundo\n"
            f"✅ Tarjetas rojas, VAR, goles anulados\n\n"
            f"Para contratar escríbeme directamente:",
            [[{"text": f"💬 Contactar a {TU_USUARIO_TELEGRAM}", "url": f"https://t.me/{TU_USUARIO_TELEGRAM.replace('@', '')}"}]]
        )

    elif texto == "/pausar":
        col.update_one({"chat_id": chat_id_str}, {"$set": {"pausado": True}})
        enviar_mensaje_con_botones(chat_id,
            "⏸️ Notificaciones pausadas.",
            [[{"text": "▶️ Reanudar alertas", "callback_data": "reanudar"}]]
        )

    elif texto == "/reanudar":
        col.update_one({"chat_id": chat_id_str}, {"$set": {"pausado": False}})
        enviar_mensaje_con_botones(chat_id,
            "▶️ ¡Notificaciones reactivadas! 🟥",
            [[{"text": "📊 Ver mi estado", "callback_data": "estado"}]]
        )

    elif texto == "/estado":
        u = col.find_one({"chat_id": chat_id_str}) or {}
        pausado = "⏸️ Pausado" if u.get("pausado") else "▶️ Activo"
        plan    = "⭐ Premium" if u.get("plan") == "premium" else "🆓 Gratuito"
        hoy     = u.get("notificaciones_hoy", 0)
        total   = u.get("notificaciones_recibidas", 0)
        es_prem = u.get("plan") == "premium" or es_admin(chat_id)
        limite  = "∞" if es_prem else f"{hoy}/{LIMITE_GRATUITO}"

        botones = []
        if not es_prem:
            botones = [[{"text": "⭐ Quiero Premium", "callback_data": "premium"}]]

        enviar_mensaje_con_botones(chat_id,
            f"📊 <b>Tu estado:</b>\n\n"
            f"Estado: {pausado}\n"
            f"Plan: {plan}\n"
            f"Alertas hoy: {limite}\n"
            f"Total recibidas: {total}\n"
            f"Miembro desde: {u.get('fecha_registro', 'desconocido')}",
            botones
        )

    # ======= COMANDOS SOLO ADMIN =======

    elif texto == "/usuarios" and es_admin(chat_id):
        total    = col.count_documents({})
        activos  = col.count_documents({"activo": True, "pausado": False})
        pausados = col.count_documents({"pausado": True})
        premium  = col.count_documents({"plan": "premium"})
        enviar_mensaje(chat_id,
            f"📊 <b>Estadísticas:</b>\n\n"
            f"👥 Total usuarios: {total}\n"
            f"▶️ Activos: {activos}\n"
            f"⏸️ Pausados: {pausados}\n"
            f"⭐ Premium: {premium}\n"
            f"🆓 Gratuitos: {total - premium}"
        )

    elif texto == "/lista" and es_admin(chat_id):
        todos = list(col.find())
        if not todos:
            enviar_mensaje(chat_id, "No hay usuarios aún.")
            return
        msg = "👥 <b>Lista de usuarios:</b>\n\n"
        for u in todos:
            plan = "⭐" if u.get("plan") == "premium" else "🆓"
            msg += f"{plan} {u['nombre']} (@{u['username']}) — <code>{u['chat_id']}</code>\n"
        enviar_mensaje(chat_id, msg)

    elif texto.startswith("/dar_premium ") and es_admin(chat_id):
        target_id = texto.split(" ")[1]
        u = col.find_one({"chat_id": target_id})
        if u:
            col.update_one({"chat_id": target_id}, {"$set": {"plan": "premium"}})
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
        u = col.find_one({"chat_id": target_id})
        if u:
            col.update_one({"chat_id": target_id}, {"$set": {"plan": "gratuito"}})
            enviar_mensaje(chat_id, "✅ Listo, volvió a plan gratuito.")
        else:
            enviar_mensaje(chat_id, "❌ Usuario no encontrado.")

    elif texto.startswith("/bloquear ") and es_admin(chat_id):
        target_id = texto.split(" ")[1]
        u = col.find_one({"chat_id": target_id})
        if u:
            col.update_one({"chat_id": target_id}, {"$set": {"activo": False}})
            enviar_mensaje(chat_id, f"🚫 Usuario {target_id} bloqueado.")
        else:
            enviar_mensaje(chat_id, "❌ Usuario no encontrado.")

    elif texto.startswith("/desbloquear ") and es_admin(chat_id):
        target_id = texto.split(" ")[1]
        u = col.find_one({"chat_id": target_id})
        if u:
            col.update_one({"chat_id": target_id}, {"$set": {"activo": True}})
            enviar_mensaje(chat_id, f"✅ Usuario {target_id} desbloqueado.")
        else:
            enviar_mensaje(chat_id, "❌ Usuario no encontrado.")

    elif texto.startswith("/agregar ") and es_admin(chat_id):
        partes = texto.split(" ")
        if len(partes) < 3:
            enviar_mensaje(chat_id,
                "❌ Formato incorrecto.\n\n"
                "Uso: /agregar [id] [nombre] [username]\n"
                "Ejemplo: /agregar 123456789 Juan juanito123"
            )
        else:
            target_id = partes[1]
            nombre_ag = partes[2]
            username  = partes[3] if len(partes) > 3 else "sin_username"
            hoy       = datetime.now().strftime("%Y-%m-%d")
            existe = col.find_one({"chat_id": target_id})
            if existe:
                enviar_mensaje(chat_id,
                    f"⚠️ El usuario {target_id} ya existe en la base de datos.")
            else:
                col.insert_one({
                    "chat_id": target_id,
                    "nombre": nombre_ag,
                    "username": username,
                    "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "plan": "gratuito",
                    "activo": True,
                    "pausado": False,
                    "notificaciones_recibidas": 0,
                    "notificaciones_hoy": 0,
                    "ultima_actividad": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "fecha_conteo": hoy,
                })
                enviar_mensaje(chat_id,
                    f"✅ Usuario agregado:\n"
                    f"ID: {target_id}\n"
                    f"Nombre: {nombre_ag}\n"
                    f"Username: @{username}"
                )
                enviar_mensaje(target_id,
                    f"👋 ¡Hola <b>{nombre_ag}</b>! Tu cuenta fue reactivada en el bot 🟥\n\n"
                    f"Ya estás recibiendo alertas nuevamente.\n"
                    f"Escribe /estado para ver tu plan."
                )

    elif texto.startswith("/mensaje ") and es_admin(chat_id):
        contenido = texto.replace("/mensaje ", "", 1)
        todos = list(col.find())
        for u in todos:
            enviar_mensaje(u["chat_id"],
                f"📢 <b>Mensaje del administrador:</b>\n\n{contenido}")
        enviar_mensaje(chat_id, f"✅ Mensaje enviado a {len(todos)} usuarios.")

# ==========================================
# PROCESAR BOTONES TOCADOS
# ==========================================
def responder_boton(callback_query):
    chat_id     = callback_query["message"]["chat"]["id"]
    nombre      = callback_query["from"]["first_name"]
    username    = callback_query["from"].get("username", "")
    data        = callback_query["data"]
    callback_id = callback_query["id"]

    # Responder al callback para quitar el "reloj" de Telegram
    url_answer = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
    try:
        requests.post(url_answer, json={"callback_query_id": callback_id})
    except:
        pass

    # Procesar como si fuera un comando de texto
    manejar_comando(chat_id, f"/{data}", nombre, username)

# ==========================================
# LEER COMANDOS Y BOTONES DE TELEGRAM
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

            # Mensaje de texto normal
            if "message" in update:
                mensaje  = update["message"]
                texto    = mensaje.get("text", "")
                chat_id  = mensaje["chat"]["id"]
                nombre   = mensaje["from"]["first_name"]
                username = mensaje["from"].get("username", "")
                if texto.startswith("/"):
                    manejar_comando(chat_id, texto, nombre, username)

            # Botón tocado
            elif "callback_query" in update:
                responder_boton(update["callback_query"])

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
            tipo_evento = evento.get("type", "")
            detalle     = evento.get("detail", "")
            minuto      = evento["time"]["elapsed"]
            jugador     = evento["player"]["name"] or "Desconocido"
            equipo      = evento["team"]["name"]
            clave       = f"{fixture_id}-{tipo_evento}-{detalle}-{jugador}-{minuto}"

            if clave in tarjetas_notificadas:
                continue

            mensaje = None

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

            elif tipo_evento == "Var" and detalle in ["Red card upgrade", "Card upgrade"]:
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

            elif tipo_evento == "Var" and detalle in ["Penalty confirmed", "Penalty cancelled"]:
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
                print(f"✅ {tipo_evento} - {detalle} | {equipo} min {minuto}")

# ==========================================
# MAIN
# ==========================================
def main():
    print("🤖 Bot iniciado.")

    # Registrar admin primero
    registrar_usuario(ADMIN_CHAT_ID, "Admin", "admin")

    # Esperar 3 segundos para asegurar conexión estable con Telegram
    time.sleep(3)

    # Enviar mensaje de inicio al admin
    enviar_mensaje(ADMIN_CHAT_ID,
        "✅ <b>Bot iniciado correctamente</b>\n\n"
        "<b>Comandos de admin:</b>\n"
        "/usuarios — Estadísticas\n"
        "/lista — Ver todos los usuarios\n"
        "/dar_premium [id] — Dar premium\n"
        "/quitar_premium [id] — Quitar premium\n"
        "/bloquear [id] — Bloquear usuario\n"
        "/desbloquear [id] — Desbloquear\n"
        "/agregar [id] [nombre] [user] — Agregar usuario\n"
        "/mensaje [texto] — Broadcast a todos"
    )
    print(f"✅ Mensaje de inicio enviado al admin {ADMIN_CHAT_ID}")

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
