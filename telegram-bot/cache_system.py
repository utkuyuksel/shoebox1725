# -*- coding: utf-8 -*-
# cache_system.py
"""
Proje genelinde API yanıtlarını ön belleğe (RAM) almak için kullanılan sistem.
Özellikle 'Hafta' (Round) bazlı caching yaparak gereksiz istekleri engeller.
"""
import time
from datetime import datetime
from config import logger

class CacheManager:
    def __init__(self):
        # Cache yapısı:
        # {
        #   "matches_TR_SL_52_77805_round_12": { "data": [...], "timestamp": 123456789 },
        #   "team_stats_3072_round_12": { ... },
        #   "current_round_TR_SL": { "round": 12, "timestamp": ... }
        # }
        self._cache = {}
        
        # Round bilgisinin kendisini ne kadar süre cache'leyeceğiz? (Örn: 30 dakika)
        # Çünkü maç oynanırken hafta değişmez ama maç biter bitmez değişebilir.
        self.ROUND_TTL = 1800  # 30 dakika (Saniye cinsinden)

    def _get_cache_key(self, prefix: str, unique_id: str, round_or_date: str) -> str:
        """Standart bir cache anahtarı oluşturur."""
        return f"{prefix}_{unique_id}_{round_or_date}"

    def get_cached_round(self, api_lig_id: str):
        """
        Bir ligin 'Şu anki haftası' bilgisini cache'den getirir.
        Bu bilgi çok sık değişmez, o yüzden kısa süreli cachelenir.
        """
        key = f"current_round_{api_lig_id}"
        cached = self._cache.get(key)
        
        if cached:
            if time.time() - cached['timestamp'] < self.ROUND_TTL:
                return cached['data']
            else:
                # Süresi dolmuş
                del self._cache[key]
        return None

    def set_cached_round(self, api_lig_id: str, round_val):
        """Ligin hafta bilgisini cache'e yazar."""
        key = f"current_round_{api_lig_id}"
        self._cache[key] = {
            "data": round_val,
            "timestamp": time.time()
        }

    def get_data(self, prefix: str, identifier: str, round_info: str):
        """
        Belirli bir haftaya/tarihe ait veriyi getirir.
        Eğer hafta bilgisi (round_info) aynıysa, veri sonsuza kadar geçerli sayılabilir
        (Ta ki hafta değişip yeni istek atılana kadar).
        """
        key = self._get_cache_key(prefix, identifier, round_info)
        item = self._cache.get(key)
        
        if item:
            logger.info(f"⚡ CACHE HIT: {key} (Ön bellekten alındı)")
            return item['data']
        return None

    def set_data(self, prefix: str, identifier: str, round_info: str, data):
        """Veriyi cache'e yazar."""
        key = self._get_cache_key(prefix, identifier, round_info)
        # Veriyi kaydet
        self._cache[key] = {
            "data": data,
            "timestamp": time.time()
        }
        logger.info(f"💾 CACHE SAVED: {key} (Hafta: {round_info})")

    def clear_cache(self):
        """Tüm cache'i temizler (Manuel tetikleme veya restart için)."""
        self._cache = {}
        logger.info("🧹 Cache temizlendi.")

# Global instance (Tekil nesne)
cache_manager = CacheManager()