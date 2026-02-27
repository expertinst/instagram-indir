import os
import sys
import subprocess
import json
import time
import requests

# ═══════════════════════════════════════
HESAPLAR = ["motive2m", "nerdesinpango"]
DRIVE_KLASOR_ID = "1OaRDgcKjbEKM1gPny3CE19s8vaFUs03T"
ARSIV_DOSYA = "arsiv.json"
# ═══════════════════════════════════════

def kurulum():
    print("📦 Gerekli araçlar hazırlanıyor...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "google-api-python-client", "google-auth", "requests", "-q"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

def arsiv_oku():
    if os.path.exists(ARSIV_DOSYA):
        with open(ARSIV_DOSYA, "r") as f: return json.load(f)
    return []

def arsiv_kaydet(arsiv):
    with open(ARSIV_DOSYA, "w") as f: json.dump(arsiv, f)

def fastdl_indir(hesap, arsiv):
    from playwright.sync_api import sync_playwright
    linkler = []
    story_url = f"https://www.instagram.com/stories/{hesap}/"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        print(f"  🔍 @{hesap} hikayeleri taranıyor...")
        try:
            page.goto("https://fastdl.dev/", wait_until="networkidle", timeout=60000)
            input_selector = 'input[name="url"]'
            page.wait_for_selector(input_selector, timeout=20000)
            page.fill(input_selector, story_url)
            page.keyboard.press("Enter")
            
            # Sonuç kutusunun gelmesini bekle
            page.wait_for_selector('.download-items, .download-box', timeout=30000)
            time.sleep(7) # Linklerin tamamen oluşması için biraz daha süre
            
            # Video ve Resim linklerini beraber yakala
            items = page.locator('a[href*=".mp4"], a[href*="snapcdn.app"], a[href*=".jpg"], a[href*=".webp"]').all()
            for item in items:
                href = item.get_attribute("href")
                if href and href not in arsiv and href not in linkler:
                    # Reklam linklerini filtrele
                    if "googlevideo" not in href and "doubleclick" not in href:
                        linkler.append(href)
                        print(f"  ✅ İçerik linki bulundu!")
        except Exception:
            print(f"  ⚠️ Şu an yeni içerik bulunamadı.")
        browser.close()
    return linkler

def dosya_indir(url, hedef_yol):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, stream=True, timeout=30)
        
        # 🛡️ YENİ KONTROL:
        # 1. Dosya boyutu 20KB'dan büyük olmalı (Gerçek storyler genelde 20KB-5MB arasıdır)
        # 2. Dosya türü resim (image) veya video olmalı
        content_length = int(resp.headers.get('Content-Length', 0))
        content_type = resp.headers.get('Content-Type', '').lower()
        
        is_valid_type = 'image' in content_type or 'video' in content_type
        
        if resp.status_code == 200 and content_length > 20000 and is_valid_type:
            with open(hedef_yol, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192): f.write(chunk)
            return True
        else:
            print(f"  🚫 Geçersiz dosya atlandı (Boyut: {content_length} bytes, Tür: {content_type})")
    except: return False
    return False

def drive_baglanti():
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    token_json = os.environ.get("GDRIVE_TOKEN")
    creds = Credentials.from_authorized_user_info(json.loads(token_json))
    return build("drive", "v3", credentials=creds)

def drive_yukle(service, dosya_yolu, klasor_id):
    from googleapiclient.http import MediaFileUpload
    ad = os.path.basename(dosya_yolu)
    meta = {"name": ad, "parents": [klasor_id]}
    media = MediaFileUpload(dosya_yolu, resumable=True)
    service.files().create(body=meta, media_body=media).execute()
    print(f"  ☁️ Drive'a (2TB) gönderildi: {ad}")

if __name__ == "__main__":
    kurulum()
    service = drive_baglanti()
    arsiv = arsiv_oku()
    for hesap in HESAPLAR:
        os.makedirs(hesap, exist_ok=True)
        linkler = fastdl_indir(hesap, arsiv)
        for i, link in enumerate(linkler):
            # Uzantıyı linkten anlamaya çalış, yoksa varsayılan mp4 yap
            ext = "jpg" if ".jpg" in link or ".webp" in link else "mp4"
            dosya_adi = f"{hesap}/{hesap}_{int(time.time())}_{i}.{ext}"
            
            if dosya_indir(link, dosya_adi):
                drive_yukle(service, dosya_adi, DRIVE_KLASOR_ID)
                arsiv.append(link)
                if os.path.exists(dosya_adi): os.remove(dosya_adi)
    arsiv_kaydet(arsiv)
    print("🎉 İşlem bitti!")
