import os
import sys
import subprocess
import json
import time
from pathlib import Path

# ═══════════════════════════════════════
# AYARLAR
HESAPLAR = [
    "motive2m",
    "nerdesinpango",
]
DRIVE_KLASOR_ID = "1OaRDgcKjbEKM1gPny3CE19s8vaFUs03T"
ARSIV_DOSYA = "arsiv.json"
# ═══════════════════════════════════════

def kurulum():
    print("📦 Kütüphaneler kuruluyor...")
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                          "playwright", "google-api-python-client",
                          "google-auth", "requests", "-q"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

def arsiv_oku():
    if os.path.exists(ARSIV_DOSYA):
        with open(ARSIV_DOSYA, "r") as f:
            return json.load(f)
    return []

def arsiv_kaydet(arsiv):
    with open(ARSIV_DOSYA, "w") as f:
        json.dump(arsiv, f)

def fastdl_indir(hesap, arsiv):
    from playwright.sync_api import sync_playwright
    linkler = []
    urls = [
        f"https://www.instagram.com/stories/{hesap}/",
        f"https://www.instagram.com/{hesap}/",
    ]
    with sync_playwright() as p:
        # Daha "insansı" bir tarayıcı kimliği (User-Agent) ekliyoruz
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        for url in urls:
            print(f"  🔗 Kaynak taranıyor: {url}")
            try:
                # Bekleme süresini 60 saniyeye çıkarıyoruz (Site yavaş açılabilir)
                page.goto("https://fastdl.dev/", wait_until="networkidle", timeout=60000)
                
                # Kutucuğun gelmesini daha sabırla bekliyoruz
                input_selector = 'input[placeholder*="Instagram"], input[name="url"]'
                page.wait_for_selector(input_selector, timeout=30000)
                
                input_el = page.locator(input_selector).first
                input_el.fill(url)
                page.keyboard.press("Enter")
                
                # İndirme butonlarının gelmesini bekle
                page.wait_for_selector('.download-box, a[href*="mp4"]', timeout=30000)
                time.sleep(5) # Sayfanın tam yüklenmesi için kısa bir mola
                
                # Linkleri topla
                anchors = page.locator('a[href*="snapcdn"], a[href*=".mp4"], a[href*=".jpg"]').all()
                for a in anchors:
                    href = a.get_attribute("href")
                    if href and href not in arsiv and href not in linkler:
                        linkler.append(href)
                        print(f"  ✅ Yeni Link bulundu!")
            except Exception as e:
                print(f"  ⚠️ Tarama uyarısı: Siteye ulaşılamadı veya kutucuk bulunamadı.")
        browser.close()
    return linkler

def dosya_indir(url, hedef_yol):
    import requests
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, stream=True, timeout=60)
        if resp.status_code == 200:
            with open(hedef_yol, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except Exception:
        return False
    return False

# ✨ YENİ: 2TB KOTA İÇİN OAUTH BAĞLANTISI
def drive_baglanti():
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    
    # GitHub Secrets'taki o uzun token metnini alıyoruz
    token_json = os.environ.get("GDRIVE_TOKEN")
    if not token_json:
        print("❌ HATA: GDRIVE_TOKEN bulunamadı! GitHub Secrets ayarlarını kontrol et.")
        sys.exit(1)
    
    creds_dict = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(creds_dict)
    
    # Eğer token eskimişse otomatik yenile
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        
    return build("drive", "v3", credentials=creds)

def klasor_bul_veya_olustur(service, ad, ust_id):
    q = f"name='{ad}' and '{ust_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    sonuc = service.files().list(q=q).execute().get("files", [])
    if sonuc:
        return sonuc[0]["id"]
    meta = {"name": ad, "mimeType": "application/vnd.google-apps.folder", "parents": [ust_id]}
    return service.files().create(body=meta, fields="id").execute()["id"]

def drive_yukle(service, dosya_yolu, klasor_id):
    from googleapiclient.http import MediaFileUpload
    ad = os.path.basename(dosya_yolu)
    
    # Aynı isimde dosya var mı kontrolü
    q = f"name='{ad}' and '{klasor_id}' in parents and trashed=false"
    if service.files().list(q=q).execute().get("files"):
        print(f"  ⏭️ Zaten yüklü: {ad}")
        return

    meta = {"name": ad, "parents": [klasor_id]}
    media = MediaFileUpload(dosya_yolu, resumable=True)
    service.files().create(body=meta, media_body=media).execute()
    print(f"  ☁️ Drive'a yüklendi: {ad}")

if __name__ == "__main__":
    kurulum()
    service = drive_baglanti()
    arsiv = arsiv_oku()

    for hesap in HESAPLAR:
        gecici_klasor = f"temp_{hesap}"
        os.makedirs(gecici_klasor, exist_ok=True)
        
        drive_hedef = klasor_bul_veya_olustur(service, hesap, DRIVE_KLASOR_ID)
        print(f"\n🚀 İşlem başlıyor: @{hesap}")

        linkler = fastdl_indir(hesap, arsiv)
        for i, link in enumerate(linkler):
            ext = "mp4" if "mp4" in link else "jpg"
            dosya_adi = f"{gecici_klasor}/{hesap}_{int(time.time())}_{i}.{ext}"
            
            if dosya_indir(link, dosya_adi):
                drive_yukle(service, dosya_adi, drive_hedef)
                arsiv.append(link)
                # İndirilen dosyayı temizle (GitHub alanını doldurmamak için)
                if os.path.exists(dosya_adi): os.remove(dosya_adi)

    arsiv_kaydet(arsiv)
    print("\n🎉 İşlem başarıyla tamamlandı!")
