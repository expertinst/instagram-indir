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
    # DNS hatalarını aşmak için yedekli liste
    sites = ["https://saveig.app/en/instagram-story-downloader", "https://fastdl.dev/"]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        # 🛡️ Reklam Engelleme: Sayfanın hızlı açılmasını ve butonların görünmesini sağlar
        page.route("**/*", lambda route: route.abort() if any(x in route.request.url for x in ["doubleclick", "google-analytics", "ads"]) else route.continue_())

        for site in sites:
            try:
                print(f"🔍 {site} üzerinden @{hesap} taranıyor...")
                page.goto(site, timeout=60000, wait_until="domcontentloaded")
                
                # Her türlü kutucuğu bulabilen esnek bulucu
                box = page.locator('input[id*="url"], input[name="url"], input[placeholder*="Instagram"]').first
                box.wait_for(timeout=20000)
                box.fill(target)
                page.keyboard.press("Enter")
                
                # Butonun oluşması için inatla bekle
                page.wait_for_selector('a[href*="mp4"], a[href*="token="], .download-items', timeout=45000)
                time.sleep(12)
                
                anchors = page.locator('a[href*="mp4"], a[href*="token="], a[href*=".jpg"]').all()
                for a in anchors:
                    href = a.get_attribute("href")
                    if href and href not in arsiv and href not in linkler:
                        if "googlevideo" not in href: # Reklam videolarını ele
                            linkler.append(href)
                
                if linkler: 
                    print(f"✅ {len(linkler)} yeni içerik yakalandı.")
                    break 
            except:
                continue
        browser.close()
    return linkler

def dosya_indir(url, yol):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, stream=True, timeout=60)
        # 20KB altı bozuk dosyaları eler
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
    arsiv = json.load(open(ARSIV_DOSYA)) if os.path.exists(ARSIV_DOSYA) else []
    for hesap in HESAPLAR:
        os.makedirs(hesap, exist_ok=True)
        found = get_links(hesap, arsiv)
        for i, link in enumerate(found):
            yol = f"{hesap}/{int(time.time())}_{i}.mp4"
            if dosya_indir(link, yol):
                drive_yukle(yol, DRIVE_KLASOR_ID)
                arsiv.append(link)
                print(f"☁️ 2TB Drive'a yüklendi: {yol}")
                if os.path.exists(yol): os.remove(yol)
    with open(ARSIV_DOSYA, "w") as f: json.dump(arsiv, f)
    print("🎉 İşlem başarıyla bitti.")
