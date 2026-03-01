import os, sys, subprocess, json, time, requests

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
INDEX_DOSYA = "kaldigimiz_yer.txt"

def kurulum():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "google-api-python-client", "google-auth", "requests", "-q"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

def get_drive_folder_id(service, parent_id, folder_name):
    query = f"name = '{folder_name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id)").execute()
    items = results.get('files', [])
    if items:
        return items[0]['id']
    else:
        file_metadata = {'name': folder_name, 'parents': [parent_id], 'mimeType': 'application/vnd.google-apps.folder'}
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')

def get_links(hesap, arsiv):
    from playwright.sync_api import sync_playwright
    linkler = []
    target = f"https://www.instagram.com/stories/{hesap}/"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        page.route("**/*", lambda route: route.abort() if any(x in route.request.url for x in ["ads", "doubleclick"]) else route.continue_())

        try:
            print(f"🔍 {hesap} taranıyor...")
            page.goto("https://fastdl.dev/", wait_until="domcontentloaded", timeout=60000)
            page.fill('input[name="url"]', target)
            page.keyboard.press("Enter")
            
            page.wait_for_selector('.download-box, a[href*="mp4"]', timeout=45000)
            time.sleep(12) 
            
            anchors = page.locator('a[href*="mp4"], a[href*="token="]').all()
            for a in anchors:
                href = a.get_attribute("href")
                if href and href not in arsiv and href not in linkler:
                    if "googlevideo" not in href:
                        linkler.append(href)
        except Exception as e:
            print(f"⚠️ @{hesap} bulunamadı veya şu an hikayesi yok.")
        
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
    
    # Nerede kaldığımızı oku
    try:
        with open(INDEX_DOSYA, "r") as f:
            baslangic = int(f.read().strip())
    except:
        baslangic = 0

    # Sadece 5 hesap al
    bitis = baslangic + 5
    islem_gorecekler = TUM_HESAPLAR[baslangic:bitis]
    
    print(f"🚀 Otomasyon Başladı! (Sıra: {baslangic} ile {bitis} arası)")

    creds = Credentials.from_authorized_user_info(json.loads(os.environ.get("GDRIVE_TOKEN")))
    service = build("drive", "v3", credentials=creds)
    
    arsiv = json.load(open(ARSIV_DOSYA)) if os.path.exists(ARSIV_DOSYA) else []
    
    for hesap in islem_gorecekler:
        os.makedirs(hesap, exist_ok=True)
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
                    print(f"✅ Klasöre Yüklendi: {yol}")
                if os.path.exists(yol): os.remove(yol)
            except Exception as e: 
                print(f"❌ İndirme hatası: {e}")
                
        time.sleep(5)
            
    with open(ARSIV_DOSYA, "w") as f: json.dump(arsiv, f)
    
    # Yeni index'i kaydet (Listenin sonuna gelirse başa dön)
    yeni_baslangic = bitis if bitis < len(TUM_HESAPLAR) else 0
    with open(INDEX_DOSYA, "w") as f: f.write(str(yeni_baslangic))
    print(f"🛑 İşlem bitti. Bir sonraki turda {yeni_baslangic}. sıradan devam edilecek.")
