import os
import sys
import subprocess
import json
import time
import requests

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
        
        for site in sites:
            try:
                page.goto(site, wait_until="domcontentloaded", timeout=60000)
                input_selector = 'input[name="url"]'
                page.wait_for_selector(input_selector, timeout=20000)
                page.fill(input_selector, target)
                page.keyboard.press("Enter")
                
                page.wait_for_selector('a[href*="mp4"], a[href*="snapcdn"], .download-items', timeout=30000)
                time.sleep(10)
                
                items = page.locator('a[href*="mp4"], a[href*="snapcdn"], a[href*=".jpg"]').all()
                for item in items:
                    href = item.get_attribute("href")
                    if href and href not in arsiv and href not in linkler:
                        if "doubleclick" not in href and "google" not in href:
                            linkler.append(href)
                if linkler: break 
            except: continue
        browser.close()
    return linkler

def dosya_indir(url, yol):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, stream=True, timeout=40)
        size = int(resp.headers.get('Content-Length', 0))
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
    creds = Credentials.from_authorized_user_info(json.loads(token_json))
    return build("drive", "v3", credentials=creds)

def drive_yukle(service, yol, klasor_id):
    from googleapiclient.http import MediaFileUpload
    ad = os.path.basename(yol)
    meta = {"name": ad, "parents": [klasor_id]}
    media = MediaFileUpload(yol, resumable=True)
    service.files().create(body=meta, media_body=media).execute()

if __name__ == "__main__":
    kurulum()
    try:
        service = drive_baglanti()
        arsiv = json.load(open(ARSIV_DOSYA, "r")) if os.path.exists(ARSIV_DOSYA) else []
        for hesap in HESAPLAR:
            os.makedirs(hesap, exist_ok=True)
            linkler = get_links(hesap, arsiv)
            for i, link in enumerate(linkler):
                ext = "mp4" if "mp4" in link or "video" in link else "jpg"
                yol = f"{hesap}/{int(time.time())}_{i}.{ext}"
                if dosya_indir(link, yol):
                    drive_yukle(service, yol, DRIVE_KLASOR_ID)
                    arsiv.append(link)
                    if os.path.exists(yol): os.remove(yol)
        with open(ARSIV_DOSYA, "w") as f: json.dump(arsiv, f)
    except: pass
