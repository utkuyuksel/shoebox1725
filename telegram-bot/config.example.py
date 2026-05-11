# -*- coding: utf-8 -*-
# config.example.py
#
# Copy this file to `config.py` and fill in real values. `config.py` is
# .gitignored so the real bot token and proxy credentials never end up
# in the repo.

import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- SECRETS ---
TOKEN = "REPLACE_WITH_TELEGRAM_BOT_TOKEN"
SOFASCORE_API_BASE_URL = "https://www.sofascore.com/api/v1/unique-tournament"

# Residential proxy in "http://user:pass@ip:port" format. Leave None to skip.
PROXY_URL = None

# --- Headers used by the Sofascore client ---
SOFASCORE_HEADERS = {
    "Accept": "*/*",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
}

# --- Transfermarkt (referee scraping) ---
TM_BASE_URL = "https://www.transfermarkt.com.tr"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
    "Referer": "https://www.transfermarkt.com.tr/",
}

# --- League tables (football) ---
LIG_LISTESI = {
    "Süper Lig":      ("🇹🇷", "TR_SL", "52", "77805", "round"),
    "Premier League": ("🇬🇧", "GB_PL", "17", "76986", "round"),
    "La Liga":        ("🇪🇸", "ES_LL", "8",  "77559", "round"),
    "Serie A":        ("🇮🇹", "IT_SA", "23", "76457", "round"),
    "Bundesliga":     ("🇩🇪", "DE_BL", "35", "77333", "round"),
    "Ligue 1":        ("🇫🇷", "FR_L1", "34", "77356", "round"),
}

# --- League tables (basketball) ---
BASKETBOL_LIG_LISTESI = {
    "NBA":              ("🇺🇸", "NBA",     "132", "80229", "date"),
    "Euroleague":       ("🇪🇺", "EUROLIG", "138", "78545", "round"),
    "Eurocup":          ("🇪🇺", "EUROCUP", "141", "77910", "round"),
    "Türkiye BSL":      ("🇹🇷", "BSL",     "519", "81036", "round"),
    "Almanya BBL":      ("🇩🇪", "BBL",     "227", "79994", "round"),
    "İspanya Liga ACB": ("🇪🇸", "ACB",     "264", "80922", "round"),
}
