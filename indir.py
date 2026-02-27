import os
import sys
import subprocess
import json
import base64
import requests
import time
from pathlib import Path

# ═══════════════════════════════════════
HESAPLAR = [
    "motive2m",
    "nerdesinpango",
]
DRIVE_KLASOR_ID = "1Oxvkiq2QcEhjTIBCH7leGsKPuSNpKPCd"
# ═══════════════════════════════════════

def kurulum():
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                          "requests", "google-api-python-client",
                          "google-auth", "-q"])

def fastdl_indir(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://fastdl.dev",
            "Referer": "https://fastdl.dev/",
        }
        resp = requests.post(
            "https://fastdl.dev/api/ajaxSearch",
            data={"q": url, "t": "media", "v": "v2", "lang": "en", "cftoken": ""},
            headers=headers,
            timeout=30
        )
        print(f"  📡 FastDl yanıtı: {resp.status_code}")
        print(f"  📡 FastDl içerik: {resp.text[:500]}")
        data = resp.json()
        linkler = []
        if data.get("url"):
            for item in data["url"]:
                if item.get("url"):
                    linkler.append(item["url"])
        return linkler
    except Exception as e:
        print(f"  ❌ FastDl hatası: {e}")
        return []
def dosya_indir(url, hedef_yol):
    try:
        resp = requests.get(url, stream=True, timeout=60)
        with open(hedef_yol, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except:
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
    sonuc = service.files().list(q=q).execute().get("files", [])
    if sonuc:
        return sonuc[0]["id"]
    meta = {"name": ad, "mimeType": "application/vnd.google-apps.folder", "parents": [ust_id]}
    return service.files().create(body=meta, fields="id").execute()["id"]

def drive_yukle(service, dosya_yolu, klasor_id):
    from googleapiclient.http import MediaFileUpload
    ad = os.path.basename(dosya_yolu)
    q = f"name='{ad}' and '{klasor_id}' in parents and trashed=false"
    if service.files().list(q=q).execute().get("files"):
        print(f"  ⏭️ Zaten var: {ad}")
        return
    meta = {"name": ad, "parents": [klasor_id]}
    media = MediaFileUpload(dosya_yolu, resumable=True)
    service.files().create(body=meta, media_body=media).execute()
    print(f"  ☁️ Yüklendi: {ad}")

def hesap_indir(service, hesap):
    gecici = f"/tmp/{hesap}"
    os.makedirs(gecici, exist_ok=True)
    drive_klasor = klasor_bul_veya_olustur(service, hesap, DRIVE_KLASOR_ID)
    print(f"\n📥 İşleniyor: @{hesap}")

    urls = [
        f"https://www.instagram.com/stories/{hesap}/",
        f"https://www.instagram.com/{hesap}/",
    ]

    yuklenen = 0
    for url in urls:
        print(f"  🔗 {url}")
        linkler = fastdl_indir(url)
        for i, link in enumerate(linkler):
            ext = "mp4" if "video" in link else "jpg"
            dosya_adi = f"{gecici}/{hesap}_{int(time.time())}_{i}.{ext}"
            if dosya_indir(link, dosya_adi):
                drive_yukle(service, dosya_adi, drive_klasor)
                yuklenen += 1
        time.sleep(2)

    print(f"✅ {hesap}: {yuklenen} dosya yüklendi")

if __name__ == "__main__":
    kurulum()
    service = drive_baglanti()
    for hesap in HESAPLAR:
        hesap_indir(service, hesap.strip())
    print("\n🎉 Tamamlandı!")
