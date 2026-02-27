import os
import sys
import subprocess
import json
import base64
import time
from pathlib import Path

# ═══════════════════════════════════════
HESAPLAR = [
    "motive2m",
    "nerdesinpango",
]
DRIVE_KLASOR_ID = "1OaRDgcKjbEKM1gPny3CE19s8vaFUs03T"
ARSIV_DOSYA = "arsiv.json"
# ═══════════════════════════════════════

def kurulum():
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                          "playwright", "google-api-python-client",
                          "google-auth", "-q"])
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
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for url in urls:
            print(f"  🔗 {url}")
            try:
                page.goto("https://fastdl.dev/", timeout=30000)
                page.wait_for_selector('input[name="url"], input[type="text"]', timeout=10000)
                input_el = page.locator('input[name="url"], input[type="text"]').first
                input_el.fill(url)
                page.keyboard.press("Enter")
                page.wait_for_selector('.download-box, .download-items, a[href*="mp4"], a[href*="snapcdn"]', timeout=15000)
                time.sleep(2)
                # Download linklerini topla
                anchors = page.locator('a[href*="snapcdn"], a[href*=".mp4"], a[href*=".jpg"]').all()
                for a in anchors:
                    href = a.get_attribute("href")
                    if href and href not in arsiv and href not in linkler:
                        linkler.append(href)
                        print(f"  ✅ Link bulundu: {href[:80]}")
            except Exception as e:
                print(f"  ❌ Hata: {e}")
        browser.close()
    return linkler

def dosya_indir(url, hedef_yol):
    import requests
    try:
        headers = {
            "Referer": "https://fastdl.dev/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        resp = requests.get(url, headers=headers, stream=True, timeout=60)
        if resp.status_code == 200:
            with open(hedef_yol, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        print(f"  ❌ İndirme hatası: HTTP {resp.status_code}")
        return False
    except Exception as e:
        print(f"  ❌ İndirme hatası: {e}")
        return False

def drive_baglanti():
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    creds_json = base64.b64decode(os.environ["GDRIVE_CREDENTIALS"]).decode()
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

def klasor_bul_veya_olustur(service, ad, ust_id):
    q = f"name='{ad}' and '{ust_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
