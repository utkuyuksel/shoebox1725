# -*- coding: utf-8 -*-
# handlers/commands.py
"""
... (önceki açıklamalar) ...
GÜNCELLEME (LOGLAMA): Tüm handler'lar @log_command decorator'ı ile sarmalandı.
GÜNCELLEME (ADMIN): Gizli /admin komutu eklendi.
"""

import os # YENİ
import json # YENİ
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes, filters, MessageHandler

# Diğer modüllerden importlar
from config import logger, LIG_LISTESI, BASKETBOL_LIG_LISTESI
import data_loader 
from bot_logger import log_command, LOG_FILE # YENİ: LOG_FILE import edildi

# =================================================================
# YENİ: ADMIN AYARLARI
# =================================================================

# !! ÖNEMLİ !!
# Buraya kendi Telegram User ID'nizi yazın.
# Bu ID'yi bir önceki adımda bot_logs.jsonl dosyasında "user_id" alanında gördünüz.
ADMIN_USER_ID = 7197369392 # 7197369392 yerine kendi ID'nizi yazın

async def _read_last_n_lines(filepath, n) -> list:
    """(YENİ) Bir dosyanın son N satırını verimli bir şekilde okur."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Dosyayı oku ve satırlara ayır
            lines = f.readlines()
            # Son N satırı al
            return lines[-n:]
    except FileNotFoundError:
        return ["Log dosyası henüz oluşturulmamış."]
    except Exception as e:
        return [f"Log okuma hatası: {e}"]

@log_command
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    (YENİ) Sadece ADMIN_USER_ID tarafından kullanılabilen
    gizli log okuma komutu.
    """
    if update.message.from_user.id != ADMIN_USER_ID:
        logger.warning(f"Yetkisiz /admin denemesi: {update.message.from_user.id}")
        return # Yetkisi olmayanlara hiçbir şey gönderme
    
    args = context.args
    command = args[0] if args else "help"

    try:
        if command == "logs":
            line_count = int(args[1]) if len(args) > 1 else 10 # Varsayılan 10 satır
            lines = await _read_last_n_lines(LOG_FILE, line_count)
            
            message_text = f"📋 *Son {len(lines)} log satırı:*\n\n"
            
            # Logları daha okunaklı hale getirelim (opsiyonel)
            formatted_lines = []
            for line in lines:
                try:
                    data = json.loads(line)
                    ts = data.get('timestamp', '').split('T')[1].split('.')[0]
                    cmd = data.get('command', 'N/A')
                    user = data.get('user_id', 'N/A')
                    err = data.get('error')
                    
                    if err:
                        formatted_lines.append(f"🚨 {ts} | {cmd} | HATA: {err}")
                    else:
                        formatted_lines.append(f"✅ {ts} | {user} | {cmd}")
                except:
                    formatted_lines.append(line) # Hatalı satırı olduğu gibi ekle

            message_text += "```\n" + "\n".join(formatted_lines) + "\n```"
            await update.message.reply_text(message_text, parse_mode='Markdown')

        elif command == "file":
            await update.message.reply_text("📂 `bot_logs.jsonl` dosyası gönderiliyor...")
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=open(LOG_FILE, 'rb')
            )
            
        elif command == "help":
            await update.message.reply_text(
                "ℹ️ *Admin Komutları:*\n"
                "`/admin logs [satır_sayısı]`\n"
                "  _Son N log satırını gösterir (varsayılan 10)._\n\n"
                "`/admin file`\n"
                "  _Log dosyasının tamamını gönderir._",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("Bilinmeyen admin komutu. `/admin help` yazın.")
            
    except FileNotFoundError:
        await update.message.reply_text(f"🚨 Hata: {LOG_FILE} dosyası sunucuda bulunamadı.")
    except Exception as e:
        await update.message.reply_text(f"🚨 Komut işlenirken hata: {e}")

# =================================================================
# MEVCUT KOMUTLAR (Aşağısı değişmedi)
# =================================================================

# --- /start ---
@log_command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcıya bot komutlarını ve kullanım talimatını gönderir."""
    # ... (kod değişmedi) ...
    help_text = (
        "👋 Merhaba! Ben İstatistik Botu.\n\n"
        "Aşağıdaki komutları kullanarak arama yapabilirsin:\n"
        "\n"
        "➡️ */futbol*\n"
        "Futbol liglerindeki maçları ve istatistikleri görüntüler.\n\n"
        "➡️ */basketbol*\n"
        "Basketbol liglerindeki maçları ve istatistikleri görüntüler.\n\n"
        "➡️ */hakem [isim]*\n"
        "Sofascore veritabanından hakem arar."
    )
    await update.message.reply_text(
        help_text, 
        parse_mode='Markdown'
    )

# --- /futbol (GÜNCELLENDİ) ---
@log_command
async def futbol_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/futbol komutu için ana işleyici. Lig Seçim Menüsünü gösterir."""
    await send_futbol_menu(update)

async def send_futbol_menu(update_or_query: Update | CallbackQuery) -> None:
    # ... (kod değişmedi) ...
    keyboard = []
    ligler = list(LIG_LISTESI.items())
    
    for i in range(0, len(ligler), 2):
        row = []
        for j in range(2):
            if i + j < len(ligler):
                lig_adi, (emoji, lig_id, api_id, season_id, fetch_type) = ligler[i + j]
                callback_data = f"LIG_SEC|{lig_id}"
                button_text = f"{emoji} {lig_adi}"
                row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        
        if row:
            keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    menu_text = "⚽ Futbol Ligleri\n\nBir lig seçin:"

    if isinstance(update_or_query, Update) and update_or_query.message:
        await update_or_query.message.reply_text(menu_text, reply_markup=reply_markup)
    elif isinstance(update_or_query, CallbackQuery):
         await update_or_query.edit_message_text(menu_text, reply_markup=reply_markup)

# --- /basketbol (DOKUNULMADI) ---
@log_command
async def basketbol_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/basketbol komutu için ana işleyici. Basketbol Lig Menüsünü gösterir."""
    await send_basketbol_menu(update)

async def send_basketbol_menu(update_or_query: Update | CallbackQuery) -> None:
    # ... (kod değişmedi) ...
    keyboard = []
    ligler = list(BASKETBOL_LIG_LISTESI.items())
    
    for i in range(0, len(ligler), 2):
        row = []
        for j in range(2):
            if i + j < len(ligler):
                lig_adi, (emoji, lig_id, api_id, season_id, fetch_type) = ligler[i + j]
                callback_data = f"BASKET_SEC|{lig_id}" 
                button_text = f"{emoji} {lig_adi}"
                row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        
        if row:
            keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    menu_text = "🏀 Basketbol Ligleri\n\nBir lig seçin:"

    if isinstance(update_or_query, Update) and update_or_query.message:
        await update_or_query.message.reply_text(menu_text, reply_markup=reply_markup)
    elif isinstance(update_or_query, CallbackQuery):
         await update_or_query.edit_message_text(menu_text, reply_markup=reply_markup)

# --- YENİ: /hakem ---
@log_command
async def hakem_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (kod değişmedi) ...
    if not context.args:
        await update.message.reply_text(
            "❌ Kullanım: /hakem [hakem ismi]\n\n"
            "Örnek: /hakem yasin kol\n"
            "Örnek: /hakem marciniak"
        )
        return

    search_term = " ".join(context.args).lower()
    context.user_data['LAST_HAKEM_SEARCH'] = search_term

    results = []
    for referee_name, referee_id in data_loader.ALL_REFEREES.items():
        if search_term in referee_name.lower():
            results.append((referee_name, referee_id))
    
    if not results:
        await update.message.reply_text(f"🔎 '{search_term}' için hakem bulunamadı.")
        return
        
    if len(results) > 15:
        await update.message.reply_text(f"🔎 '{search_term}' için çok fazla sonuç bulundu ({len(results)}). Lütfen daha spesifik bir arama yapın.")
        return

    keyboard = []
    for i, (name, ref_id) in enumerate(results):
        callback_data = f"HAKEM_SEC|{ref_id}"
        keyboard.append([InlineKeyboardButton(f"{i+1}. {name}", callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"🔎 '{search_term}' için {len(results)} hakem bulundu:", 
        reply_markup=reply_markup
    )


# --- Hata Yakalayıcılar (GÜNCELLENDİ) ---
@log_command
async def unknown_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (kod değişmedi) ...
    await update.message.reply_text(
        "ℹ️ Üzgünüm, bu komutu anlayamadım.\n\n"
        "Lütfen /futbol, /basketbol veya /hakem komutlarını kullanın."
    )

@log_command
async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (kod değişmedi) ...
    await update.message.reply_text(
        "ℹ️ Üzgünüm, bu komutu anlayamadım.\n\n"
        "Kullanılabilir komutlar: /futbol, /basketbol, /hakem"
    )