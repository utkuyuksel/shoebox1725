# -*- coding: utf-8 -*-
# scraping/transfermarkt.py
"""
GÜNCELLEME: Bu dosya, 'eski_proje'deki çalışan Transfermarkt scraper'ı
(cloudscraper kullanan) ile değiştirilmiştir.
Sadece hakem fonksiyonları (`fetch_referee_stats`) alınmış,
/futbol ve /basketbol ile çakışmaması için diğer fonksiyonlar (maç listesi vs.)
temizlenmiştir.
"""
import cloudscraper
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time 
import requests # cloudscraper'ın exception'ları için gerekli olabilir

# Proje içi importlar
from config import logger, HEADERS, TM_BASE_URL
# Not: Lig listesi veya cache importları bu dosyadan kaldırıldı,
# çünkü onlar /ligler (eski) sistemine aitti.

# --- GÜVENİLİR SCRAPER OTURUMU ---
def _get_scraper_session():
    """Yeniden deneme mekanizmalı bir cloudscraper oturumu başlatır."""
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'linux', 'mobile': False},
        delay=10
    )
    scraper.headers.update(HEADERS)
    return scraper

# --- ANA FONKSİYONLAR ---

def fetch_referee_stats(referee_id: str) -> dict | None:
    """Belirli bir hakemin istatistiklerini çeker (Ağ denemeli)."""
    
    referee_url = f"{TM_BASE_URL}/-/profil/schiedsrichter/{referee_id}"
    scraper = _get_scraper_session()
    
    for attempt in range(3):
        try:
            response = scraper.get(referee_url, timeout=20)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # --- Veri Çekim Mantığı ---
                referee_name = "Bilinmiyor"
                name_element = soup.find('div', class_='data-header__headline-container')
                if name_element and name_element.find('h1'):
                    referee_name = name_element.find('h1').text.strip().split('\n')[0].strip()

                current_season = "Mevcut Sezon"
                season_select = soup.find('select', {'name': 'saison_id'})
                if season_select and season_select.find('option', selected=True):
                     current_season = season_select.find('option', selected=True).text.strip()
                
                matches, yellow, yellow_red, red, penalty = 0, 0, 0, 0, 0

                stats_table = soup.find('div', class_='responsive-table')
                if stats_table and stats_table.find('table', class_='items'):
                    total_row = stats_table.find('tfoot').find('tr') if stats_table.find('tfoot') else None
                    if total_row:
                        total_cols = total_row.find_all('td')
                        if len(total_cols) >= 7:
                            matches = int(total_cols[2].text.strip().replace('.', '') or 0)
                            yellow = int(total_cols[3].text.strip().replace('.', '') or 0)
                            yellow_red = int(total_cols[4].text.strip().replace('.', '') or 0)
                            red = int(total_cols[5].text.strip().replace('.', '') or 0)
                            penalty = int(total_cols[6].text.strip().replace('.', '') or 0)
                
                all_matches_data = []
                match_boxes = soup.find_all('div', class_='box')
                for box in match_boxes:
                    headline = box.find('div', class_='content-box-headline')
                    if headline and 'content-box-headline--logo' in headline.get('class', []):
                        match_table = box.find('div', class_='responsive-table')
                        if match_table and match_table.find('table'):
                            # --- GÜNCELLEME (tbody eklendi) ---
                            match_body = match_table.find('tbody')
                            if not match_body:
                                match_body = match_table
                            # --- GÜNCELLEME SONU ---

                            match_rows = match_body.find_all('tr')
                            for row in match_rows:
                                cols = row.find_all('td')
                                if len(cols) >= 11:
                                    match_date_str = cols[1].text.strip()
                                    try:
                                        month_map = {'Oca': 'Jan', 'Şub': 'Feb', 'Mar': 'Mar', 'Nis': 'Apr', 'May': 'May', 'Haz': 'Jun', 'Tem': 'Jul', 'Ağu': 'Aug', 'Eyl': 'Sep', 'Eki': 'Oct', 'Kas': 'Nov', 'Ara': 'Dec'}
                                        match_date_temp = match_date_str
                                        for tr, en in month_map.items():
                                            match_date_temp = match_date_temp.replace(tr, en)
                                        match_date_obj = datetime.strptime(match_date_temp, '%d %b %Y')
                                        
                                        home_team_name = cols[3].find('a').text.strip() if cols[3].find('a') else "Ev Sahibi"
                                        away_team_name = cols[5].find('a').text.strip() if cols[5].find('a') else "Konuk Takım"
                                        
                                        # --- GÜNCELLEME (Güvenli int dönüşümü) ---
                                        def safe_int(text):
                                            cleaned = text.strip()
                                            if not cleaned or cleaned == '-':
                                                return 0
                                            return int(cleaned)
                                        # --- GÜNCELLEME SONU ---

                                        all_matches_data.append({
                                            "date_obj": match_date_obj,
                                            "match": f"{home_team_name} vs {away_team_name}",
                                            "yellow": safe_int(cols[7].text),
                                            "yellow_red": safe_int(cols[8].text),
                                            "red": safe_int(cols[9].text)
                                        })
                                    except Exception as e:
                                        logger.warning(f"Hakem maçı işlenirken tarih/veri hatası: {e} | Satır: {row.text.strip()}")
                                        continue
                
                all_matches_data.sort(key=lambda x: x['date_obj'], reverse=True)
                
                return {
                    "name": referee_name,
                    "season": current_season,
                    "stats": {
                        "matches": matches,
                        "yellow": yellow,
                        "yellow_red": yellow_red,
                        "red": red,
                        "penalty": penalty
                    },
                    "last_5_matches": all_matches_data[:5]
                }
            
            else:
                logger.warning(f"TM Hakem (Deneme {attempt+1}): {response.status_code} hatası.")
                time.sleep(1) 
        
        # 'requests' importu bu 'except' bloğu için gerekliydi
        except (cloudscraper.exceptions.CloudflareChallengeError, 
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.RequestException) as e:
            logger.warning(f"TM Hakem (Deneme {attempt+1}): Ağ hatası: {e}")
            time.sleep(1) 
        except Exception as e:
            logger.error(f"TM Hakem (Deneme {attempt+1}): Beklenmedik hata: {e}", exc_info=True)
            time.sleep(1)
            
    logger.error(f"❌ HATA: TM Hakem {referee_id} verisi 3 denemede çekilemedi.")
    return None

# --- ESKİ PROJEDEN GELEN /LIGLER FONKSİYONLARI ---
# --- GÜNCEL PROJEDE /futbol OLDUĞU İÇİN TAMAMEN KALDIRILDI ---
# fetch_future_matches
# fetch_match_details
# _find_tab_id_by_text
# _parse_matches_from_tab