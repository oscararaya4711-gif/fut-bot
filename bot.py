import requests
import time
import os
import json
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
LIMITE_GRATUITO = 15  # ✅ Corregido a 15

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
    333, 334,  # ✅ 334 solo aparece aquí, eliminado de Colombia

    # ======= SUDAMÉRICA =======
    11, 13,
    128, 129, 130,  # Chile
    71, 72, 73,     # Brasil
    239, 240,       # Argentina
    242, 243,       # Uruguay
    281, 282,       # Paraguay
    266, 267,       # Perú
    314, 315,       # Ecuador
    332, 335,       # Colombia 1ª y 2ª  ✅ corregido (335 en vez de 334)
    300,            # Bolivia

    # ======= NORTEAMÉRICA =======
    253, 254,   # MLS y USL
    262, 263,   # Liga MX
    164,        # Canadian Premier League

    # ======= ASIA =======
    169,        # AFC Champions League
    292,        # Saudi Pro League
    307,        # Qatar Stars League
    268, 269, 270,  # Japón J1/J2/J3
    293, 294,       # Corea K League 1/2
    154,            # China Super League

    # ======= OCEANÍA =======
    188,        # A-League Australia
]

tarjetas_notificadas = set()
ultimo_update_id = 0

# ==========================================
# BASE DE DATOS - MONGODB
# ==========================================
cliente_mongo = MongoClient(MONGO_URL)
db = cliente_mongo["botfutbol"]
col = db["usuarios"]

def cargar_usuarios():
    usuarios = {}
    for u in col.find():
        chat_id = u["chat_id"]
        u.pop("_id", None)
        usuarios[chat_id] = u
    return usuarios

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
    usuarios = col.find({"activo": True, "pausado": False})
    for u in usuarios:
        chat_id = u["chat_id"]

        # Resetear contador si es nuevo día
        resetear_si_nuevo_dia(chat_id)
        u = col.find_one({"chat_id": chat_id})  # Recargar tras posible reset

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
                enviar_mensaje(chat_id,
                    f"⚠️ Te queda <b>1 notificación gratuita</b> por hoy.\n\n"
                    f"¿Quieres alertas ilimitadas?\n"
                    f"👉 {TU_USUARIO_TELEGRAM}"
                )
            elif restantes == 0:
                enviar_mensaje(chat_id,
                    f"🔒 <b>Límite diario alcanzado</b>\n\n"
                    f"Plan gratuito: {LIMITE_GRATUITO} alertas por día.\n\n"
                    f"Para alertas <b>ilimitadas</b> actualiza a Premium:\n"
                    f"👉 {TU_USUARIO_TELEGRAM}"
                )
        else:
            print(f"⛔ Usuario {chat_id} alcanzó límite gratuito hoy")

# ==========================================
# COMANDOS
# ==========================================
def manejar_comando(chat_id, texto, nombre, username):
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
            "/premium — Info sobre plan premium\n"
            "/ayuda — Ver esta lista"
        )

    elif texto == "/premium":
        # ✅ Solo info, no confunde con el comando admin /premium [id]
        enviar_mensaje(chat_id,
            f"⭐ <b>Plan Premium</b>\n\n
