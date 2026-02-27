import os
import sys
import subprocess
import json
import base64
from pathlib import Path

# ═══════════════════════════════════════
# SADECE BURAYI DÜZENLE
HESAPLAR = [
    "motive2m",
    "nerdesinpango",
]
DRIVE_KLASOR_ID = "1Oxvkiq2QcEhjTIBCH7leGsKPuSNpKPCd"
# ═══════════════════════════════════════

def kurulum():
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                          "yt-dlp", "google-api-python-client",
                          "google-auth", "-q"])

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
    arsiv = f"/tmp/{hesap}_arsiv.txt"
    os.makedirs(gecici, exist_ok=True)

    drive_klasor = klasor_bul_veya_olustur(service, hesap, DRIVE_KLASOR_ID)

    print(f"\n📥 Kontrol ediliyor: @{hesap}")

    # Postlar ve Reels
    subprocess.run([
        sys.executable, "-m", "yt_dlp",
        "--download-archive", arsiv,
        "--output", f"{gecici}/%(upload_date)s_%(id)s.%(ext)s",
        "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--no-warnings",
        "--quiet",
        f"https://www.instagram.com/{hesap}/",
    ])

    # Stories
    subprocess.run([
        sys.executable, "-m", "yt_dlp",
        "--download-archive", arsiv,
        "--output", f"{gecici}/story_%(upload_date)s_%(id)s.%(ext)s",
        "--format", "best",
        "--no-warnings",
        "--quiet",
        f"https://www.instagram.com/stories/{hesap}/",
    ])

    # Drive'a yükle
    yuklenen = 0
    for dosya in Path(gecici).glob("*"):
        if dosya.is_file() and dosya.suffix in [".mp4", ".jpg", ".jpeg", ".png", ".webp"]:
            drive_yukle(service, str(dosya), drive_klasor)
            yuklenen += 1

    print(f"✅ {hesap}: {yuklenen} dosya işlendi")

if __name__ == "__main__":
    kurulum()
    service = drive_baglanti()
    for hesap in HESAPLAR:
        hesap_indir(service, hesap.strip())
    print("\n🎉 Tamamlandı!")
