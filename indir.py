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

def kurulum():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "google-api-python-client", "google-auth", "requests", "-q"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

def get_drive_folder_id(service, parent_id, folder_name):
    query = f"name = '{folder_name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    items = service.files().list(q=query, fields="files(id)").execute().get('files', [])
    if items: return items[0]['id']
    return service.files().create(body={'name': folder_name, 'parents': [parent_id], 'mimeType': 'application/vnd.google-apps.folder'}, fields='id').execute().get('id')

def get_links(hesap, arsiv):
    from playwright.sync_api import sync_playwright
    linkler = []
    target = f"https://www.instagram.com/stories/{hesap}/"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page.route("**/*", lambda route: route.abort() if any(x in route.request.url for x in ["ads", "doubleclick", "analytics"]) else route.continue_())
        
        try:
            print(f"🔍 Taranıyor: @{hesap}")
            page.goto("https://fastdl.dev/", wait_until="domcontentloaded", timeout=60000)
            page.fill('input[name="url"]', target)
            page.keyboard.press("Enter")
            
            page.wait_for_selector('.download-box, a[href*="mp4"]', timeout=40000)
            time.sleep(10)
            
            anchors = page.locator('a[href*="mp4"], a[href*="token="]').all()
            for a in anchors:
                href = a.get_attribute("href")
                if href and href not in arsiv and "googlevideo" not in href:
                    linkler.append(href)
        except Exception as e:
            # Hata mesajını artık gizlemiyoruz, doğrudan loga yazdırıyoruz
            print(f"⚠️ @{hesap} BULUNAMADI. HATA DETAYI: {str(e)[:150]}")
        
        browser.close()
    return linkler

def grup_ayir(liste, toplam_grup):
    grup_no = int(os.environ.get("GRUP_NO", 0))
    parca = len(liste) // toplam_grup
    if parca == 0: parca = 1
    bas = grup_no * parca
    return liste[bas:] if grup_no == (toplam_grup - 1) else liste[bas : bas + parca]

if __name__ == "__main__":
    grup_no = int(os.environ.get("GRUP_NO", 0))
    
    # 🛡️ IP BAN ÖNLEMİ: Botlar aynı anda siteye saldırmasın diye sırayla bekletiyoruz
    bekleme_suresi = grup_no * 15
    if bekleme_suresi > 0:
        print(f"⏳ IP engeli yememek için {bekleme_suresi} saniye bekleniyor...")
        time.sleep(bekleme_suresi)

    kurulum()
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from googleapiclient.http import MediaFileUpload
    
    creds = Credentials.from_authorized_user_info(json.loads(os.environ.get("GDRIVE_TOKEN")))
    service = build("drive", "v3", credentials=creds)
    
    HESAPLAR = grup_ayir(TUM_HESAPLAR, 10)
    print(f"🚀 GRUP {grup_no} BAŞLADI: {HESAPLAR}")
    
    arsiv = json.load(open(ARSIV_DOSYA)) if os.path.exists(ARSIV_DOSYA) else []
    
    for hesap in HESAPLAR:
        os.makedirs(hesap, exist_ok=True)
        target_folder = get_drive_folder_id(service, DRIVE_KLASOR_ID, hesap)
        found = get_links(hesap, arsiv)
        
        if not found:
            continue
            
        for i, link in enumerate(found):
            ext = "mp4" if "mp4" in link or "video" in link else "jpg"
            yol = f"{hesap}/{hesap}_{int(time.time())}_{i}.{ext}"
            
            try:
                resp = requests.get(link, stream=True, timeout=60)
                if resp.status_code == 200:
                    with open(yol, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192): f.write(chunk)
                    
                    if os.path.getsize(yol) > 20000:
                        service.files().create(body={'name': os.path.basename(yol), 'parents': [target_folder]}, media_body=MediaFileUpload(yol, resumable=True)).execute()
                        arsiv.append(link)
                        print(f"✅ Klasöre Yüklendi: {yol}")
                    else:
                        print(f"🚫 Bozuk dosya atlandı: {yol}")
                
                if os.path.exists(yol): os.remove(yol)
            except Exception as e:
                print(f"❌ İndirme hatası: {e}")
                
    with open(ARSIV_DOSYA, "w") as f: json.dump(arsiv, f)
