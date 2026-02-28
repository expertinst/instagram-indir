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
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        # 🛡️ REKLAM ENGELLEYİCİ: Videonun önüne çıkan reklamları bloklar
        page.route("**/*", lambda route: route.abort() if any(x in route.request.url for x in ["doubleclick", "ads", "analytics", "googlead"]) else route.continue_())

        try:
            print(f"🔍 {hesap} taranıyor...")
            page.goto("https://fastdl.dev/", wait_until="domcontentloaded", timeout=60000)
            
            box = page.locator('input[name="url"]').first
            box.wait_for(timeout=20000)
            box.fill(target)
            page.keyboard.press("Enter")
            
            # Sonuçların yüklenmesini bekle
            page.wait_for_selector('.download-box, a[href*="mp4"]', timeout=40000)
            time.sleep(10)
            
            # Linkleri topla: .mp4 olanları en başa al (Video önceliği)
            anchors = page.locator('a[href*="mp4"], a[href*="token="], a[href*=".jpg"]').all()
            for a in anchors:
                href = a.get_attribute("href")
                if href and href not in arsiv and href not in linkler:
                    if "googlevideo" not in href: # Reklam videolarını ele
                        linkler.append(href)
        except:
            pass
        browser.close()
    return linkler

def dosya_indir(url, yol):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, stream=True, timeout=60)
        # Sadece gerçek dosyaları (20KB üstü) indir
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
    # Klasör adını ve dosya adını al
    klasor_adi = os.path.dirname(yol).split('/')[-1]
    dosya_adi = os.path.basename(yol)
    
    meta = {"name": f"[{klasor_adi}] {dosya_adi}", "parents": [klasor_id]}
    media = MediaFileUpload(yol, resumable=True)
    service.files().create(body=meta, media_body=media).execute()

if __name__ == "__main__":
    kurulum()
    arsiv = json.load(open(ARSIV_DOSYA)) if os.path.exists(ARSIV_DOSYA) else []
    
    for hesap in HESAPLAR:
        # 📂 KLASÖR OLUŞTURMA: GitHub üzerinde geçici klasör açar
        if not os.path.exists(hesap):
            os.makedirs(hesap)
            
        found = get_links(hesap, arsiv)
        for i, link in enumerate(found):
            # 🎥 VİDEO/FOTO AYRIMI: Linke göre uzantı belirle
            is_video = "mp4" in link or "video" in link
            ext = "mp4" if is_video else "jpg"
            yol = f"{hesap}/{int(time.time())}_{i}.{ext}"
            
            if dosya_indir(link, yol):
                try:
                    drive_yukle(yol, DRIVE_KLASOR_ID)
                    arsiv.append(link)
                    print(f"✅ {yol} yüklendi.")
                finally:
                    if os.path.exists(yol): os.remove(yol)
                    
    with open(ARSIV_DOSYA, "w") as f: json.dump(arsiv, f)
