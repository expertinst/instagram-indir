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
    # Hem profil hem story linkini kontrol ederek şansı artırıyoruz
    test_urls = [f"https://www.instagram.com/stories/{hesap}/", f"https://www.instagram.com/{hesap}/"]
    sites = ["https://fastdl.dev/", "https://saveig.app/en/instagram-story-downloader", "https://snapinsta.app/"]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        # 🛡️ Reklam ve gereksiz yükleri engelleyerek sayfayı hızlandırıyoruz
        page.route("**/*", lambda route: route.abort() if any(x in route.request.url for x in ["ads", "analytics", "doubleclick", "google"]) else route.continue_())

        for site in sites:
            for insta_url in test_urls:
                try:
                    print(f"📡 {site} üzerinden {insta_url} kontrol ediliyor...")
                    page.goto(site, timeout=60000, wait_until="domcontentloaded")
                    
                    box = page.locator('input[name="url"], input[id*="url"], input[placeholder*="Instagram"]').first
                    box.wait_for(timeout=15000)
                    box.fill(insta_url)
                    page.keyboard.press("Enter")
                    
                    # 🎥 Video butonlarının gelmesi için daha inatçı bekliyoruz
                    page.wait_for_selector('a[href*="mp4"], a[href*="token="], .download-items', timeout=45000)
                    time.sleep(12) 
                    
                    # Tüm indirme butonlarını tara
                    anchors = page.locator('a[href*="download"], a[href*="token="], a[href*=".mp4"], a[href*=".jpg"]').all()
                    
                    temp_links = []
                    for a in anchors:
                        href = a.get_attribute("href")
                        if href and href not in arsiv:
                            # Reklamları ele ve listeye ekle
                            if "googlevideo" not in href and "doubleclick" not in href:
                                temp_links.append(href)
                    
                    if temp_links:
                        # 🏁 STRATEJİ: Listede mp4 varsa onu en başa al (Video Önceliği)
                        temp_links.sort(key=lambda x: ("mp4" in x or "video" in x), reverse=True)
                        linkler.extend(temp_links)
                        print(f"✅ {len(linkler)} içerik (video/foto) yakalandı.")
                        break 
                except: continue
            if linkler: break 
        browser.close()
    return linkler

def dosya_indir(url, yol_base):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, stream=True, timeout=60)
        
        if resp.status_code == 200:
            # 🛡️ KRİTİK NOKTA: Dosyanın gerçek türünü Header'dan kontrol et
            content_type = resp.headers.get('Content-Type', '').lower()
            size = int(resp.headers.get('Content-Length', 0))
            
            # 20KB altı çöp dosyaları engelle
            if size < 20000: return None
            
            # Uzantıyı belirle
            ext = ".mp4" if "video" in content_type else ".jpg"
            tam_yol = yol_base + ext
            
            with open(tam_yol, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192): f.write(chunk)
            return tam_yol
    except: return None
    return None

def drive_yukle(yol, klasor_id):
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from googleapiclient.http import MediaFileUpload
    creds = Credentials.from_authorized_user_info(json.loads(os.environ.get("GDRIVE_TOKEN")))
    service = build("drive", "v3", credentials=creds)
    media = MediaFileUpload(yol, resumable=True)
    # Dosya isminin başına hesap adını ekle ki Drive'da karışmasın
    ad = os.path.basename(yol)
    service.files().create(body={"name": ad, "parents": [klasor_id]}, media_body=media).execute()

if __name__ == "__main__":
    kurulum()
    arsiv = json.load(open(ARSIV_DOSYA)) if os.path.exists(ARSIV_DOSYA) else []
    
    for hesap in HESAPLAR:
        os.makedirs(hesap, exist_ok=True)
        found = get_links(hesap, arsiv)
        
        for i, link in enumerate(found):
            # Uzantıyı dosya_indir içinde belirleyeceğiz
            yol_temel = f"{hesap}/{hesap}_{int(time.time())}_{i}"
            
            indirilen_yol = dosya_indir(link, yol_temel)
            if indirilen_yol:
                try:
                    drive_yukle(indirilen_yol, DRIVE_KLASOR_ID)
                    arsiv.append(link)
                    print(f"☁️ Yüklendi: {indirilen_yol}")
                finally:
                    if os.path.exists(indirilen_yol): os.remove(indirilen_yol)
                    
    with open(ARSIV_DOSYA, "w") as f: json.dump(arsiv, f)
