# -*- coding: utf-8 -*-
# utils.py
"""
Proje genelinde kullanılacak yardımcı fonksiyonlar (örn: isim normalleştirme).
GÜNCELLEME: Basketbol için timestamp formatlayıcı eklendi.
GÜNCELLEME (HAKEM): Kısa tarih (YYYY-MM-DD) formatlayıcı eklendi.
"""
import re
from datetime import datetime

# --- YARDIMCI FONKSİYONLAR (FUTBOL) ---
# ... (Diğer yardımcı fonksiyonlar kaldırıldığı için bu dosya temizlendi) ...

# --- GENEL YARDIMCI FONKSİYONLAR (BASKETBOL & FUTBOL) ---

def _get_tr_month(month_num: int) -> str:
    """Sayısal ay değerini Türkçe kısaltmaya çevirir. (Artık kullanılmıyor)"""
    months = {
        1: 'Oca', 2: 'Şub', 3: 'Mar', 4: 'Nis', 5: 'May', 6: 'Haz',
        7: 'Tem', 8: 'Ağu', 9: 'Eyl', 10: 'Eki', 11: 'Kas', 12: 'Ara'
    }
    return months.get(month_num, '??')

def format_timestamp_to_date(timestamp: int) -> str:
    """
    Unix timestamp'i (örn: 1763063100)
    okunabilir bir "22.11.2025 15:30" formatına çevirir.
    (GÜNCELLENDİ)
    """
    try:
        dt_object = datetime.fromtimestamp(timestamp)
        # Format: Gün.Ay.Yıl Saat:Dakika (Hedef botun formatı)
        return dt_object.strftime('%d.%m.%Y %H:%M')
    except Exception as e:
        from config import logger
        logger.warning(f"Timestamp ({timestamp}) çevirme hatası: {e}")
        return "Tarih Bilinmiyor"

# --- YENİ: HAKEM İÇİN KISA TARİH FORMATLAYICI ---
def format_timestamp_to_date_short(timestamp: int) -> str:
    """
    (YENİ EKLENDİ - İZOLE)
    Unix timestamp'i "YYYY-MM-DD" formatına çevirir (Hakem son 5 maç için).
    """
    try:
        dt_object = datetime.fromtimestamp(timestamp)
        # Format: Yıl-Ay-Gün
        return dt_object.strftime('%Y-%m-%d')
    except Exception as e:
        from config import logger
        logger.warning(f"Kısa Timestamp ({timestamp}) çevirme hatası: {e}")
        return "Tarih Yok"