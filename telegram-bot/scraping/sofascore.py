# -*- coding: utf-8 -*-
# scraping/sofascore.py
"""
Sofascore API'sinden basketbol VE FUTBOL verilerini çeker.

GÜNCELLEME: Cache (Ön Bellek) Sistemi Entegre Edildi.
Her denemede yeni oturum açarak Cloudflare/Rate Limit blokajlarını aşmayı dener.
"""
from curl_cffi import requests
from config import logger, SOFASCORE_API_BASE_URL, SOFASCORE_HEADERS, PROXY_URL
from utils import format_timestamp_to_date, format_timestamp_to_date_short
import time
from datetime import datetime, timedelta

# YENİ: Cache yöneticisini import et (Dosyanın config.py ile aynı dizinde olduğu varsayılmıştır)
try:
    from cache_system import cache_manager
except ImportError:
    logger.warning("⚠️ Cache sistemi bulunamadı! Caching devre dışı çalışacak.")
    # Fallback: Dummy cache manager
    class DummyCache:
        def get_data(self, *args): return None
        def set_data(self, *args): pass
        def get_cached_round(self, *args): return None
        def set_cached_round(self, *args): pass
    cache_manager = DummyCache()

# --- REQUESTS OTURUMU OLUŞTURMA ---
def get_session():
    """
    Gerçek bir Chrome tarayıcısı gibi davranan (impersonate) ve
    varsa Proxy ayarlarını kullanan bir session oluşturur.
    """
    session = requests.Session()
    session.impersonate = "chrome120" # Chrome 120 sürümü taklidi
    session.headers = SOFASCORE_HEADERS
    
    if PROXY_URL:
        session.proxies = {"http": PROXY_URL, "https": PROXY_URL}
        
    return session

def _log_error_details(url: str, response=None, error=None, context="API İsteği"):
    """
    Hataları standart ve detaylı bir formatta loglar.
    """
    error_msg = f"🚨 {context} BAŞARISIZ | URL: {url}"
    
    if response is not None:
        error_msg += f"\n   ├ Durum Kodu: {response.status_code}"
        try:
            preview = response.text[:500].replace('\n', ' ') 
            error_msg += f"\n   └ Yanıt (İlk 500kr): {preview}"
        except:
            error_msg += "\n   └ Yanıt içeriği okunamadı."
            
    if error:
        error_msg += f"\n   └ Exception: {str(error)}"
    
    logger.error(error_msg, exc_info=True if error else False)

# --- GÜVENLİ İSTEK MEKANİZMASI (RETRY - EXPONENTIAL BACKOFF) ---
def _request_with_retry(url: str, context: str, max_retries: int = 3, timeout: int = 15):
    """
    Belirtilen URL'ye istek atar. Başarısız olursa belirtilen sayıda tekrar dener.
    """
    last_error = None
    last_response = None

    for attempt in range(max_retries):
        session = get_session()
        
        try:
            response = session.get(url, timeout=timeout)
            last_response = response
            
            if response.status_code == 200:
                return response
            
            if response.status_code == 404:
                return response

            logger.warning(f"⚠️ {context} - Deneme {attempt+1}/{max_retries} Başarısız (Status: {response.status_code})")
            
        except Exception as e:
            last_error = e
            logger.warning(f"⚠️ {context} - Deneme {attempt+1}/{max_retries} Ağ Hatası: {e}")
        
        finally:
            try:
                session.close()
            except:
                pass

        if attempt < max_retries - 1:
            sleep_time = 2 ** attempt 
            time.sleep(sleep_time)

    _log_error_details(url, response=last_response, error=last_error, context=f"{context} (Tüm Denemeler Başarısız)")
    return None

# ###########################################################################
# # --- YENİ: HAFTA (ROUND) VE TARİH YÖNETİMİ ---
# ###########################################################################

def get_current_round_or_date(api_lig_id: int, api_season_id: int, fetch_type: str) -> str:
    """
    Ligin o anki 'Round' bilgisini veya NBA ise 'Tarih' bilgisini döner.
    Bu bilgi Cache Key'in bir parçası olacaktır.
    """
    # 1. NBA / Basketbol Tarih Bazlı ise
    if fetch_type == 'date':
        return datetime.now().strftime("%Y-%m-%d")

    # 2. Round Bazlı ise (Futbol & Euroleague)
    cached_round = cache_manager.get_cached_round(str(api_lig_id))
    if cached_round:
        return str(cached_round)

    real_round = _fetch_current_round_api(api_lig_id, api_season_id)
    if real_round:
        cache_manager.set_cached_round(str(api_lig_id), str(real_round))
        return str(real_round)
    
    return "unknown"

def _fetch_current_round_api(api_lig_id: int, api_season_id: int) -> int | None:
    """API'den güncel raundu çeker (Cache kullanmaz, helper fonksiyon)."""
    url = f"{SOFASCORE_API_BASE_URL}/{api_lig_id}/season/{api_season_id}/rounds"
    response = _request_with_retry(url, context="Raund Bilgisi Çekme")
    
    if response and response.status_code == 200:
        try:
            data = response.json()
            current_round = data.get("currentRound", {}).get("round")
            if current_round:
                return int(current_round)
            else:
                rounds = data.get("rounds", [])
                if rounds: return 1
        except Exception as e:
            _log_error_details(url, error=e, context="Raund JSON Parse")
    return None

# ###########################################################################
# # --- MAÇ LİSTESİ ÇEKME ---
# ###########################################################################

def _parse_events_json(data: dict, log_prefix: str, api_lig_id_filter: int | None = None) -> list:
    matches = []
    if "events" not in data:
        logger.warning(f"⚠️ {log_prefix}: API yanıtında 'events' anahtarı yok.")
        return []
        
    for event in data["events"]:
        status_type = event.get("status", {}).get("type")
        if status_type == "notstarted":
            try:
                if api_lig_id_filter:
                    event_lig_id = event.get("tournament", {}).get("uniqueTournament", {}).get("id")
                    if event_lig_id != api_lig_id_filter:
                        continue 
                
                home_team_data = event.get("homeTeam", {})
                away_team_data = event.get("awayTeam", {})
                
                if not home_team_data or not away_team_data:
                    continue 
                    
                match_id = event["id"]
                timestamp = event["startTimestamp"]
                
                matches.append({
                    'tarih_saat': format_timestamp_to_date(timestamp),
                    'ev_sahibi': home_team_data.get("name"),
                    'konuk': away_team_data.get("name"),
                    'id': match_id,
                    'home_id': home_team_data.get("id"), 
                    'away_id': away_team_data.get("id"),
                    'timestamp': timestamp 
                })
            except Exception as e:
                logger.warning(f"⚠️ Maç parse edilirken hata (ID: {event.get('id')}): {e}")
                continue
                
    matches.sort(key=lambda x: x['timestamp']) 
    logger.info(f"✅ {log_prefix}: {len(matches)} maç bulundu.")
    return matches

def _fetch_matches_by_round(api_lig_id: int, api_season_id: int, current_round: int = None) -> list | None:
    # Eğer current_round verilmemişse (cache sisteminden gelmiyorsa) API'den bul
    if not current_round:
        current_round = _fetch_current_round_api(api_lig_id, api_season_id)
        if not current_round:
            return []
        
    url = f"{SOFASCORE_API_BASE_URL}/{api_lig_id}/season/{api_season_id}/events/round/{current_round}"
    
    response = _request_with_retry(url, context=f"Maç Listesi (Round {current_round})")
    
    if not response or response.status_code != 200:
        return None

    try:
        matches = _parse_events_json(response.json(), f"Round {current_round}")
        
        if not matches:
            # Bu hafta maç yoksa bir sonraki haftayı dene
            next_round = current_round + 1
            url_next = f"{SOFASCORE_API_BASE_URL}/{api_lig_id}/season/{api_season_id}/events/round/{next_round}"
            logger.info(f"ℹ️ Bu hafta maç yok, sonraki hafta deneniyor (Round {next_round})...")
            
            response_next = _request_with_retry(url_next, context=f"Maç Listesi (Round {next_round})")
            
            if response_next and response_next.status_code == 200:
                matches = _parse_events_json(response_next.json(), f"Round {next_round}")
                
        return matches
        
    except Exception as e:
        _log_error_details(url, error=e, context="Maç Listesi JSON Parse")
        return None

def _fetch_matches_by_date(api_lig_id: int, api_season_id: int) -> list | None:
    url = f"{SOFASCORE_API_BASE_URL}/{api_lig_id}/season/{api_season_id}/events/next/0"
    
    response = _request_with_retry(url, context="Maç Listesi (Date)")
    
    if not response:
        return None
        
    if response.status_code == 404:
        logger.warning(f"ℹ️ Gelecek maç bulunamadı (404) - Lig: {api_lig_id}")
        return []
        
    if response.status_code != 200:
        return None
            
    try:
        return _parse_events_json(response.json(), "Date", api_lig_id_filter=api_lig_id) 
    except Exception as e:
        _log_error_details(url, error=e, context="Maç Listesi (Date) JSON Parse")
        return None

def fetch_matches_from_sofascore(api_lig_id: str, api_season_id: str, fetch_type: str) -> list | None:
    """
    (GÜNCELLENDİ) Cache kontrollü ana maç çekme fonksiyonu.
    """
    try:
        api_lig_id_int = int(api_lig_id)
        api_season_id_int = int(api_season_id)
    except (ValueError, TypeError):
        logger.error(f"🚨 Konfigürasyon Hatası: Lig ID ({api_lig_id}) veya Sezon ID ({api_season_id}) sayı değil.")
        return None

    # 1. Şu anki haftayı/tarihi belirle (Cache Key için kritik)
    current_key_suffix = get_current_round_or_date(api_lig_id_int, api_season_id_int, fetch_type)
    
    # 2. Cache Kontrolü
    cache_id = f"{api_lig_id}_{api_season_id}"
    cached_matches = cache_manager.get_data("matches", cache_id, current_key_suffix)
    
    if cached_matches is not None:
        return cached_matches

    # 3. Cache Yoksa API'den Çek
    matches = None
    if fetch_type == "round":
        # suffix sayı ise round olarak gönder, değilse None (API bulsun)
        round_num = int(current_key_suffix) if current_key_suffix.isdigit() else None
        matches = _fetch_matches_by_round(api_lig_id_int, api_season_id_int, round_num)
    elif fetch_type == "date":
        matches = _fetch_matches_by_date(api_lig_id_int, api_season_id_int)
    else:
        logger.error(f"🚨 Bilinmeyen fetch_type: {fetch_type}")
        return None

    # 4. Veri geldiyse Cache'e yaz (Boş liste olsa bile, çünkü o hafta maç yok demektir)
    if matches is not None:
        cache_manager.set_data("matches", cache_id, current_key_suffix, matches)
    
    return matches

def fetch_sofascore_match_details(match_id: str) -> dict | None:
    # Maç detayı (skor, saat vb.) anlık değişebildiği için kısa süreli cache yapılabilir
    # ama şimdilik doğrudan çekiyoruz.
    url = f"https://www.sofascore.com/api/v1/event/{match_id}"
    
    response = _request_with_retry(url, context=f"Maç Detayı ({match_id})")
    
    if not response or response.status_code != 200:
        return None
            
    try:
        event = response.json().get("event", {})
        home_team = event.get("homeTeam", {})
        away_team = event.get("awayTeam", {})
        
        return {
            "home_name": home_team.get("name"),
            "home_shortName": home_team.get("shortName", home_team.get("name")), 
            "away_name": away_team.get("name"),
            "away_shortName": away_team.get("shortName", away_team.get("name")), 
            "date_info": format_timestamp_to_date(event.get("startTimestamp")),
            "round_number": event.get("roundInfo", {}).get("round") 
        }
    except Exception as e:
        _log_error_details(url, error=e, context="Maç Detayı JSON Parse")
        return None

# ###########################################################################
# # --- TAKIM İSTATİSTİKLERİ ---
# ###########################################################################

def _parse_basket_stats_json(stats_data: dict, team_id_for_nba: int) -> tuple[dict, int]:
    # ... (Mevcut kodun aynısı) ...
    if "ranks" in stats_data: 
        stats = stats_data.get("ranks", {})
        matches = stats_data.get("matches", 0)
        return {
            "points": stats.get("points", {}).get("value", 0),
            "pointsAgainst": stats.get("pointsAgainst", {}).get("value", 0),
            "fieldGoalsPercentage": stats.get("fieldGoalsPercentage", {}).get("value", 0.0),
            "twoPointsPercentage": stats.get("twoPointsPercentage", {}).get("value", 0.0),
            "threePointsPercentage": stats.get("threePointsPercentage", {}).get("value", 0.0),
            "freeThrowsPercentage": stats.get("freeThrowsPercentage", {}).get("value", 0.0),
            "twoPointsMade": stats.get("twoPointsMade", {}).get("value", 0),
            "twoPointAttempts": stats.get("twoPointAttempts", {}).get("value", 0),
            "threePointsMade": stats.get("threePointsMade", {}).get("value", 0),
            "threePointAttempts": stats.get("threePointAttempts", {}).get("value", 0),
            "freeThrowsMade": stats.get("freeThrowsMade", {}).get("value", 0),
            "freeThrowAttempts": stats.get("freeThrowAttempts", {}).get("value", 0),
            "offensiveRebounds": stats.get("offensiveRebounds", {}).get("value", 0),
            "defensiveRebounds": stats.get("defensiveRebounds", {}).get("value", 0),
            "assists": stats.get("assists", {}).get("value", 0),
            "turnovers": stats.get("turnovers", {}).get("value", 0),
            "steals": stats.get("steals", {}).get("value", 0),
            "blocks": stats.get("blocks", {}).get("value", 0),
        }, matches
    elif "statistics" in stats_data: 
        stats = stats_data.get("statistics", {})
        matches = stats.get("matches", 0) 
        return {
            "points": stats.get("points", 0),
            "pointsAgainst": stats.get("pointsAgainst", 0),
            "fieldGoalsPercentage": stats.get("fieldGoalsPercentage", 0.0),
            "twoPointsPercentage": stats.get("twoPointsPercentage", 0.0),
            "threePointsPercentage": stats.get("threePointsPercentage", 0.0),
            "freeThrowsPercentage": stats.get("freeThrowsPercentage", 0.0),
            "twoPointsMade": stats.get("twoPointsMade", 0),
            "twoPointAttempts": stats.get("twoPointAttempts", 0),
            "threePointsMade": stats.get("threePointsMade", 0),
            "threePointAttempts": stats.get("threePointAttempts", 0),
            "freeThrowsMade": stats.get("freeThrowsMade", 0),
            "freeThrowAttempts": stats.get("freeThrowAttempts", 0),
            "offensiveRebounds": stats.get("offensiveRebounds", 0),
            "defensiveRebounds": stats.get("defensiveRebounds", 0),
            "assists": stats.get("assists", 0),
            "turnovers": stats.get("turnovers", 0),
            "steals": stats.get("steals", 0),
            "blocks": stats.get("blocks", 0),
        }, matches
    elif "standings" in stats_data: 
        try:
            team_stats = None
            for conference in stats_data.get("standings", []):
                for row in conference.get("rows", []):
                    if row.get("team", {}).get("id") == team_id_for_nba:
                        team_stats = row
                        break
                if team_stats:
                    break
            if not team_stats:
                return {}, 0
            matches = team_stats.get("matches", 0)
            return {
                "points": team_stats.get("scoresFor", 0),
                "pointsAgainst": team_stats.get("scoresAgainst", 0),
            }, matches
        except Exception:
            return {}, 0
    else:
        return {}, 0

def _fetch_basket_team_stats_internal(team_id: str, api_lig_id: str, api_season_id: str) -> dict | None:
    """Cache'siz, direkt istek yapan iç fonksiyon."""
    stats_data = None
    session = get_session()
    
    # 1. Deneme: Ranks
    url_ranks = f"{SOFASCORE_API_BASE_URL.replace('/unique-tournament', '/team')}/{team_id}/unique-tournament/{api_lig_id}/season/{api_season_id}/ranks/regularSeason"
    try:
        response = session.get(url_ranks, timeout=10)
        if response.status_code == 200:
            stats_data = response.json()
    except Exception as e:
        logger.warning(f"Basketbol ranks endpoint hatası: {e}")

    # 2. Deneme: Overall
    if not stats_data:
        url_overall = f"{SOFASCORE_API_BASE_URL.replace('/unique-tournament', '/team')}/{team_id}/unique-tournament/{api_lig_id}/season/{api_season_id}/statistics/overall"
        try:
            response = session.get(url_overall, timeout=10)
            if response.status_code == 200:
                stats_data = response.json()
        except Exception as e:
            logger.warning(f"Basketbol overall endpoint hatası: {e}")

    # 3. Deneme: Standings (NBA)
    if not stats_data:
        url_standings = f"{SOFASCORE_API_BASE_URL}/{api_lig_id}/season/{api_season_id}/standings/total"
        try:
            response = session.get(url_standings, timeout=10)
            if response.status_code == 200:
                stats_data = response.json()
        except Exception as e:
            _log_error_details(url_standings, error=e, context="Basketbol Standings")
            return {}

    if not stats_data:
        logger.error(f"❌ Basketbol Takım İstatistiği bulunamadı: Team {team_id}")
        return {}

    try:
        stats, matches = _parse_basket_stats_json(stats_data, int(team_id))
        matches_safe = max(matches, 1)
        
        if not stats:
            return {}
            
        off_reb_pg = stats.get("offensiveRebounds", 0) / matches_safe
        def_reb_pg = stats.get("defensiveRebounds", 0) / matches_safe
        
        return {
            "ppg": stats.get("points", 0) / matches_safe,
            "ppg_allowed": stats.get("pointsAgainst", 0) / matches_safe,
            "fg_pct": stats.get("fieldGoalsPercentage", 0.0),
            "2p_pct": stats.get("twoPointsPercentage", 0.0),
            "3p_pct": stats.get("threePointsPercentage", 0.0),
            "ft_pct": stats.get("freeThrowsPercentage", 0.0),
            "2p_made_pg": stats.get("twoPointsMade", 0) / matches_safe,
            "2p_att_pg": stats.get("twoPointAttempts", 0) / matches_safe,
            "3p_made_pg": stats.get("threePointsMade", 0) / matches_safe,
            "3p_att_pg": stats.get("threePointAttempts", 0) / matches_safe,
            "ft_made_pg": stats.get("freeThrowsMade", 0) / matches_safe,
            "ft_att_pg": stats.get("freeThrowAttempts", 0) / matches_safe,
            "total_reb_pg": off_reb_pg + def_reb_pg, 
            "off_reb_pg": off_reb_pg,
            "def_reb_pg": def_reb_pg,
            "assists_pg": stats.get("assists", 0) / matches_safe,
            "turnovers_pg": stats.get("turnovers", 0) / matches_safe,
            "steals_pg": stats.get("steals", 0) / matches_safe,
            "blocks_pg": stats.get("blocks", 0) / matches_safe,
        }
    except Exception as e:
        logger.error(f"Basketbol İstatistik Hesaplama Hatası: {e}", exc_info=True)
        return None

def fetch_basket_team_stats(team_id: str, api_lig_id: str, api_season_id: str) -> dict | None:
    """(GÜNCELLENDİ) Cache kullanan basketbol takım istatistik fonksiyonu."""
    # 1. Güncel "dönemi" belirle
    # Basketbolda 'round' genelde güvenlidir, NBA için 'date' de olabilir ama
    # istatistikler için 'current round' iyi bir cache key'dir.
    current_round = get_current_round_or_date(int(api_lig_id), int(api_season_id), "round")
    
    # 2. Cache Kontrol
    cached_stats = cache_manager.get_data("team_stats", team_id, current_round)
    if cached_stats:
        return cached_stats

    # 3. Veri Çek
    stats = _fetch_basket_team_stats_internal(team_id, api_lig_id, api_season_id)
    
    # 4. Cache Yaz
    if stats:
        cache_manager.set_data("team_stats", team_id, current_round, stats)
    
    return stats

def _parse_football_stats_json(stats_data: dict, team_id: int, data_type: str) -> tuple[dict, int, str]:
    """Futbol istatistik JSON'ını parse eder (Detailed veya Standings)."""
    if data_type == "detailed":
        try:
            stats = stats_data.get("statistics", {})
            matches_total = stats.get("matches", 0)
            if matches_total == 0:
                 logger.warning(f"⚽ Detaylı istatistiklerde 'matches' 0, {team_id} için veri bulunamadı.")
                 return {}, 0, "empty" 
            
            matches_safe = matches_total if matches_total > 0 else 1
            
            return {
                "stats_source": "calculated_total_correct",
                "total_shots_pg": stats.get("shots", 0) / matches_safe,
                "shots_on_target_pg": stats.get("shotsOnTarget", 0) / matches_safe,
                "corners_pg": stats.get("corners", 0) / matches_safe,
                "fouls_pg": stats.get("fouls", 0) / matches_safe,
                "offsides_pg": stats.get("offsides", 0) / matches_safe,
                "yellow_cards_pg": stats.get("yellowCards", 0) / matches_safe,
                "red_cards_pg": (stats.get("redCards", 0) + stats.get("yellowRedCards", 0)) / matches_safe,
                "goal_kicks_pg": stats.get("goalKicks", 0) / matches_safe, 
            }, matches_total, "detailed"
        except Exception as e:
            logger.error(f"Futbol 'detailed' JSON parse hatası: {e}", exc_info=True)
            return {}, 0, "empty"

    elif data_type == "standings":
        try:
            logger.info(f"⚽ İstatistik Tipi: 'standings' (Puan Durumu Fallback) bulundu. Takım {team_id} aranıyor...")
            team_stats = None
            
            for table in stats_data.get("standings", []):
                if table.get("type") != "total": 
                    continue
                
                for row in table.get("rows", []):
                    if row.get("team", {}).get("id") == team_id:
                        team_stats = row
                        break
                if team_stats:
                    break
            
            if not team_stats:
                logger.warning(f"Futbol standings JSON içinde takım {team_id} bulunamadı.")
                return {}, 0, "empty"

            matches = team_stats.get("matches", 0)
            matches_safe = matches if matches > 0 else 1
            
            return {
                "position": team_stats.get("position", 0),
                "wins": team_stats.get("wins", 0),
                "draws": team_stats.get("draws", 0),
                "losses": team_stats.get("losses", 0),
                "goalsFor": team_stats.get("scoresFor", 0),
                "goalsAgainst": team_stats.get("scoresAgainst", 0),
                "points": team_stats.get("points", 0),
                "goals_for_pg": team_stats.get("scoresFor", 0) / matches_safe,
                "goals_against_pg": team_stats.get("scoresAgainst", 0) / matches_safe,
            }, matches, "standings"
            
        except Exception as e:
            logger.error(f"Futbol standings JSON parse hatası: {e}", exc_info=True)
            return {}, 0, "empty"
            
    return {}, 0, "empty"

def _fetch_football_team_stats_internal(team_id: str, api_lig_id: str, api_season_id: str) -> dict | None:
    """Cache'siz, direkt istek yapan iç fonksiyon."""
    stats_data = None
    data_type = ""
    session = get_session()
    
    # 1. Deneme: Detailed
    url_stats = f"{SOFASCORE_API_BASE_URL.replace('/unique-tournament', '/team')}/{team_id}/unique-tournament/{api_lig_id}/season/{api_season_id}/statistics/overall"
    try:
        response = session.get(url_stats, timeout=10)
        if response.status_code == 200:
            stats_data = response.json()
            data_type = "detailed"
    except Exception:
        pass 
        
    # 2. Deneme: Standings (Fallback)
    if not stats_data:
        url_standings = f"{SOFASCORE_API_BASE_URL}/{api_lig_id}/season/{api_season_id}/standings/total"
        try:
            response = session.get(url_standings, timeout=10)
            if response.status_code == 200:
                stats_data = response.json()
                data_type = "standings"
        except Exception as e:
            _log_error_details(url_standings, error=e, context="Futbol Standings")
            return {} 
            
    if not stats_data:
        logger.error(f"❌ Futbol Takım İstatistiği bulunamadı: Team {team_id}")
        return {} 
        
    try:
        stats, matches_total, stats_type = _parse_football_stats_json(stats_data, int(team_id), data_type)
        
        if stats_type == "empty" or not stats:
             return {}
             
        if stats_type == "detailed":
            calculated_stats = stats
            calculated_stats["stats_type"] = "detailed"
            calculated_stats["matches"] = matches_total 
        else: # stats_type == "standings"
            calculated_stats = {
                "stats_type": "standings",
                "position": stats.get("position", 0),
                "points": stats.get("points", 0),
                "matches": matches_total, 
                "wins": stats.get("wins", 0),
                "draws": stats.get("draws", 0),
                "losses": stats.get("losses", 0),
                "goals_for_pg": stats.get("goals_for_pg", 0),
                "goals_against_pg": stats.get("goals_against_pg", 0),
                "goalsForTotal": stats.get("goalsFor", 0),
                "goalsAgainstTotal": stats.get("goalsAgainst", 0),
            }
        return calculated_stats
    except Exception as e:
        logger.error(f"Futbol İstatistik Hesaplama Hatası: {e}", exc_info=True)
        return None

def fetch_football_team_stats(team_id: str, api_lig_id: str, api_season_id: str) -> dict | None:
    """(GÜNCELLENDİ) Cache kullanan futbol takım istatistik fonksiyonu."""
    current_round = get_current_round_or_date(int(api_lig_id), int(api_season_id), "round")
    
    cached_stats = cache_manager.get_data("team_stats", team_id, current_round)
    if cached_stats:
        return cached_stats

    stats = _fetch_football_team_stats_internal(team_id, api_lig_id, api_season_id)
    
    if stats:
        cache_manager.set_data("team_stats", team_id, current_round, stats)
    
    return stats

def fetch_team_players(team_id: str) -> dict | None:
    """Takım oyuncu listesi (Çok sık değişmez ama round bazlı cache uygun)."""
    # Not: team_id tek başına yeterli değil, lig ve sezon bilgisi burada parametre olarak yok.
    # Bu yüzden takım ID'sine göre kısa süreli (örn: 1 günlük) bir cache yapılabilir.
    # Ancak basitlik adına, current_round bilgisi elimizde olmadığı için
    # şimdilik cache'siz bırakıyoruz veya sabit bir key ile cacheleyebiliriz.
    # (Bu fonksiyonun cache'lenmesi şu an için kritik değil)
    
    url = f"https://www.sofascore.com/api/v1/team/{team_id}/players"
    
    response = _request_with_retry(url, context="Oyuncu Listesi")
    
    if not response or response.status_code != 200:
        return None
    
    try:
        data = response.json()
        
        players_grouped = {"Goalkeeper": [], "Defender": [], "Midfielder": [], "Forward": [], "Diğer": []}
        all_players_flat = []
        
        if not data.get("players"):
            return {"grouped": players_grouped, "flat": all_players_flat}

        for player_data in data.get("players", []):
            player = player_data.get("player", {})
            name = player.get("name")
            position = player.get("position")
            player_id = player.get("id")
            
            if not name or not player_id:
                continue
                
            player_tuple = (name, player_id)
            all_players_flat.append(player_tuple)

            if position == "G": players_grouped["Goalkeeper"].append(player_tuple)
            elif position == "D": players_grouped["Defender"].append(player_tuple)
            elif position == "M": players_grouped["Midfielder"].append(player_tuple)
            elif position == "F": players_grouped["Forward"].append(player_tuple)
            else: players_grouped["Diğer"].append(player_tuple)
        
        return {"grouped": players_grouped, "flat": all_players_flat}
        
    except Exception as e:
        _log_error_details(url, error=e, context="Oyuncu Listesi Parse")
        return None

# ###########################################################################
# # --- OYUNCU İSTATİSTİKLERİ ---
# ###########################################################################

def _parse_player_football_stats(stats_data: dict) -> dict | None:
    if not stats_data or "statistics" not in stats_data:
        return None
    player_stats = stats_data.get("statistics", {})
    appearances = player_stats.get("appearances", 0)
    matches_safe = max(appearances, 1)
    try:
        calculated_stats = {
            "appearances": appearances,
            "started": player_stats.get("matchesStarted", 0),
            "minutes_pg": player_stats.get("minutesPlayed", 0) / matches_safe,
            "shots_pg": player_stats.get("totalShots", 0) / matches_safe,
            "shots_on_target_pg": player_stats.get("shotsOnTarget", 0) / matches_safe,
            "passes_pg": player_stats.get("totalPasses", 0) / matches_safe,
            "accurate_passes_pg": player_stats.get("accuratePasses", 0) / matches_safe,
            "interceptions_pg": player_stats.get("interceptions", 0) / matches_safe,
            "fouls_pg": player_stats.get("fouls", 0) / matches_safe,
            "was_fouled_pg": player_stats.get("wasFouled", 0) / matches_safe,
            "yellow_cards_pg": player_stats.get("yellowCards", 0) / matches_safe,
        }
        player_info = stats_data.get("player", {})
        calculated_stats["player_name"] = player_info.get("name", "Bilinmeyen Oyuncu")
        return calculated_stats
    except Exception:
        return {}

def _fetch_player_football_stats_internal(player_id: str, api_lig_id: str, api_season_id: str, player_name: str = None) -> dict | None:
    """Cache'siz, direkt istek yapan iç fonksiyon."""
    url = f"https://www.sofascore.com/api/v1/player/{player_id}/unique-tournament/{api_lig_id}/season/{api_season_id}/statistics/overall"
    
    response = _request_with_retry(url, context="Futbol Oyuncu Stats")
    
    if response and response.status_code == 200:
        try:
            data = response.json()
            stats = _parse_player_football_stats(data)
            if stats and player_name:
                stats["player_name"] = player_name
            elif stats and not stats.get("player_name"):
                 stats["player_name"] = player_name if player_name else f"ID: {player_id}"
            elif not stats:
                if player_name: return {"player_name": player_name, "appearances": 0}
                return {"player_name": f"ID: {player_id}", "appearances": 0}
            return stats
        except Exception as e:
            _log_error_details(url, error=e, context="Futbol Oyuncu Stats Parse")
    
    if player_name: return {"player_name": player_name, "appearances": 0}
    return {"player_name": f"ID: {player_id}", "appearances": 0}

def fetch_player_football_stats(player_id: str, api_lig_id: str, api_season_id: str, player_name: str = None) -> dict | None:
    """(GÜNCELLENDİ) Cache kullanan futbol oyuncu istatistik fonksiyonu."""
    current_round = get_current_round_or_date(int(api_lig_id), int(api_season_id), "round")
    
    cached_stats = cache_manager.get_data("player_stats", player_id, current_round)
    if cached_stats:
        if player_name: cached_stats["player_name"] = player_name
        return cached_stats

    stats = _fetch_player_football_stats_internal(player_id, api_lig_id, api_season_id, player_name)
    
    if stats:
        cache_manager.set_data("player_stats", player_id, current_round, stats)
        
    return stats

def _parse_player_basket_stats(stats_data: dict) -> dict | None:
    if not stats_data or "statistics" not in stats_data:
        return None
    try:
        stats = stats_data.get("statistics", {})
        appearances = stats.get("appearances", 0) 
        matches_safe = max(appearances, 1) 
        
        player_info = stats_data.get("player", {})
        player_name = player_info.get("name", "Bilinmeyen Oyuncu")
        fg_attempts = stats.get("fieldGoalAttempts", stats.get("fieldGoalsAttempted", 0)) 
        
        calculated_stats = {
            "player_name": player_name,
            "appearances": appearances,
            "ppg": stats.get("points", 0) / matches_safe,
            "rpg": stats.get("rebounds", 0) / matches_safe,
            "apg": stats.get("assists", 0) / matches_safe,
            "spg": stats.get("steals", 0) / matches_safe,
            "bpg": stats.get("blocks", 0) / matches_safe,
            "tpg": stats.get("turnovers", 0) / matches_safe,
            "pir": stats.get("pir", 0) / matches_safe, 
            "minutes_pg": stats.get("secondsPlayed", 0) / 60 / matches_safe,
            "ft_made_pg": stats.get("freeThrowsMade", 0) / matches_safe,
            "ft_att_pg": stats.get("freeThrowAttempts", 0) / matches_safe,
            "ft_pct": stats.get("freeThrowsPercentage", 0),
            "2p_made_pg": stats.get("twoPointsMade", 0) / matches_safe,
            "2p_att_pg": stats.get("twoPointAttempts", 0) / matches_safe,
            "2p_pct": stats.get("twoPointsPercentage", 0),
            "3p_made_pg": stats.get("threePointsMade", 0) / matches_safe,
            "3p_att_pg": stats.get("threePointAttempts", 0) / matches_safe,
            "3p_pct": stats.get("threePointsPercentage", 0),
            "fg_made_pg": stats.get("fieldGoalsMade", 0) / matches_safe,
            "fg_att_pg": fg_attempts / matches_safe,
            "fg_pct": stats.get("fieldGoalsPercentage", 0),
        }
        return calculated_stats
    except Exception:
        return None

def _fetch_player_basket_stats_internal(player_id: str, api_lig_id: str, api_season_id: str, player_name: str = None) -> dict | None:
    """Cache'siz, direkt istek yapan iç fonksiyon."""
    url_regular = f"https://www.sofascore.com/api/v1/player/{player_id}/unique-tournament/{api_lig_id}/season/{api_season_id}/statistics/regularSeason"
    url_overall = f"https://www.sofascore.com/api/v1/player/{player_id}/unique-tournament/{api_lig_id}/season/{api_season_id}/statistics/overall"

    stats = None
    session = get_session()
    
    try:
        response = session.get(url_regular, timeout=10)
        if response.status_code == 200:
            stats = _parse_player_basket_stats(response.json())
            if stats and stats.get("appearances", 0) > 0:
                if player_name: stats["player_name"] = player_name
                return stats 
    except Exception:
         pass 

    try:
        response = session.get(url_overall, timeout=10)
        if response.status_code == 200:
            stats = _parse_player_basket_stats(response.json())
            if stats and stats.get("appearances", 0) > 0:
                if player_name: stats["player_name"] = player_name
                return stats 
    except Exception:
         pass

    if player_name: return {"player_name": player_name, "appearances": 0}
    return {"player_name": f"ID: {player_id}", "appearances": 0}

def fetch_player_basket_stats(player_id: str, api_lig_id: str, api_season_id: str, player_name: str = None) -> dict | None:
    """(GÜNCELLENDİ) Cache kullanan basketbol oyuncu istatistik fonksiyonu."""
    current_round = get_current_round_or_date(int(api_lig_id), int(api_season_id), "round")
    
    cached_stats = cache_manager.get_data("player_stats", player_id, current_round)
    if cached_stats:
        if player_name: cached_stats["player_name"] = player_name
        return cached_stats

    stats = _fetch_player_basket_stats_internal(player_id, api_lig_id, api_season_id, player_name)
    
    if stats:
        cache_manager.set_data("player_stats", player_id, current_round, stats)
        
    return stats

def _try_alternative_basketball_endpoint(player_id: str) -> dict:
    url = f"https://www.sofascore.com/api/v1/player/{player_id}/statistics/last"
    try:
        session = get_session()
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            return _parse_player_basket_stats(response.json())
        return {}
    except Exception:
        return {}