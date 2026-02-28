import os
import sys
import subprocess
import json
import time
import requests

# AYARLAR
HESAPLAR = ["motive2m", "nerdesinpango"] 
DRIVE_KLASOR_ID = "1OaRDgcKjbEKM1gPny3CE19s8vaFUs03T"
ARSIV_DOSYA = "arsiv.json"

def kurulum():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "google-api-python-client", "google-auth", "requests", "-q"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

def arsiv_oku():
    if os.path.exists(ARSIV_DOSYA):
        with open(ARSIV_DOSYA, "r") as f: return json.load(f)
    return []

def arsiv_kaydet(arsiv):
    with open(ARSIV_DOSYA, "w") as f: json.dump(arsiv, f)

def get_links(hesap, arsiv):
    from playwright.sync_api import sync_playwright
    linkler = []
    target = f"https://www.instagram.com/stories/{hesap}/"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        try:
            print(f"🔍 @{hesap} taranıyor...")
            page.goto("https://snapinsta.app/", wait_until="networkidle", timeout=60000)
            
            # Link kutusunu doldur
            page.fill('input[name="url"]', target)
            page.click('button[type="submit"]')
            
            # Butonun gelmesini bekle
            page.wait_for_selector('.download-items', timeout=30000)
            time.sleep(8) # Videoların hazırlanması için bekleme
            
            # Gerçek indirme linklerini yakala
            anchors = page.locator('a[href*="download"], a[href*=".mp4"]').all()
            for a in anchors:
                href = a.get_attribute("href")
                if href and href not in arsiv and href not in linkler:
                    linkler.append(href)
                    print(f"✅ Link bulundu: {href[:50]}...")
        except Exception as e:
            print(f"⚠️ Hata: {str(e)[:100]}")
        browser.close()
    return linkler

def dosya_indir(url, yol):
    try:
        resp = requests.get(url, stream=True, timeout=30)
        size = int(resp.headers.get('Content-Length', 0))
        # 20KB altı dosyalar genelde bozuktur, onları indirme
        if resp.status_code == 200 and size > 20000:
            with open(yol, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192): f.write(chunk)
            return True
    except: return False
    return False

def drive_baglanti():
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    token_json = os.environ.get("GDRIVE_TOKEN")
    if not token_json: raise ValueError("GDRIVE_TOKEN eksik!")
    creds = Credentials.from_authorized_user_info(json.loads(token_json))
    return build("drive", "v3", credentials=creds)

def drive_yukle(service, yol, klasor_id):
    from googleapiclient.http import MediaFileUpload
    ad = os.path.basename(yol)
    meta = {"name": ad, "parents": [klasor_id]}
    media = MediaFileUpload(yol, resumable=True)
    service.files().create(body=meta, media_body=media).execute()
    print(f"☁️ Drive'a yüklendi: {ad}")

if __name__ == "__main__":
    kurulum()
    try:
        service = drive_baglanti()
        arsiv = arsiv_oku()
        for hesap in HESAPLAR:
            os.makedirs(hesap, exist_ok=True)
            linkler = get_links(hesap, arsiv)
            for i, link in enumerate(linkler):
                ext = "mp4" if "video" in link or "mp4" in link else "jpg"
                yol = f"{hesap}/{int(time.time())}_{i}.{ext}"
                if dosya_indir(link, yol):
                    drive_yukle(service, yol, DRIVE_KLASOR_ID)
                    arsiv.append(link)
                    if os.path.exists(yol): os.remove(yol)
        arsiv_kaydet(arsiv)
        print("🎉 İşlem tamamlandı!")
    except Exception as e:
        print(f"❌ Ana Hata: {e}")
