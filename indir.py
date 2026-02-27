import os
import sys
import subprocess
import json
import base64
from pathlib import Path

# ═══════════════════════════════════════
# TAKİP EDİLECEK HESAPLAR
HESAPLAR = [
    "motive2m",
    "nerdesinpango",
]
DRIVE_KLASOR_ID = "BURAYA_KLASOR_ID_YAZACAZ"  # sonra dolduracağız
# ═══════════════════════════════════════

def kurulum():
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "instaloader", "google-api-python-client",
                          "google-auth", "-q"])

def drive_baglanti():
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    import json, base64

    creds_json = base64.b64decode(os.environ["GDRIVE_CREDENTIALS"]).decode()
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

def klasor_bul_veya_olustur(service, ad, ust_klasor_id):
    q = f"name='{ad}' and '{ust_klasor_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    sonuc = service.files().list(q=q).execute().get("files", [])
    if sonuc:
        return sonuc[0]["id"]
    meta = {"name": ad, "mimeType": "application/vnd.google-apps.folder", "parents": [ust_klasor_id]}
    return service.files().create(body=meta, fields="id").execute()["id"]

def drive_yukle(service, dosya_yolu, klasor_id):
    from googleapiclient.http import MediaFileUpload
    ad = os.path.basename(dosya_yolu)
    q = f"name='{ad}' and '{klasor_id}' in parents and trashed=false"
    varmi = service.files().list(q=q).execute().get("files", [])
    if varmi:
        return  # zaten var, atlat
    meta = {"name": ad, "parents": [klasor_id]}
    media = MediaFileUpload(dosya_yolu)
    service.files().create(body=meta, media_body=media).execute()
    print(f"  ☁️ Yüklendi: {ad}")

def hesap_indir_ve_yukle(service, hesap):
    import instaloader
    L = instaloader.Instaloader(
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        post_metadata_txt_pattern=""
    )
    
    gecici_klasor = f"/tmp/{hesap}"
    os.makedirs(gecici_klasor, exist_ok=True)
    
    drive_hesap_klasor = klasor_bul_veya_olustur(service, hesap, DRIVE_KLASOR_ID)
    
    print(f"\n📥 İndiriliyor: @{hesap}")
    try:
        profil = instaloader.Profile.from_username(L.context, hesap)
        
        # Postlar
        for post in profil.get_posts():
            dosya_adi = f"{post.date_utc.strftime('%Y-%m-%d')}_{post.shortcode}"
            hedef = os.path.join(gecici_klasor, dosya_adi)
            L.dirname_pattern = gecici_klasor
            L.download_post(post, target=gecici_klasor)
            break  # test için sadece son post, sonra kaldırırız
            
        # Klasördeki her dosyayı Drive'a yükle
        for dosya in Path(gecici_klasor).glob("*"):
            if dosya.is_file() and not dosya.suffix == ".txt":
                drive_yukle(service, str(dosya), drive_hesap_klasor)
                
        print(f"✅ Tamamlandı: @{hesap}")
    except Exception as e:
        print(f"❌ Hata ({hesap}): {e}")

if __name__ == "__main__":
    kurulum()
    service = drive_baglanti()
    for hesap in HESAPLAR:
        hesap_indir_ve_yukle(service, hesap.strip())
    print("\n🎉 Bitti!")
