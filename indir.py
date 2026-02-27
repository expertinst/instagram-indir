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
    # Sadece hikayeye odaklanmak için linki netleştiriyoruz
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
            
            # Sonuçların yüklenmesi için bekle
            page.wait_for_selector('.download-items', timeout=30000)
            time.sleep(5)
            
            # Sadece video (.mp4) ve kaliteli resim linklerini yakala
            items = page.locator('a[href*=".mp4"], a[href*="snapcdn.app"]').all()
            for item in items:
                href = item.get_attribute("href")
                if href and href not in arsiv and href not in linkler:
                    # Bozuk linkleri (reklam vb) filtrele
                    if "googlevideo" not in href and "doubleclick" not in href:
                        linkler.append(href)
                        print(f"  ✅ Video linki yakalandı!")
        except Exception:
            print(f"  ⚠️ Şu an yeni hikaye bulunamadı veya site yanıt vermedi.")
        browser.close()
    return linkler

def dosya_indir(url, hedef_yol):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, stream=True, timeout=30)
        # Sadece dosya boyutu 100KB'dan büyükse indir (Bozuk/küçük dosyaları engeller)
        if resp.status_code == 200 and int(resp.headers.get('Content-Length', 0)) > 100000:
            with open(hedef_yol, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192): f.write(chunk)
            return True
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
    print(f"  ☁️ Drive'a gönderildi: {ad}")

if __name__ == "__main__":
    kurulum()
    service = drive_baglanti()
    arsiv = arsiv_oku()
    for hesap in HESAPLAR:
        os.makedirs(hesap, exist_ok=True)
        linkler = fastdl_indir(hesap, arsiv)
        for i, link in enumerate(linkler):
            dosya_adi = f"{hesap}/{hesap}_{int(time.time())}_{i}.mp4"
            if dosya_indir(link, dosya_adi):
                drive_yukle(service, dosya_adi, DRIVE_KLASOR_ID)
                arsiv.append(link)
                if os.path.exists(dosya_adi): os.remove(dosya_adi)
    arsiv_kaydet(arsiv)
    print("🎉 İşlem bitti!")
