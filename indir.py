import os, sys, subprocess, json, time, requests

# AYARLAR
HESAPLAR = ["motive2m", "zeynep.okktay"]
DRIVE_KLASOR_ID = "1OaRDgcKjbEKM1gPny3CE19s8vaFUs03T"
ARSIV_DOSYA = "arsiv.json"

def kurulum():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "google-api-python-client", "google-auth", "requests", "-q"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

def get_links(hesap, arsiv):
    from playwright.sync_api import sync_playwright
    linkler = []
    target = f"https://www.instagram.com/stories/{hesap}/"
    sites = ["https://fastdl.dev/", "https://saveig.app/"]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        # 🛡️ REKLAM ENGELLEYİCİ: Gereksiz tüm istekleri blokluyoruz
        def block_ads(route):
            ad_domains = ["doubleclick", "google-analytics", "facebook", "amazon-adsystem", "adnxs", "popads", "adsterra"]
            if any(domain in route.request.url for domain in ad_domains) or route.request.resource_type in ["image", "stylesheet", "font"]:
                route.abort()
            else:
                route.continue_()

        page.route("**/*", block_ads)

        for site in sites:
            try:
                print(f"🔍 {site} üzerinden @{hesap} taranıyor...")
                page.goto(site, wait_until="domcontentloaded", timeout=60000)
                
                # Link kutusunu bul ve doldur
                box = page.locator('input[name="url"], input[id*="url"]').first
                box.wait_for(timeout=20000)
                box.fill(target)
                page.keyboard.press("Enter")
                
                # İndirme kutusunun gelmesini bekle (Reklamlar engellendiği için daha temiz gelecek)
                page.wait_for_selector('a[href*="mp4"], a[href*="token="], .download-items', timeout=40000)
                time.sleep(10)
                
                # Gerçek video ve resim linklerini yakala
                items = page.locator('a[href*="mp4"], a[href*="token="], a[href*=".jpg"]').all()
                for item in items:
                    href = item.get_attribute("href")
                    if href and href not in arsiv and href not in linkler:
                        # Son bir kontrol: Gerçekten Instagram tabanlı bir indirme linki mi?
                        if "googlevideo" not in href and "googlead" not in href:
                            linkler.append(href)
                
                if linkler: 
                    print(f"✅ {len(linkler)} yeni içerik bulundu.")
                    break 
            except Exception:
                continue
        browser.close()
    return linkler

def dosya_indir(url, yol):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, stream=True, timeout=60)
        # 20KB altı dosyalar genelde bozuktur, onları atla
        if resp.status_code == 200 and int(resp.headers.get('Content-Length', 0)) > 20000:
            with open(yol, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192): f.write(chunk)
            return True
    except: return False
    return False

def drive_yukle(yol, klasor_id):
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from googleapiclient.http import MediaFileUpload
    creds = Credentials.from_authorized_user_info(json.loads(os.environ.get("GDRIVE_TOKEN")))
    service = build("drive", "v3", credentials=creds)
    media = MediaFileUpload(yol, resumable=True)
    service.files().create(body={"name": os.path.basename(yol), "parents": [klasor_id]}, media_body=media).execute()

if __name__ == "__main__":
    kurulum()
    # Arşivi yükle (Yoksa oluştur)
    if os.path.exists(ARSIV_DOSYA):
        with open(ARSIV_DOSYA, "r") as f: arsiv = json.load(f)
    else:
        arsiv = []

    for hesap in HESAPLAR:
        os.makedirs(hesap, exist_ok=True)
        found = get_links(hesap, arsiv)
        for i, link in enumerate(found):
            yol = f"{hesap}/{int(time.time())}_{i}.mp4"
            if dosya_indir(link, yol):
                drive_yukle(yol, DRIVE_KLASOR_ID)
                arsiv.append(link)
                print(f"☁️ Drive'a yüklendi: {yol}")
                if os.path.exists(yol): os.remove(yol)
    
    with open(ARSIV_DOSYA, "w") as f: json.dump(arsiv, f)
