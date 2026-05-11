# -*- coding: utf-8 -*-
# data_loader.py
"""
Global verileri (JSON dosyaları) yükleyen ve saklayan modül.
GÜNCELLEME: Tüm scraper'lar kaldırıldığı için bu modül artık boş.
Hakem ve FBRef ile ilgili her şey TEMİZLENDİ.

GÜNCELLEME (HAKEM): Yerel hakem veritabanı (referees.json) eklendi.
"""
import json
from config import logger

# --- GLOBAL VERİTABANLARI (TEMİZLENDİ) ---
# ALL_REFEREES = {}
# GÜNCELLEME: Hakem veritabanı eklendi
ALL_REFEREES = {}


def load_referees_from_json():
    """(KALDIRILDI) referees.json dosyasını yükler."""
    # GÜNCELLEME: Bu fonksiyon artık yerel Transfermarkt hakem JSON'unu yüklüyor.
    global ALL_REFEREES
    try:
        # DEĞİŞİKLİK: Dosya adı 'referees.json' olarak güncellendi.
        with open('referees.json', 'r', encoding='utf-8') as f:
            ALL_REFEREES = json.load(f)
        # Log seviyesi CRITICAL olsa bile görünmesi için CRITICAL kullanıyoruz.
        logger.critical(f"BAŞARILI: 'referees.json' yüklendi ({len(ALL_REFEREES)} hakem).")
    except FileNotFoundError:
        logger.error("HATA: 'referees.json' dosyası bulunamadı.")
        ALL_REFEREES = {}
    except json.JSONDecodeError:
        logger.error("HATA: 'referees.json' dosyası bozuk (JSON parse hatası).")
        ALL_REFEREES = {}
    except Exception as e:
        logger.error(f"HATA: Hakem JSON yüklenirken beklenmedik bir hata oluştu: {e}")
        ALL_REFEREES = {}


def load_all_data():
    """
    Botun ihtiyaç duyduğu tüm başlangıç verilerini yükler.
    (Artık yüklenecek veri yok)
    
    GÜNCELLEME: Hakem verisi artık yükleniyor.
    """
    logger.critical("Veri yükleme adımı (data_loader) - Yüklenecek statik veri yok.")
    # GÜNCELLEME: Hakem verisini yükle
    load_referees_from_json()
    pass