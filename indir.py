import os, sys, subprocess, json, time, requests

# AYARLAR
HESAPLAR = ["motive2m", "zeynep.okktay"]
DRIVE_KLASOR_ID = "1OaRDgcKjbEKM1gPny3CE19s8vaFUs03T"
ARSIV_DOSYA = "arsiv.json"

def kurulum():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "google-api-python-client", "google-auth", "requests", "-q"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

def get_drive_folder_id(service, parent_id, folder_name):
    # Drive içinde bu hesap adında bir klasör var mı kontrol et
    query = f"name = '{folder_name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id)").execute()
    items = results.get('files', [])
    
    if items:
        return items[0]['id']
    else:
        # Klasör yoksa oluştur
        file_metadata = {
            'name': folder_name,
            'parents': [parent_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        print(f"📂 Yeni klasör oluşturuldu: {folder_name}")
        return folder.get('id')

def get_links(hesap, arsiv):
    from playwright.sync_api import sync_playwright
    linkler = []
    target = f"https://www.instagram.com/stories/{hesap}/"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        # Reklamları engelle
        page.route("**/*", lambda route: route.abort() if any(x in route.request.url for x in ["ads", "doubleclick"]) else route.continue_())

        try:
            print(f"🔍 {hesap} taranıyor...")
            page.goto("https://fastdl.dev/", wait_until="domcontentloaded", timeout=60000)
            page.fill('input[name="url"]', target)
            page.keyboard.press("Enter")
            
            # Linklerin oluşmasını bekle
            page.wait_for_selector('.download-box, a[href*="mp4"]', timeout=45000)
            time.sleep(12) 
            
            # 🛡️ SES SORUNU İÇİN: Sadece gerçek indirme linklerini yakala
            # Genelde 'download' veya '.mp4' içeren linkler sesli olanlardır
            anchors = page.locator('a[href*="mp4"], a[href*="token="]').all()
            for a in anchors:
                href = a.get_attribute("href")
                if href and href not in arsiv and href not in linkler:
                    # 'googlevideo' gibi sessiz önizleme linklerini atla
                    if "googlevideo" not in href:
                        linkler.append(href)
        except: pass
        browser.close()
    return linkler

def drive_yukle(service, yol, target_folder_id):
    from googleapiclient.http import MediaFileUpload
    ad = os.path.basename(yol)
    meta = {"name": ad, "parents": [target_folder_id]}
    media = MediaFileUpload(yol, resumable=True)
    service.files().create(body=meta, media_body=media).execute()

if __name__ == "__main__":
    kurulum()
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    
    # Drive bağlantısını bir kez kur
    creds = Credentials.from_authorized_user_info(json.loads(os.environ.get("GDRIVE_TOKEN")))
    service = build("drive", "v3", credentials=creds)
    
    arsiv = json.load(open(ARSIV_DOSYA)) if os.path.exists(ARSIV_DOSYA) else []
    
    for hesap in HESAPLAR:
        os.makedirs(hesap, exist_ok=True)
        # 📂 Hesap için klasör ID'sini al veya oluştur
        target_folder = get_drive_folder_id(service, DRIVE_KLASOR_ID, hesap)
        
        found = get_links(hesap, arsiv)
        for i, link in enumerate(found):
            ext = "mp4" if "mp4" in link or "video" in link else "jpg"
            yol = f"{hesap}/{hesap}_{int(time.time())}_{i}.{ext}"
            
            try:
                resp = requests.get(link, stream=True, timeout=60)
                if resp.status_code == 200 and int(resp.headers.get('Content-Length', 0)) > 20000:
                    with open(yol, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192): f.write(chunk)
                    
                    drive_yukle(service, yol, target_folder)
                    arsiv.append(link)
                    print(f"✅ Yüklendi: {yol}")
                if os.path.exists(yol): os.remove(yol)
            except: continue
            
    with open(ARSIV_DOSYA, "w") as f: json.dump(arsiv, f)
