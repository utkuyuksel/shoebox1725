# -*- coding: utf-8 -*-
# main.py
"""
... (önceki açıklamalar) ...
GÜNCELLEME (ADMIN): /admin komutu eklendi ve filtrelerden çıkarıldı.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Proje içi importlar
from config import TOKEN, logger
import data_loader 
import bot_logger

# Handler (işleyici) modüllerini import et
from handlers import commands as cmd_handlers # Komut işleyiciler
from handlers import callbacks as cb_handlers # Buton işleyiciler

def main() -> None:
    """Botu çalıştıran ana fonksiyon."""
    
    bot_logger.setup_logging()
    
    try:
        data_loader.load_all_data()
    except Exception as e:
        logger.critical(f"FATAL: Veri yükleme başarısız ({e}). Bot başlatılamıyor.")
        return

    application = Application.builder().token(TOKEN).build()

    # --- Komut Handler'ları ---
    application.add_handler(CommandHandler("start", cmd_handlers.start_command))
    application.add_handler(CommandHandler("futbol", cmd_handlers.futbol_command)) 
    application.add_handler(CommandHandler("basketbol", cmd_handlers.basketbol_command)) 
    application.add_handler(CommandHandler("hakem", cmd_handlers.hakem_command))
    application.add_handler(CommandHandler("admin", cmd_handlers.admin_command)) # YENİ
    
    callback_pattern = (
        r'^(LIG_SEC|MAC_SEC|MENU_ANAMENU|LIG_SECIM_GERI|'
        r'BASKET_SEC|BASKET_SECIM_GERI|GERI_BASKET_LISTE|BASKET_MAC_SEC|'
        r'PLAYER_LIST|BACK_TO_MATCH|BACK_TO_BASKET_MATCH|PLAYER_LIST_PAGE|PLAYER_STATS|'
        r'BASKET_PLAYER_STATS|'
        r'HAKEM_SEC|HAKEM_ARAMA_GERI)'
    )
    
    application.add_handler(
        CallbackQueryHandler(cb_handlers.button_callback_handler, pattern=callback_pattern)
    )

    # YENİ: /admin komutunu da bilinen komutlara ekle
    known_commands = r'^(/start|/futbol|/basketbol|/hakem|/admin)$'
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cmd_handlers.unknown_text_handler))
    application.add_handler(MessageHandler(filters.COMMAND & ~filters.Regex(known_commands), cmd_handlers.unknown_command_handler))
    
    
    logger.critical("Bot başlatılıyor... (Polling)")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()