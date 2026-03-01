import os, sys, subprocess, json, time

# ══════════════════════════════════════════════════════════════════════════
TUM_HESAPLAR = [
    "dogacakr", "minasolakk", "suedaauluca", "zeybik", "pynarlidia",
    "g.unes", "motive2m", "bluvrts", "esyundo", "lvbelc5",
    "hilalyelekci", "esin.bahat", "bestiaydeniz_", "aydeedlicious", "uzielchavo",
    "weghrumi", "m6nifestgirls", "nerdesinpango", "nisasoygudenn", "aynisinemalar",
    "jefe.045", "kaanhsl", "chef.akdo", "daniela_avanzi", "zeyyoa",
    "selin.gecit", "cybellegucluer", "ecebgs", "nazlicogan", "damladgen",
    "iamrubyboi", "beril.turhanlar", "ege_waw", "melimlisa", "belina.cebi",
    "savanaworldwide", "13killoki", "sudesseen", "_nazlalceyhan_", "113ulas",
    "katseyeworld", "eseerrr_", "reckol17yeni", "_ecertugrul_", "meganskiendiel",
    "big5.turkiye", "batuflex", "therealbaneva", "aiseayin", "baranguvennnn",
    "naseneer", "defalonee", "ozlemgozcu_", "aaslisivri", "naxliates",
    "alaraserena", "alo.waxy", "lacin_martynov", "d3.anaf", "ezgiguclu",
    "moddgng", "fatimelariz", "berkcan", "mertcanbaharr", "orb.one",
    "jeffreddofficiel", "segah.808", "berikasonmez", "betulcicekyurt", "azraonaay",
    "bekom045", "zezfyi", "asyaalizaude", "rengin.duru", "laralouisewellington",
    "organize034", "endertheluv", "silabbayrak", "yilmaztuana", "abugat.anaf",
    "d.azy", "baranmengucc", "alphiakidd", "tai.junge", "erosenn9",
    "benyokumfarzet", "bugymusic", "kum.tv", "ahmetemresaka", "cakal.95",
    "eftalyayagcii", "elvin.ozky", "xxxtentacion", "zekiiarkun", "ezhel06",
    "ardaguler", "tyla", "rraenee", "tugkangonultas", "kayrazapkinus",
    "vessboi", "tchalamet", "meretmanon", "didomidosong", "caarlossainz55",
    "ferdikadioglu", "charles_leclerc", "f1", "swirff", "centralcee",
    "oscarpiastri", "ester_exposito", "zeynep.okktay"
]
# ══════════════════════════════════════════════════════════════════════════

DRIVE_KLASOR_ID = "1OaRDgcKjbEKM1gPny3CE19s8vaFUs03T"
ARSIV_DOSYA = "arsiv.json"

def kurulum():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "google-api-python-client", "google-auth", "-q"])

def get_drive_folder_id(service, parent_id, folder_name):
    query = f"name = '{folder_name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    items = service.files().list(q=query, fields="files(id)").execute().get('files', [])
    if items: return items[0]['id']
    return service.files().create(body={'name': folder_name, 'parents': [parent_id], 'mimeType': 'application/vnd.google-apps.folder'}, fields='id').execute().get('id')

def grup_ayir(liste, toplam_grup):
    grup_no = int(os.environ.get("GRUP_NO", 0))
    parca = len(liste) // toplam_grup
    if parca == 0: parca = 1
    bas = grup_no * parca
    return liste[bas:] if grup_no == (toplam_grup - 1) else liste[bas : bas + parca]

if __name__ == "__main__":
    grup_no = int(os.environ.get("GRUP_NO", 0))
    
    bekleme_suresi = grup_no * 3 
    if bekleme_suresi > 0:
        time.sleep(bekleme_suresi)

    kurulum()
    import yt_dlp
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from googleapiclient.http import MediaFileUpload
    
    session_id = os.environ.get("IG_SESSIONID")
    if not session_id:
        print("❌ HATA: IG_SESSIONID bulunamadı!")
        sys.exit(1)
        
    creds = Credentials.from_authorized_user_info(json.loads(os.environ.get("GDRIVE_TOKEN")))
    service = build("drive", "v3", credentials=creds)
    
    HESAPLAR = grup_ayir(TUM_HESAPLAR, 10)
    print(f"🚀 GRUP {grup_no} BAŞLADI (Direct API Mode): {HESAPLAR}")
    
    arsiv = json.load(open(ARSIV_DOSYA)) if os.path.exists(ARSIV_DOSYA) else []
    
    # yt-dlp'nin tekrarları atlaması için arşivi geçici dosyaya yazıyoruz
    with open("yt_archive.txt", "w") as f:
        for kayit in arsiv:
            f.write(f"instagram {kayit}\n")
            
    for hesap in HESAPLAR:
        print(f"🔍 Taranıyor: @{hesap}")
        os.makedirs(hesap, exist_ok=True)
        target_folder = get_drive_folder_id(service, DRIVE_KLASOR_ID, hesap)
        
        ydl_opts = {
            'outtmpl': f'{hesap}/%(id)s.%(ext)s',
            'http_headers': {'Cookie': f'sessionid={session_id}'},
            'download_archive': 'yt_archive.txt',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'sleep_requests': 1.5, # Sahte hesabın banlanmaması için nefes aralığı
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([f'https://www.instagram.com/stories/{hesap}/'])
            except: pass
            
        for dosya in os.listdir(hesap):
            yol = os.path.join(hesap, dosya)
            if os.path.isfile(yol):
                if os.path.getsize(yol) > 20000:
                    try:
                        service.files().create(body={'name': dosya, 'parents': [target_folder]}, media_body=MediaFileUpload(yol, resumable=True)).execute()
                        print(f"✅ Klasöre Yüklendi: {dosya}")
                    except Exception as e:
                        print(f"❌ Yükleme hatası: {e}")
                os.remove(yol)
        
        time.sleep(3)
        
    # Yeni indirilen videoların ID'lerini ana arşive kaydet
    if os.path.exists("yt_archive.txt"):
        with open("yt_archive.txt", "r") as f:
            for line in f:
                if line.startswith("instagram "):
                    vid = line.strip().split(" ")[1]
                    if vid not in arsiv:
                        arsiv.append(vid)
                        
    with open(ARSIV_DOSYA, "w") as f: json.dump(arsiv, f)
