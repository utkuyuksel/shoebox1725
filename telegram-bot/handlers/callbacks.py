# -*- coding: utf-8 -*-
# handlers/callbacks.py
"""
Tüm Telegram buton (CallbackQuery) tıklamalarını yönetir.

GÜNCELLEME (LOGLAMA): Ana button_callback_handler, @log_command ile sarmalandı.
GÜNCELLEME (UX): "Retry" ve "Refresh" butonları eklendi.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes
import re 
import math 

# Proje içi importlar
from config import logger, LIG_LISTESI, BASKETBOL_LIG_LISTESI
from scraping import sofascore as sfs_scraper
from scraping import transfermarkt as tm_scraper 
import data_loader
from bot_logger import log_command # YENİ: Decorator'ı import et

PLAYER_PAGE_SIZE = 10 

# ###########################################################################
# # --- YARDIMCI FONKSİYONLAR (GERİ TUŞLARI) ---
# # (Bunlar handler değil, decorator EKLEME)
# ###########################################################################

async def _go_back_to_futbol_menu(query: CallbackQuery):
    """(DOKUNULMADI)"""
    logger.info("Geri tuşu: Futbol Ligleri menüsü yeniden oluşturuluyor...")
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
    text = "⚽ Futbol Ligleri\n\nBir lig seçin:"
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        if 'message is not modified' not in str(e):
            logger.warning(f"Ligler menüsü (geri) gösterilirken hata: {e}")

async def _go_back_to_basketbol_menu(query: CallbackQuery):
    """(DOKUNULMADI)"""
    logger.info("Geri tuşu: Basketbol Ligleri menüsü yeniden oluşturuluyor...")
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
    text = "🏀 Basketbol Ligleri\n\nBir lig seçin:"
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        if 'message is not modified' not in str(e):
            logger.warning(f"Basketbol menüsü (geri) gösterilirken hata: {e}")

async def _go_back_to_hakem_arama(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """(DOKUNULMADI)"""
    search_term = context.user_data.get('LAST_HAKEM_SEARCH', None)
    if not search_term:
        await query.edit_message_text("Arama geçmişi bulunamadı. Lütfen /hakem komutunu tekrar kullanın.")
        return
    logger.info(f"Hakem Geri: '{search_term}' için arama sonuçları yeniden oluşturuluyor...")
    results = []
    for referee_name, referee_id in data_loader.ALL_REFEREES.items():
        if search_term in referee_name.lower():
            results.append((referee_name, referee_id))
    if not results:
        await query.edit_message_text(f"🔎 '{search_term}' için hakem bulunamadı.")
        return
    keyboard = []
    for i, (name, ref_id) in enumerate(results):
        callback_data = f"HAKEM_SEC|{ref_id}"
        keyboard.append([InlineKeyboardButton(f"{i+1}. {name}", callback_data=callback_data)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await query.edit_message_text(
            f"🔎 '{search_term}' için {len(results)} hakem bulundu:", 
            reply_markup=reply_markup
        )
    except Exception as e:
        if 'message is not modified' not in str(e):
            logger.warning(f"Hakem arama (geri) gösterilirken hata: {e}")

# ###########################################################################
# # --- YARDIMCI FONKSİYONLAR (FORMATLAYICILAR) ---
# # (Bunlar handler değil, decorator EKLEME)
# ###########################################################################

async def _format_and_send_match_list(
    query: CallbackQuery, 
    maclar: list, 
    lig_adi: str, 
    lig_id: str 
):
    """(DOKUNULMADI)"""
    message_text = f"⚽ {lig_adi} | GELECEK MAÇLAR ({len(maclar)} Maç)\n\n"
    keyboard = []
    for i, mac in enumerate(maclar):
        mac_no = i + 1
        tarih_ve_saat = mac['tarih_saat'] 
        t1_name = mac['ev_sahibi']
        t2_name = mac['konuk']
        message_text += (
            f"{mac_no}. {t1_name} 🆚 {t2_name}\n"
            f"📅 {tarih_ve_saat}\n\n"
        )
        callback_data = (
            f"MAC_SEC|{mac['id']}|{lig_id}|{mac['home_id']}|{mac['away_id']}"
        )
        keyboard.append(InlineKeyboardButton(f"{mac_no}. Maç", callback_data=callback_data))
    keyboard_rows = [keyboard[i:i + 3] for i in range(0, len(keyboard), 3)]
    keyboard_rows.append([
        InlineKeyboardButton("🏠 Menü", callback_data="MENU_ANAMENU"),
        InlineKeyboardButton("⬅️ Geri (Lig Listesi)", callback_data="LIG_SECIM_GERI") 
    ])
    reply_markup = InlineKeyboardMarkup(keyboard_rows)
    try:
        await query.edit_message_text(message_text, reply_markup=reply_markup)
    except Exception as e:
        if 'message is not modified' not in str(e):
             logger.warning(f"Futbol maç listesi gönderilirken hata: {e}")

async def _format_and_send_basket_match_list(
    query: CallbackQuery, 
    maclar: list, 
    lig_adi: str, 
    lig_id: str 
):
    """(DOKUNULMADI)"""
    message_text = f"🏀 {lig_adi} | GELECEK MAÇLAR ({len(maclar)} Maç)\n\n"
    keyboard = []
    for i, mac in enumerate(maclar):
        mac_no = i + 1
        tarih_ve_saat = mac['tarih_saat'] 
        t1_name = mac['ev_sahibi']
        t2_name = mac['konuk']
        message_text += (
            f"{mac_no}. {t1_name} - {t2_name}\n"
            f"📅 {tarih_ve_saat}\n\n"
        )
        callback_data = (
            f"BASKET_MAC_SEC|{mac['id']}|{lig_id}|{mac['home_id']}|{mac['away_id']}"
        )
        keyboard.append(InlineKeyboardButton(f"{mac_no}. Maç", callback_data=callback_data))
    keyboard_rows = [keyboard[i:i + 3] for i in range(0, len(keyboard), 3)]
    keyboard_rows.append([
        InlineKeyboardButton("🏠 Menü", callback_data="MENU_ANAMENU"),
        InlineKeyboardButton("⬅️ Geri (Lig Listesi)", callback_data="BASKET_SECIM_GERI") 
    ])
    reply_markup = InlineKeyboardMarkup(keyboard_rows)
    try:
        await query.edit_message_text(message_text, reply_markup=reply_markup)
    except Exception as e:
        if 'message is not modified' not in str(e):
             logger.warning(f"Basketbol maç listesi gönderilirken hata: {e}")

async def _format_football_match_preview(
    home_stats: dict, 
    away_stats: dict, 
    home_name: str, 
    home_shortName: str,
    away_name: str, 
    away_shortName: str,
    date_info: str
) -> tuple[str, str]:
    """(DOKUNULMADI)"""
    stats_text = ""
    stats_type = "empty" 
    if home_stats.get("stats_type") == "detailed" and away_stats.get("stats_type") == "detailed":
        logger.info(f"⚽ Formatlayıcı: Detaylı istatistik formatı kullanılıyor ({home_shortName} vs {away_shortName}).")
        message_parts = [
            "📊 *İSTATİSTİK KARŞILAŞTIRMA*",
            "_(Maç Başına Lig Ortalamaları)_\n",
            "🎯 *ŞUT İSTATİSTİKLERİ (Maç Başına)*",
            "├ Toplam Şut:",
            f"│  ├ {home_shortName}: *{home_stats['total_shots_pg']:.1f}*",
            f"│  └ {away_shortName}: *{away_stats['total_shots_pg']:.1f}*",
            "└ İsabetli Şut:",
            f"   ├ {home_shortName}: *{home_stats['shots_on_target_pg']:.1f}*",
            f"   └ {away_shortName}: *{away_stats['shots_on_target_pg']:.1f}*",
            "\n",
            "🚩 *KORNER ORTALAMASI*",
            f"├ {home_shortName}: *{home_stats['corners_pg']:.1f}*",
            f"└ {away_shortName}: *{away_stats['corners_pg']:.1f}*",
            "\n",
            "⚠️ *FAUL ORTALAMASI*",
            f"├ {home_shortName}: *{home_stats['fouls_pg']:.1f}*",
            f"└ {away_shortName}: *{away_stats['fouls_pg']:.1f}*",
            "\n",
            "🚫 *OFSAYT ORTALAMASI*",
            f"├ {home_shortName}: *{home_stats['offsides_pg']:.1f}*",
            f"└ {away_shortName}: *{away_stats['offsides_pg']:.1f}*",
            "\n",
            "🥅 *KALE VURUŞU (Maç Başına)*",
            f"├ {home_shortName}: *{home_stats.get('goal_kicks_pg', 0.0):.1f}*",
            f"└ {away_shortName}: *{away_stats.get('goal_kicks_pg', 0.0):.1f}*",
            "\n",
            "🟨🟥 *KART ORTALAMASI*",
            "├ Sarı Kart:",
            f"│  ├ {home_shortName}: *{home_stats['yellow_cards_pg']:.1f}*",
            f"│  └ {away_shortName}: *{away_stats['yellow_cards_pg']:.1f}*",
            "└ Kırmızı Kart:",
            f"   ├ {home_shortName}: *{home_stats['red_cards_pg']:.1f}*",
            f"   └ {away_shortName}: *{away_stats['red_cards_pg']:.1f}*",
        ]
        stats_text = "\n".join(message_parts)
        stats_type = "detailed"
        return stats_text, stats_type
    elif home_stats.get("stats_type") == "standings" and away_stats.get("stats_type") == "standings":
        logger.warning(f"⚽ Formatlayıcı: 'Detaylı' istatistikler bulunamadı. 'Puan Durumu' (fallback) formatı kullanılıyor ({home_shortName} vs {away_shortName}).")
        message_parts = [
            "📊 *PUAN DURUMU & GENEL İSTATİSTİKLER*\n",
            f"*{home_shortName}* ({home_stats.get('matches', 0)} Maç)",
            f" Sıra: *{home_stats.get('position', 'N/A')}* | Puan: *{home_stats.get('points', 'N/A')}*",
            f" G-B-M: *{home_stats.get('wins', 0)}-{home_stats.get('draws', 0)}-{home_stats.get('losses', 0)}*",
            f" Goller (Attığı/Yediği): *{home_stats.get('goalsForTotal', 0)} / {home_stats.get('goalsAgainstTotal', 0)}*",
            f" Maç Başına Gol Ort: *{home_stats['goals_for_pg']:.1f}* / *{home_stats['goals_against_pg']:.1f}*",
            "\n",
            f"*{away_shortName}* ({away_stats.get('matches', 0)} Maç)",
            f" Sıra: *{away_stats.get('position', 'N/A')}* | Puan: *{away_stats.get('points', 'N/A')}*",
            f" G-B-M: *{away_stats.get('wins', 0)}-{away_stats.get('draws', 0)}-{away_stats.get('losses', 0)}*",
            f" Goller (Attığı/Yediği): *{away_stats.get('goalsForTotal', 0)} / {away_stats.get('goalsAgainstTotal', 0)}*",
            f" Maç Başına Gol Ort: *{away_stats['goals_for_pg']:.1f}* / *{away_stats['goals_against_pg']:.1f}*",
        ]
        stats_text = "\n".join(message_parts)
        stats_type = "standings"
        return stats_text, stats_type
    else:
        logger.error(f"Formatlayıcı: {home_shortName} veya {away_shortName} için HİÇ istatistik verisi bulunamadı (ne detaylı ne de puan durumu).")
        stats_text = (
            "ℹ️ *İstatistik Bilgisi Eksik*\n\n"
            f"*{home_shortName}* veya *{away_shortName}* takımlarından biri için "
            "bu lige ait sezon istatistikleri bulunamadı.\n\n"
            "(Takım bu sezon ligde oynamamış veya henuz istatistikleri oluşmamış olabilir.)"
        )
        stats_type = "empty"
        return stats_text, stats_type

async def _format_basket_match_preview(
    home_stats: dict, 
    away_stats: dict, 
    home_name: str, 
    home_shortName: str,
    away_name: str, 
    away_shortName: str,
    date_info: str
) -> str:
    """(DOKUNULMADI)"""
    h_name_stats = home_shortName
    a_name_stats = away_shortName
    if not home_stats or not away_stats:
        logger.warning(f"Formatlayıcı: {h_name_stats} veya {a_name_stats} için istatistik verisi boş geldi.")
        return (
            "ℹ️ *İstatistik Bilgisi Eksik*\n\n"
            f"*{h_name_stats}* veya *{a_name_stats}* takımlarından biri için "
            "bu lige ait detaylı sezon istatistikleri bulunamadı.\n\n"
            "(Takım bu sezon ligde oynamamış veya henüz istatistikleri oluşmamış olabilir.)"
        )
    message_parts = [
        "🏀 *MAÇ ÖNİZLEMESİ*",
        f"*{home_name}* 🆚 *{away_name}*", 
        f"📅 _{date_info.replace(' ', ' | ', 1)}_", 
        "\n"
        "📊 *İSTATİSTİK KARŞILAŞTIRMA*",
        "_(Maç Başına Lig Ortalamaları)_\n",
        "🎯 *SAYI ÜRETİMİ (Maç Başına)*",
        "├ _Takım Sayı Ortalaması_",
        f"│ • {h_name_stats}: *{home_stats['ppg']:.1f}*", 
        f"│ • {a_name_stats}: *{away_stats['ppg']:.1f}*",
        "└ _Yenen Sayı Ortalaması_",
        f"  • {h_name_stats}: *{home_stats['ppg_allowed']:.1f}*",
        f"  • {a_name_stats}: *{away_stats['ppg_allowed']:.1f}*",
        "\n",
        "📈 *HÜCUM VERİMLİLİĞİ*",
        "├ _Şut Yüzdesi (FG%):_",
        f"│ • {h_name_stats}: *{home_stats['fg_pct']:.1f}%*",
        f"│ • {a_name_stats}: *{away_stats['fg_pct']:.1f}%*",
        "├ _İkilik (2P - Maç Başına):_",
        f"│ • {h_name_stats}: *{home_stats['2p_made_pg']:.1f}/{home_stats['2p_att_pg']:.1f} (%{home_stats['2p_pct']:.1f})*",
        f"│ • {a_name_stats}: *{away_stats['2p_made_pg']:.1f}/{away_stats['2p_att_pg']:.1f} (%{away_stats['2p_pct']:.1f})*",
        "├ _Üçlük (3P - Maç Başına):_",
        f"│ • {h_name_stats}: *{home_stats['3p_made_pg']:.1f}/{home_stats['3p_att_pg']:.1f} (%{home_stats['3p_pct']:.1f})*",
        f"│ • {a_name_stats}: *{away_stats['3p_made_pg']:.1f}/{away_stats['3p_att_pg']:.1f} (%{away_stats['3p_pct']:.1f})*",
        "└ _Serbest Atış (FT - Maç Başına):_",
        f"  • {h_name_stats}: *{home_stats['ft_made_pg']:.1f}/{home_stats['ft_att_pg']:.1f} (%{home_stats['ft_pct']:.1f})*",
        f"  • {a_name_stats}: *{away_stats['ft_made_pg']:.1f}/{away_stats['ft_att_pg']:.1f} (%{home_stats['ft_pct']:.1f})*",
        "\n",
        "🧱 *RİBAUND MÜCADELESİ (Maç Başına)*",
        "├ _Toplam Ribaund:_",
        f"│ • {h_name_stats}: *{home_stats['total_reb_pg']:.1f}*",
        f"│ • {a_name_stats}: *{away_stats['total_reb_pg']:.1f}*",
        "├ _Hücum Ribaundu:_",
        f"│ • {h_name_stats}: *{home_stats['off_reb_pg']:.1f}*",
        f"│ • {a_name_stats}: *{away_stats['off_reb_pg']:.1f}*",
        "└ _Savunma Ribaundu:_",
        f"  • {h_name_stats}: *{home_stats['def_reb_pg']:.1f}*",
        f"  • {a_name_stats}: *{away_stats['def_reb_pg']:.1f}*",
        "\n",
        "🎯 *ASİST & TOP KAYBI (Maç Başına)*",
        "├ _Asist:_",
        f"│ • {h_name_stats}: *{home_stats['assists_pg']:.1f}*",
        f"│ • {a_name_stats}: *{away_stats['assists_pg']:.1f}*",
        "└ _Top Kaybı:_",
        f"  • {h_name_stats}: *{home_stats['turnovers_pg']:.1f}*",
        f"  • {a_name_stats}: *{away_stats['turnovers_pg']:.1f}*",
        "\n",
        "⚔️ *SAVUNMA VERİLERİ (Maç Başına)*",
        "├ _Top Çalma:_",
        f"│ • {h_name_stats}: *{home_stats['steals_pg']:.1f}*",
        f"│ • {a_name_stats}: *{away_stats['steals_pg']:.1f}*",
        "└ _Blok:_",
        f"  • {h_name_stats}: *{home_stats['blocks_pg']:.1f}*",
        f"  • {a_name_stats}: *{away_stats['blocks_pg']:.1f}*",
    ]
    return "\n".join(message_parts)


async def _format_and_send_player_list(
    query: CallbackQuery, 
    players_data: dict, 
    team_name: str, 
    team_id: str, 
    match_id: str, 
    lig_id: str, 
    home_id: str, 
    away_id: str,
    page: int = 0,
    context: ContextTypes.DEFAULT_TYPE = None
):
    """(DOKUNULMADI)"""
    
    players_grouped = players_data.get("grouped", {}) 
    all_players_flat = players_data.get("flat", []) 
    total_players = len(all_players_flat)
    
    total_pages = math.ceil(total_players / PLAYER_PAGE_SIZE)
    if page < 0: page = 0
    if page >= total_pages and total_pages > 0: page = total_pages - 1
    
    page_start = page * PLAYER_PAGE_SIZE
    page_end = (page + 1) * PLAYER_PAGE_SIZE
    players_on_page = all_players_flat[page_start:page_end] 
    
    message_parts = []
    message_parts.append(f"👥 *{team_name} Kadrosu*")
    message_parts.append(f"Sayfa {page + 1}/{total_pages} • Toplam {total_players} oyuncu\n")

    if not players_on_page:
        message_parts.append("Bu takım için detaylı kadro bilgisi bulunamadı.")
    else:
        for name, p_id in players_on_page:
            message_parts.append(f" • {name}") 
            
    keyboard_rows = []
    player_buttons = []
    
    for name, p_id in players_on_page:
        # YENİ: Oyuncu ismini context'e kaydet
        if context:
            context.user_data[f'player_name_{p_id}'] = name
            
        # Basketbol veya futbol olduğunu context'ten anla
        last_basket_match = context.user_data.get('LAST_BASKET_MATCH_DATA') if context else None
        
        if last_basket_match:
            callback_data = f"BASKET_PLAYER_STATS|{p_id}|{page}"
        else:
            callback_data = f"PLAYER_STATS|{p_id}|{page}"

        player_buttons.append(InlineKeyboardButton(f"{name}", callback_data=callback_data))
    
    for i in range(0, len(player_buttons), 2):
        keyboard_rows.append(player_buttons[i:i+2])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Önceki", callback_data=f"PLAYER_LIST_PAGE|{page - 1}|{team_id}|{team_name}"))
    if (page + 1) < total_pages:
        nav_buttons.append(InlineKeyboardButton("Sonraki ➡️", callback_data=f"PLAYER_LIST_PAGE|{page + 1}|{team_id}|{team_name}"))
    
    if nav_buttons:
        keyboard_rows.append(nav_buttons)

    # Geri butonu için basketbol/futbol ayrımı
    last_basket_match = context.user_data.get('LAST_BASKET_MATCH_DATA') if context else None
    if last_basket_match:
        callback_data_geri = f"BACK_TO_BASKET_MATCH|{match_id}|{lig_id}|{home_id}|{away_id}"
    else:
        callback_data_geri = f"BACK_TO_MATCH|{match_id}|{lig_id}|{home_id}|{away_id}"
        
    keyboard_rows.append([
        InlineKeyboardButton("🏠 Menü", callback_data="MENU_ANAMENU"),
        InlineKeyboardButton("⬅️ Geri (Maça)", callback_data=callback_data_geri)
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard_rows)

    try:
        await query.edit_message_text(
            "\n".join(message_parts), 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        if 'message is not modified' not in str(e):
             logger.warning(f"Oyuncu listesi gönderilirken hata: {e}")

async def _format_player_stats_message(stats: dict, player_id: str) -> str:
    """(DOKUNULMADI)"""
    
    # player_name'i stats'ten al
    player_name = stats.get("player_name", "Oyuncu")
    
    if not stats or stats.get("appearances", 0) == 0:
        logger.warning(f"Formatlayıcı: {player_name} için lig istatistiği bulunamadı (appearances=0).")
        return (
            f"👤 *{player_name}*\n"
            f"🆔 ID: {player_id}\n\n"
            "📊 *LİG İSTATİSTİKLERİ*\n\n"
            "ℹ️ Bu oyuncu için ligde sezon istatistiği bulunamadı."
        )

    message_parts = [
        f"👤 *{player_name}*",
        f"🆔 ID: {player_id}\n",
        "📊 *LİG İSTATİSTİKLERİ*\n",
        
        f"🏟️ Ligde Kaç Maç Oynadı: *{stats.get('appearances', 0)}*",
    ]

    started_count = stats.get('started', 0)
    if started_count > 0:
        message_parts.append(f"🏃 Ligde Kaç Maç İlk 11 Başladı: *{started_count}*")
    
    message_parts.extend([
        f"⏰ Maç Başına Dakika: *{stats.get('minutes_pg', 0.0):.1f}*\n",
        f"⚽ Maç Başına Şut: *{stats.get('shots_pg', 0.0):.1f}*",
        f"🎯 Maç Başına İsabetli Şut: *{stats.get('shots_on_target_pg', 0.0):.1f}*\n",
        f"👟 Maç Başına Pas: *{stats.get('passes_pg', 0.0):.1f}*",
        f"✅ Maç Başına İsabetli Pas: *{stats.get('accurate_passes_pg', 0.0):.1f}*\n",
        f"🛡️ Maç Başına Top Çalma: *{stats.get('interceptions_pg', 0.0):.1f}*",
        f"⚠️ Maç Başına Faul: *{stats.get('fouls_pg', 0.0):.1f}*",
        f"🤕 Maç Başına Kendisine Yapılan Faul: *{stats.get('was_fouled_pg', 0.0):.1f}*\n",
        f"🟨 Maç Başına Sarı Kart: *{stats.get('yellow_cards_pg', 0.0):.1f}*",
    ])
    
    return "\n".join(message_parts)

async def _format_player_basket_stats_message(stats: dict, player_id: str) -> str:
    """(DOKUNULMADI) GÜNCELLENDİ: Şut istatistikleri 'İsabet/Deneme (%Yüzde)' formatına getirildi."""
    
    # player_name'i stats'ten al
    player_name = stats.get("player_name", "Oyuncu")
    
    if not stats or stats.get("appearances", 0) == 0:
        logger.warning(f"Formatlayıcı: {player_name} (Basketbol) için lig istatistiği bulunamadı (appearances=0).")
        return (
            f"👤 *{player_name}*\n"
            f"🆔 ID: {player_id}\n\n"
            "📊 *LİG İSTATİSTİKLERİ*\n\n"
            "ℹ️ Bu oyuncu için bu ligde sezon istatistiği bulunamadı."
        )

    message_parts = [
        f"👤 *{player_name}*",
        f"🆔 ID: {player_id}\n",
        f"🏟️ Oynadığı Maç: *{stats.get('appearances', 0)}*\n",
        
        "📊 *LİG İSTATİSTİKLERİ (Maç Başına)*\n",
        
        # YENİ FORMAT (Takım istatistikleri gibi)
        f"🏀 *Sayı: {stats.get('ppg', 0.0):.1f}*\n",
        f" S. Atış: *{stats.get('ft_made_pg', 0.0):.1f}/{stats.get('ft_att_pg', 0.0):.1f} (%{stats.get('ft_pct', 0.0):.0f})*",
        f" 2 Sayı: *{stats.get('2p_made_pg', 0.0):.1f}/{stats.get('2p_att_pg', 0.0):.1f} (%{stats.get('2p_pct', 0.0):.0f})*",
        f" 3 Sayı: *{stats.get('3p_made_pg', 0.0):.1f}/{stats.get('3p_att_pg', 0.0):.1f} (%{stats.get('3p_pct', 0.0):.0f})*",
        f" Saha İçi: *{stats.get('fg_made_pg', 0.0):.1f}/{stats.get('fg_att_pg', 0.0):.1f} (%{stats.get('fg_pct', 0.0):.0f})*\n",
        
        # Diğer İstatistikler
        f"🧱 Ribaund: *{stats.get('rpg', 0.0):.1f}*",
        f"👟 Asist: *{stats.get('apg', 0.0):.1f}*",
        f"🖐️ Top Çalma: *{stats.get('spg', 0.0):.1f}*",
        f"🚫 Blok: *{stats.get('bpg', 0.0):.1f}*",
        f"⚠️ Top Kaybı: *{stats.get('tpg', 0.0):.1f}*",
    ]
    
    return "\n".join(message_parts)


# ###########################################################################
# # --- ANA İŞLEYİCİLER (HANDLER) ---
# # (Decorator'lar buradan kaldırıldı, ana handler'a eklendi)
# ###########################################################################

# --- FUTBOL: LİG SEÇİMİ (GÜNCELLENDİ) ---
async def listele_futbol_maclari_handler(
    query: CallbackQuery, 
    context: ContextTypes.DEFAULT_TYPE, 
    lig_id: str 
):
    """(GÜNCELLENDİ) Maç bulunamazsa Yenile butonu gösterir"""
    await query.edit_message_text(f"⌛ Seçilen futbol liginin maçları yükleniyor...")
    lig_adi_kisaltilmis = next((k for k, v in LIG_LISTESI.items() if v[1] == lig_id), None)
    lig_info = LIG_LISTESI.get(lig_adi_kisaltilmis)
    if not lig_info or not lig_adi_kisaltilmis:
         logger.error(f"Config'de lig ID '{lig_id}' bulunamadı.")
         await query.edit_message_text("🚨 Hata: Lig bilgisi bulunamadı.")
         return
    (emoji, unique_id, api_lig_id, api_season_id, fetch_type) = lig_info
    context.user_data['LAST_LIG_ID'] = unique_id
    if not api_lig_id or not api_season_id or api_lig_id == "1": 
        keyboard = [[
            InlineKeyboardButton("🏠 Menü", callback_data="MENU_ANAMENU"),
            InlineKeyboardButton("⬅️ Geri", callback_data="LIG_SECIM_GERI") 
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"ℹ️ Bu lig ({lig_adi_kisaltilmis}) için API ID'leri henüz `config.py` dosyasına girilmemiş.",
            reply_markup=reply_markup
        )
        return
    
    try:
        maclar = sfs_scraper.fetch_matches_from_sofascore(api_lig_id, api_season_id, fetch_type)
        
        if maclar is None:
            # API Hatası durumunda Tekrar Dene
            keyboard = [
                [InlineKeyboardButton("🔄 Tekrar Dene", callback_data=query.data)],
                [InlineKeyboardButton("🏠 Menü", callback_data="MENU_ANAMENU")]
            ]
            await query.edit_message_text(
                "🚨 Hata: Lig fikstürü şu anda yüklenemiyor. Lütfen tekrar deneyin.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        if not maclar:
            # Maç bulunamadı (Boş liste) durumunda Yenile Butonu
            keyboard = [
                [InlineKeyboardButton("🔄 Listeyi Yenile", callback_data=query.data)],
                [InlineKeyboardButton("⬅️ Geri (Lig Listesi)", callback_data="LIG_SECIM_GERI")]
            ]
            await query.edit_message_text(
                f"⚠️ {lig_adi_kisaltilmis} | Şu an için listelenecek aktif maç verisi çekilemedi.\n\n"
                "Veriler güncelleniyor olabilir veya fikstür açıklanmamış olabilir. Lütfen birazdan tekrar deneyin.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
            
        await _format_and_send_match_list(query, maclar, lig_adi_kisaltilmis, unique_id)
        
    except Exception as e:
        logger.error(f"listele_futbol_maclari_handler hatası: {e}", exc_info=True)
        keyboard = [[InlineKeyboardButton("🔄 Tekrar Dene", callback_data=query.data)]]
        await query.edit_message_text("🚨 Beklenmedik bir hata oluştu.", reply_markup=InlineKeyboardMarkup(keyboard))

# --- FUTBOL: MAÇ SEÇİMİ (GÜNCELLENDİ) ---
async def goster_futbol_mac_istatistikleri_handler(
    query: CallbackQuery, 
    context: ContextTypes.DEFAULT_TYPE, 
    match_id: str, 
    lig_id: str, 
    home_id: str, 
    away_id: str
):
    """(GÜNCELLENDİ) Hata durumunda Tekrar Dene butonu ekler"""
    logger.info(f"⚽ Futbol Maç İstatistikleri... Maç ID: {match_id}, Lig: {lig_id}")
    await query.edit_message_text(f"⌛ Maç istatistikleri yükleniyor...")
    
    try:
        lig_adi_kisaltilmis = next((k for k, v in LIG_LISTESI.items() if v[1] == lig_id), None)
        lig_info = LIG_LISTESI.get(lig_adi_kisaltilmis)
        if not lig_info:
            await query.edit_message_text("🚨 Hata: Lig bilgisi işlenemedi.")
            return
        (emoji, unique_id, api_lig_id, api_season_id, fetch_type) = lig_info
        
        context.user_data['LAST_LIG_ID'] = lig_id
        context.user_data['LAST_MATCH_DATA'] = {
            "match_id": match_id, 
            "lig_id": lig_id, 
            "home_id": home_id, 
            "away_id": away_id,
            "api_lig_id": api_lig_id, 
            "api_season_id": api_season_id 
        }
        context.user_data.pop('LAST_BASKET_MATCH_DATA', None)
        
        match_details = sfs_scraper.fetch_sofascore_match_details(match_id) 
        if not match_details:
            logger.error(f"❌ HATA: fetch_sofascore_match_details başarısız (Maç ID: {match_id}).")
            # Tekrar Dene butonu
            keyboard = [[InlineKeyboardButton("🔄 Tekrar Dene", callback_data=query.data)]]
            await query.edit_message_text(
                "🚨 Maç bilgileri şu anda çekilemiyor. Lütfen tekrar deneyin.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
            
        home_name = match_details["home_name"]
        home_short_name = match_details["home_shortName"]
        away_name = match_details["away_name"]
        away_short_name = match_details["away_shortName"]
        date_info = match_details["date_info"]
        round_number = match_details.get("round_number") 
        home_stats = sfs_scraper.fetch_football_team_stats(home_id, api_lig_id, api_season_id)
        away_stats = sfs_scraper.fetch_football_team_stats(away_id, api_lig_id, api_season_id)
        
        stats_text, stats_type = await _format_football_match_preview(
            home_stats, away_stats, 
            home_name, home_short_name, 
            away_name, away_short_name, 
            date_info
        )
        date_text = date_info
        message_title = (
            f"⚽ *MAÇ ÖNİZLEMESİ* ⚽\n" 
            f"*{home_name}* 🆚 *{away_name}*\n"
            f"📅 {date_text}\n" 
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        
        button_home_players = InlineKeyboardButton(f"👥 {home_short_name} Oyuncular", callback_data=f"PLAYER_LIST|{home_id}|{home_name}|0")
        button_away_players = InlineKeyboardButton(f"👥 {away_short_name} Oyuncular", callback_data=f"PLAYER_LIST|{away_id}|{away_name}|0")
        button_menu = InlineKeyboardButton("🏠 Menü", callback_data="MENU_ANAMENU")
        button_geri = InlineKeyboardButton("⬅️ Geri (Maç Listesi)", callback_data=f"LIG_SEC|{lig_id}") 
        keyboard_rows = [
            [button_home_players],
            [button_away_players],
            [button_menu, button_geri] 
        ]
        reply_markup = InlineKeyboardMarkup(keyboard_rows)
        await query.edit_message_text(
            text=message_title + stats_text, 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"goster_futbol_mac_istatistikleri_handler hatası: {e}", exc_info=True)
        # Hata durumunda Tekrar Dene butonu
        keyboard = [
            [InlineKeyboardButton("🔄 Tekrar Dene", callback_data=query.data)],
            [InlineKeyboardButton("🏠 Menü", callback_data="MENU_ANAMENU")]
        ]
        await query.edit_message_text(
            "⚠️ Veri çekilirken bir sorun oluştu.\nLütfen tekrar deneyin.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# --- OYUNCU LİSTESİ GÖSTERİCİ (GÜNCELLENDİ) ---
async def list_team_players_handler(
    query: CallbackQuery, 
    context: ContextTypes.DEFAULT_TYPE, 
    team_id: str, 
    team_name: str,
    page: int = 0 
):
    """(GÜNCELLENDİ) Hata durumunda Tekrar Dene butonu ekler"""
    await query.edit_message_text(f"⌛ {team_name} kadrosu yükleniyor... (Sayfa {page + 1})")
    
    try:
        players_data = sfs_scraper.fetch_team_players(team_id)
        
        if not players_data or not players_data.get("flat"):
            keyboard = [[InlineKeyboardButton("🔄 Tekrar Dene", callback_data=query.data)]]
            await query.edit_message_text(
                "🚨 Hata: Takım kadrosu şu anda çekilemiyor veya boş. Lütfen tekrar deneyin.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        # Sport type'a göre maç verisini al
        last_match_data = context.user_data.get('LAST_MATCH_DATA', {}) or context.user_data.get('LAST_BASKET_MATCH_DATA', {})
        
        await _format_and_send_player_list(
            query, 
            players_data, 
            team_name,
            team_id, 
            match_id=last_match_data.get('match_id', '0'), 
            lig_id=last_match_data.get('lig_id', '0'), 
            home_id=last_match_data.get('home_id', '0'), 
            away_id=last_match_data.get('away_id', '0'),
            page=page,
            context=context
        )
    except Exception as e:
        logger.error(f"list_team_players_handler hatası: {e}", exc_info=True)
        keyboard = [[InlineKeyboardButton("🔄 Tekrar Dene", callback_data=query.data)]]
        await query.edit_message_text(
            "🚨 Hata: Takım verisi işlenirken bir sorun oluştu.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# --- FUTBOL OYUNCU İSTATİSTİK GÖSTERİCİ (GÜNCELLENDİ) ---
async def goster_futbol_player_stats_handler(
    query: CallbackQuery, 
    context: ContextTypes.DEFAULT_TYPE, 
    player_id: str,
    page: int
):
    """(GÜNCELLENDİ) Hata durumunda Tekrar Dene butonu ekler"""
    logger.info(f"🔍 DEBUG: Futbol oyuncu handler çağrıldı - player_id: {player_id}, page: {page}")
    await query.edit_message_text(f"⌛ Oyuncu istatistikleri yükleniyor...")
    
    try:
        player_name = context.user_data.get(f'player_name_{player_id}')
        last_match_data = context.user_data.get('LAST_MATCH_DATA', {})
        api_lig_id = last_match_data.get('api_lig_id')
        api_season_id = last_match_data.get('api_season_id')
        
        if not api_lig_id or not api_season_id:
            logger.error(f"Oyuncu istatistikleri için context'te API ID'leri bulunamadı (P_ID: {player_id})")
            await query.edit_message_text("🚨 Hata: Lig bilgisi hafızadan okunamadı. Lütfen maça geri dönüp tekrar deneyin.")
            return

        player_stats = sfs_scraper.fetch_player_football_stats(player_id, api_lig_id, api_season_id, player_name)
            
        message_text = await _format_player_stats_message(player_stats, player_id,)
        
        button_geri = InlineKeyboardButton(
            "⬅️ Geri (Maça)", 
            callback_data=f"BACK_TO_MATCH|{last_match_data.get('match_id', '0')}|{last_match_data.get('lig_id', '0')}|{last_match_data.get('home_id', '0')}|{last_match_data.get('away_id', '0')}"
        )
        button_menu = InlineKeyboardButton("🏠 Menü", callback_data="MENU_ANAMENU")
        
        keyboard = [[button_menu, button_geri]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"goster_futbol_player_stats_handler hatası: {e}", exc_info=True)
        keyboard = [[InlineKeyboardButton("🔄 Tekrar Dene", callback_data=query.data)]]
        await query.edit_message_text(
            "🚨 Hata: Oyuncu istatistikleri işlenirken bir sorun oluştu.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# --- BASKETBOL: LİG SEÇİMİ (GÜNCELLENDİ) ---
async def listele_basketbol_maclari_handler(
    query: CallbackQuery, 
    context: ContextTypes.DEFAULT_TYPE, 
    lig_id: str 
):
    """(GÜNCELLENDİ) Maç bulunamazsa Yenile butonu gösterir"""
    await query.edit_message_text(f"⌛ Seçilen basketbol liginin maçları yükleniyor...")
    lig_adi_kisaltilmis = next((k for k, v in BASKETBOL_LIG_LISTESI.items() if v[1] == lig_id), None)
    lig_info = BASKETBOL_LIG_LISTESI.get(lig_adi_kisaltilmis)
    if not lig_info or not lig_adi_kisaltilmis:
         logger.error(f"Config'de lig ID '{lig_id}' bulunamadı.")
         await query.edit_message_text("🚨 Hata: Lig bilgisi bulunamadı.")
         return
    (emoji, unique_id, api_lig_id, api_season_id, fetch_type) = lig_info
    context.user_data['LAST_BASKET_LIG_ID'] = unique_id
    if not api_lig_id or not api_season_id:
        keyboard = [[
            InlineKeyboardButton("🏠 Menü", callback_data="MENU_ANAMENU"),
            InlineKeyboardButton("⬅️ Geri", callback_data="BASKET_SECIM_GERI") 
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"ℹ️ Bu lig ({lig_adi_kisaltilmis}) için API henüz tanımlanmamış.",
            reply_markup=reply_markup
        )
        return
        
    try:
        maclar = sfs_scraper.fetch_matches_from_sofascore(api_lig_id, api_season_id, fetch_type)
        
        if maclar is None:
            # API Hatası durumunda Tekrar Dene
            keyboard = [
                [InlineKeyboardButton("🔄 Tekrar Dene", callback_data=query.data)],
                [InlineKeyboardButton("🏠 Menü", callback_data="MENU_ANAMENU")]
            ]
            await query.edit_message_text(
                "🚨 Hata: Lig fikstürü şu anda yüklenemiyor. Lütfen tekrar deneyin.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        if not maclar:
            # Maç bulunamadı durumunda Yenile Butonu
            keyboard = [
                [InlineKeyboardButton("🔄 Listeyi Yenile", callback_data=query.data)],
                [InlineKeyboardButton("⬅️ Geri (Lig Listesi)", callback_data="BASKET_SECIM_GERI")]
            ]
            await query.edit_message_text(
                f"⚠️ {lig_adi_kisaltilmis} | Şu an için listelenecek aktif maç verisi çekilemedi.\n\n"
                "Veriler güncelleniyor olabilir veya fikstür açıklanmamış olabilir. Lütfen birazdan tekrar deneyin.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
            
        await _format_and_send_basket_match_list(query, maclar, lig_adi_kisaltilmis, unique_id)
        
    except Exception as e:
        logger.error(f"listele_basketbol_maclari_handler hatası: {e}", exc_info=True)
        keyboard = [[InlineKeyboardButton("🔄 Tekrar Dene", callback_data=query.data)]]
        await query.edit_message_text("🚨 Beklenmedik bir hata oluştu.", reply_markup=InlineKeyboardMarkup(keyboard))

# --- BASKETBOL: MAÇ SEÇİMİ (GÜNCELLENDİ) ---
async def goster_basketbol_mac_istatistikleri_handler(
    query: CallbackQuery, 
    context: ContextTypes.DEFAULT_TYPE, 
    match_id: str, 
    lig_id: str, 
    home_id: str, 
    away_id: str
):
    """(GÜNCELLENDİ) Hata durumunda Tekrar Dene butonu ekler"""
    await query.edit_message_text(f"🏀 Maç istatistikleri yükleniyor...")
    try:
        lig_adi_kisaltilmis = next((k for k, v in BASKETBOL_LIG_LISTESI.items() if v[1] == lig_id), None)
        lig_info = BASKETBOL_LIG_LISTESI.get(lig_adi_kisaltilmis)
        if not lig_info:
             raise ValueError(f"Config'de lig ID '{lig_id}' bulunamadı.")
        
        api_lig_id = lig_info[2]
        api_season_id = lig_info[3]
        
        if not api_lig_id or not api_season_id:
             raise ValueError(f"Config'de lig '{lig_id}' için API ID'leri eksik.")

        context.user_data['LAST_BASKET_LIG_ID'] = lig_id
        context.user_data['LAST_BASKET_MATCH_DATA'] = {
            "match_id": match_id,
            "lig_id": lig_id,
            "home_id": home_id,
            "away_id": away_id,
            "api_lig_id": api_lig_id, 
            "api_season_id": api_season_id 
        }
        # YENİ: Futbol context'ini temizle
        context.user_data.pop('LAST_MATCH_DATA', None)


        match_details = sfs_scraper.fetch_sofascore_match_details(match_id)
        if not match_details:
            keyboard = [[InlineKeyboardButton("🔄 Tekrar Dene", callback_data=query.data)]]
            await query.edit_message_text(
                "🚨 Hata: Maçın temel bilgileri çekilemedi. Lütfen tekrar deneyin.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
            
        home_name = match_details["home_name"]
        home_short_name = match_details["home_shortName"]
        away_name = match_details["away_name"]
        away_short_name = match_details["away_shortName"]
        date_info = match_details["date_info"]
        
        home_stats = sfs_scraper.fetch_basket_team_stats(home_id, api_lig_id, api_season_id)
        away_stats = sfs_scraper.fetch_basket_team_stats(away_id, api_lig_id, api_season_id)
        
        message_text = await _format_basket_match_preview(
            home_stats, away_stats, 
            home_name, home_short_name, 
            away_name, away_short_name, 
            date_info
        )
        
        button_home_players = InlineKeyboardButton(f"👥 {home_short_name} Oyuncular", callback_data=f"PLAYER_LIST|{home_id}|{home_name}|0")
        button_away_players = InlineKeyboardButton(f"👥 {away_short_name} Oyuncular", callback_data=f"PLAYER_LIST|{away_id}|{away_name}|0")
        button_menu = InlineKeyboardButton("🏠 Menü", callback_data="MENU_ANAMENU")
        button_geri = InlineKeyboardButton("⬅️ Geri (Maç Listesi)", callback_data=f"BASKET_SEC|{lig_id}") 
        
        keyboard_rows = [
            [button_home_players],
            [button_away_players],
            [button_menu, button_geri]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard_rows)
        await query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except (IndexError, ValueError, Exception) as e:
        logger.error(f"BASKET_MAC_SEC callback hatası: {e} (Veri: {query.data})", exc_info=True)
        # Hata durumunda Tekrar Dene butonu
        keyboard = [
            [InlineKeyboardButton("🔄 Tekrar Dene", callback_data=query.data)],
            [InlineKeyboardButton("🏠 Menü", callback_data="MENU_ANAMENU")]
        ]
        await query.edit_message_text(
            "⚠️ Veri çekilirken bir sorun oluştu.\nLütfen tekrar deneyin.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    return

# --- HAKEM İSTATİSTİK GÖSTERİCİ (DOKUNULMADI) ---
async def goster_hakem_istatistikleri_handler(
    query: CallbackQuery, 
    context: ContextTypes.DEFAULT_TYPE, 
    referee_id: str
):
    """(DOKUNULMADI)"""
    await query.edit_message_text(f"⌛ Hakem (ID: {referee_id}) bilgileri yükleniyor...")
    stats_data = tm_scraper.fetch_referee_stats(referee_id)
    if not stats_data:
        await query.edit_message_text("🚨 Hata: Hakem verileri şu anda çekilemiyor veya profil bulunamadı.")
        return
    referee_name = stats_data["name"]
    current_season = stats_data["season"]
    stats = stats_data["stats"]
    last_5_matches = stats_data["last_5_matches"]
    matches_managed = stats["matches"]
    total_yellow_for_avg = stats["yellow"] + stats["yellow_red"]
    total_penalty = stats["penalty"]
    if matches_managed > 0:
        avg_yellow_calc = total_yellow_for_avg / matches_managed 
        avg_penalty_calc = total_penalty / matches_managed
        avg_yellow_str = f"{avg_yellow_calc:.2f}"
        avg_penalty_str = f"{avg_penalty_calc:.2f}"
    else:
        avg_yellow_str = "N/A"
        avg_penalty_str = "N/A"
    message_parts = [
        f"👨‍⚖️ *Hakem: {referee_name}*",
        f"📅 *Sezon: {current_season}*",
        f"🆔 ID: *{referee_id}*",
        f"📊 Bu sezon *{matches_managed} maç* yönetti",
        "\n",
        "📉 *Sezon Ortalamaları (Maç Başına):*",
        f"├ 🟨 Sarı Kart: *{avg_yellow_str}*",
        f"└ ⚡ Penaltı: *{avg_penalty_str}*", "\n",
        "📋 *SON 5 MAÇ KART İSTATİSTİKLERİ*"
    ]
    if last_5_matches:
        month_map_tr = {
            'Aug': 'Ağu', 'Sep': 'Eyl', 'Oct': 'Eki', 'Nov': 'Kas', 'Dec': 'Ara', 
            'Jan': 'Oca', 'Feb': 'Şub', 'Mar': 'Mar', 'Apr': 'Nis', 'May': 'May', 'Jun': 'Haz', 'Jul': 'Tem'
        }
        for i, match_data in enumerate(last_5_matches):
            formatted_date = match_data['date_obj'].strftime('%d %b %Y')
            formatted_date = formatted_date.split()
            formatted_date[1] = month_map_tr.get(formatted_date[1], formatted_date[1])
            formatted_date = " ".join(formatted_date)
            total_red_display = match_data['red'] + match_data['yellow_red'] 
            message_parts.append(f"\n*{i+1}. {match_data['match']}*")
            message_parts.append(f"   📅 {formatted_date} | 🟨 *{match_data['yellow']} Sarı* | 🟥 *{total_red_display} Kırmızı*") 
    else:
        message_parts.append("\n_Son 5 maça ait veri bulunamadı._")
    final_message = "\n".join(message_parts)
    keyboard = [[
        InlineKeyboardButton("⬅️ Geri (Arama)", callback_data="HAKEM_ARAMA_GERI")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await query.edit_message_text(
            text=final_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        if 'message is not modified' not in str(e):
             logger.warning(f"Hakem istatistikleri gönderilirken hata: {e}")

# --- BASKETBOL OYUNCU İSTATİSTİK GÖSTERİCİ (GÜNCELLENDİ) ---
async def goster_basketbol_player_stats_handler(
    query: CallbackQuery, 
    context: ContextTypes.DEFAULT_TYPE, 
    player_id: str,
    page: int
):
    """(GÜNCELLENDİ) Hata durumunda Tekrar Dene butonu ekler"""
    logger.info(f"🔍 DEBUG: Basketbol oyuncu handler çağrıldı - player_id: {player_id}, page: {page}")
    await query.edit_message_text(f"⌛ Oyuncu istatistikleri yükleniyor...")
    
    try:
        player_name = context.user_data.get(f'player_name_{player_id}')
        last_match_data = context.user_data.get('LAST_BASKET_MATCH_DATA', {})
        api_lig_id = last_match_data.get('api_lig_id')
        api_season_id = last_match_data.get('api_season_id')
        
        if not api_lig_id or not api_season_id:
            logger.error(f"Basketbol oyuncu istatistikleri için API ID'leri bulunamadı")
            await query.edit_message_text("🚨 Hata: Lig bilgisi bulunamadı.")
            return

        player_stats = sfs_scraper.fetch_player_basket_stats(player_id, api_lig_id, api_season_id, player_name)
        
        if not player_stats:
            keyboard = [[InlineKeyboardButton("🔄 Tekrar Dene", callback_data=query.data)]]
            await query.edit_message_text(
                f"🚨 Hata: Oyuncu için lig istatistikleri bulunamadı.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
            
        message_text = await _format_player_basket_stats_message(player_stats, player_id)
        
        # Geri butonu için team_id'yi context'ten al
        team_id = last_match_data.get('home_id') or last_match_data.get('away_id')
        
        button_geri = InlineKeyboardButton(
            "⬅️ Geri (Maça)", 
            callback_data=f"BACK_TO_BASKET_MATCH|{last_match_data.get('match_id', '0')}|{last_match_data.get('lig_id', '0')}|{last_match_data.get('home_id', '0')}|{last_match_data.get('away_id', '0')}"
        )
        
        button_menu = InlineKeyboardButton("🏠 Menü", callback_data="MENU_ANAMENU")
        
        keyboard = [[button_menu, button_geri]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"goster_basketbol_player_stats_handler hatası: {e}", exc_info=True)
        keyboard = [[InlineKeyboardButton("🔄 Tekrar Dene", callback_data=query.data)]]
        await query.edit_message_text(
            "🚨 Hata: Oyuncu istatistikleri işlenirken sorun oluştu.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ###########################################################################
# # --- ANA CALLBACK YÖNLENDİRİCİSİ (GÜNCELLENDİ) ---
# ###########################################################################

@log_command # YENİ: Decorator'ı ana callback handler'a ekle
async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # try...except ve zamanlayıcı mantığı artık decorator'da olduğu için
    # bu fonksiyonun içinden SİLİNDİ. Sadece yönlendirme yapıyor.
    
    query = update.callback_query
    await query.answer() 
    data = query.data
    
    # logger.info(f"🔍 DEBUG: Callback data: {data}") # Artık bot_logger.py bunu yapıyor
    
    if data == "MENU_ANAMENU":
        try:
            help_text = (
                "👋 Merhaba! Ben İstatistik Botu.\n\n"
                "Aşağıdaki komutları kullanarak arama yapabilirsin:\n"
                "\n"
                "➡️ */futbol*\n"
                "Futbol liglerindeki maçları ve istatistikleri görüntüler.\n\n"
                "➡️ */basketbol*\n"
                "Basketbol liglerindeki maçları ve istatistikleri görüntüler.\n\n"
                "➡️ */hakem [isim]*\n"
                "Hakemlere ait son 5 maç ve genel sezon istatistiklerini görüntüler."
            )
            await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=None) 
        except Exception as e:
            # Butona çift tıklamayı veya aynı mesajı düzenlemeyi engelle
            if 'message is not modified' not in str(e):
                logger.warning(f"MENU_ANAMENU hatası: {e}")
        return
    
    # Hata yakalama blokları (try...except) decorator'a taşındığı için
    # buradan kaldırıldı. Kod artık daha temiz.
    
    if data == "LIG_SECIM_GERI":
        await _go_back_to_futbol_menu(query)
        return
        
    if data.startswith("LIG_SEC|"):
        lig_id = data.split('|')[1] 
        context.user_data['LAST_LIG_ID'] = lig_id 
        await listele_futbol_maclari_handler(query, context, lig_id=lig_id)
        return
        
    if data.startswith("MAC_SEC|"):
        parts = data.split('|')
        match_id, lig_id, home_id, away_id = parts[1], parts[2], parts[3], parts[4]
        await goster_futbol_mac_istatistikleri_handler(
            query, context, match_id, lig_id, home_id, away_id
        )
        return
        
    if data.startswith("BACK_TO_MATCH|"):
        parts = data.split('|')
        match_id, lig_id, home_id, away_id = parts[1], parts[2], parts[3], parts[4]
        await goster_futbol_mac_istatistikleri_handler(
            query, context, match_id, lig_id, home_id, away_id
        )
        return

    if data == "BASKET_SECIM_GERI":
        await _go_back_to_basketbol_menu(query)
        return
        
    if data.startswith("BASKET_SEC|"):
        lig_id = data.split('|')[1] 
        await listele_basketbol_maclari_handler(query, context, lig_id)
        return
        
    if data.startswith("BASKET_MAC_SEC|"):
        parts = data.split('|')
        match_id, lig_id, home_id, away_id = parts[1], parts[2], parts[3], parts[4]
        await goster_basketbol_mac_istatistikleri_handler(
            query, context, match_id, lig_id, home_id, away_id
        )
        return
        
    if data.startswith("BACK_TO_BASKET_MATCH|"):
        parts = data.split('|')
        match_id, lig_id, home_id, away_id = parts[1], parts[2], parts[3], parts[4]
        await goster_basketbol_mac_istatistikleri_handler(
            query, context, match_id, lig_id, home_id, away_id
        )
        return

    if data.startswith("PLAYER_LIST|"):
        parts = data.split('|')
        team_id, team_name, page = parts[1], parts[2], int(parts[3])
        await list_team_players_handler(
            query, context, team_id, team_name, page=page
        )
        return

    if data.startswith("PLAYER_LIST_PAGE|"):
        parts = data.split('|')
        page = int(parts[1])
        team_id = parts[2]
        team_name = parts[3] 
        await list_team_players_handler(
            query, context, team_id, team_name, page=page
        )
        return
        
    if data.startswith("PLAYER_STATS|"):
        parts = data.split('|')
        player_id, page = parts[1], int(parts[2])
        await goster_futbol_player_stats_handler(
            query, context, player_id, page
        )
        return

    if data.startswith("BASKET_PLAYER_STATS|"):
        parts = data.split('|')
        player_id, page = parts[1], int(parts[2])
        await goster_basketbol_player_stats_handler(
            query, context, player_id, page
        )
        return

    if data == "HAKEM_ARAMA_GERI":
        await _go_back_to_hakem_arama(query, context)
        return
        
    if data.startswith("HAKEM_SEC|"):
        referee_id = data.split('|')[1]
        await goster_hakem_istatistikleri_handler(query, context, referee_id)
        return