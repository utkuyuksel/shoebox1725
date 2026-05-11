# -*- coding: utf-8 -*-
# bot_logger.py
"""
Proje geneli için JSON Lines (.jsonl) formatında yapısal loglama sistemi.
Bu sistem, her bir komutu ve callback'i sarmalayarak (decorate ederek)
performans, kullanım ve hata takibi sağlar.
"""

import os
import json
import time
import datetime
import functools
import threading
from telegram import Update
from telegram.ext import ContextTypes
from config import logger # Konsol loglaması için ana logger'ı al

# --- Dosya ve Dizin Ayarları ---
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "bot_logs.jsonl")

# --- Thread Güvenliği ---
# Bot multi-thread çalıştığı için, dosyaya aynı anda yazmayı engellemek
# amacıyla bir "Lock" (Kilit) kullanmak ZORUNLUDUR.
_log_lock = threading.Lock()

def setup_logging():
    """
    Loglama sistemini başlatır. Log klasörünün var olduğundan emin olur.
    main.py tarafından bot başlarken bir kez çağrılır.
    """
    try:
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        logger.critical(f"JSONL Loglama sistemi aktif. Loglar şu dosyaya yazılacak: {LOG_FILE}")
    except Exception as e:
        logger.critical(f"FATAL: JSONL Log klasörü oluşturulamadı: {e}")

def log_to_jsonl(data: dict):
    """
    Verilen bir sözlüğü (dictionary) thread-safe bir şekilde .jsonl dosyasına yazar.
    """
    try:
        # 'datetime' objelerini string'e çevir (eğer varsa)
        if isinstance(data.get("timestamp"), datetime.datetime):
            data["timestamp"] = data["timestamp"].isoformat() + "Z"

        log_line = json.dumps(data, ensure_ascii=False)
        
        # Thread-safe yazma bloğu
        with _log_lock:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_line + "\n")
                
    except Exception as e:
        logger.error(f"JSONL Yazma Hatası: {e} | Veri: {data}")

def _parse_params(command: str, data_or_args: str | list) -> dict:
    """
    Gelen komuta göre callback datasını veya context.args'ı
    anlamlı bir 'params' sözlüğüne çevirir.
    """
    params = {}
    try:
        if command == "/hakem":
            if isinstance(data_or_args, list):
                params["search_term"] = " ".join(data_or_args)
            return params

        # Callback Dataları (callbacks.py)
        if not isinstance(data_or_args, str):
             return params
             
        parts = data_or_args.split('|')
        
        if command in ["LIG_SEC", "BASKET_SEC"]:
            params["lig_id"] = parts[1]
        elif command in ["MAC_SEC", "BASKET_MAC_SEC", "BACK_TO_MATCH", "BACK_TO_BASKET_MATCH"]:
            params = {"match_id": parts[1], "lig_id": parts[2], "home_id": parts[3], "away_id": parts[4]}
        elif command in ["PLAYER_LIST", "PLAYER_LIST_PAGE"]:
             params = {"team_id": parts[1], "team_name": parts[2], "page": int(parts[3])}
        elif command in ["PLAYER_STATS", "BASKET_PLAYER_STATS"]:
             params = {"player_id": parts[1], "page": int(parts[2])}
        elif command == "HAKEM_SEC":
            params["referee_id"] = parts[1]
            
    except Exception as e:
        logger.warning(f"Log parametresi ayrıştırılamadı: {e} | Veri: {data_or_args}")
    return params


def log_command(func):
    """
    Ana decorator'ımız. Async handler fonksiyonlarını sarmalar.
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        start_time = time.time()
        log_data = {
            "timestamp": datetime.datetime.utcnow(),
            "user_id": None,
            "command": func.__name__, # Varsayılan (Callback'de değişecek)
            "params": {},
            "response_time": None,
            "error": None
        }

        try:
            # --- 1. Kullanıcı ve Komut Tespiti ---
            if update.callback_query:
                query = update.callback_query
                log_data["user_id"] = query.from_user.id
                # 'LIG_SEC|TR_SL' -> 'LIG_SEC'
                log_data["command"] = query.data.split('|')[0] 
                log_data["params"] = _parse_params(log_data["command"], query.data)
                
            elif update.message:
                log_data["user_id"] = update.message.from_user.id
                log_data["command"] = update.message.text.split(' ')[0] # /start, /hakem
                if context.args:
                    log_data["params"] = _parse_params(log_data["command"], context.args)

            # --- 2. Asıl Fonksiyonu Çalıştır ---
            await func(update, context, *args, **kwargs)

        except Exception as e:
            # --- 3. Hata Yakalama ---
            log_data["error"] = f"{type(e).__name__}: {str(e)}"
            # Hatayı hem JSONL'ye hem de konsola yaz
            logger.error(f"Handler Hatası ({log_data['command']}): {e}", exc_info=True)
            # (İsteğe bağlı) Kullanıcıya genel bir hata mesajı göster
            # if update.callback_query:
            #     await update.callback_query.answer("🚨 Bir hata oluştu.", show_alert=True)
            # elif update.message:
            #     await update.message.reply_text("🚨 Beklenmedik bir hata oluştu.")

        finally:
            # --- 4. Logu Yaz ---
            log_data["response_time"] = round(time.time() - start_time, 3)
            log_to_jsonl(log_data)

    return wrapper