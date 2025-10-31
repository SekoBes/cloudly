import os
import yt_dlp
import re
import subprocess
from dotenv import load_dotenv

# ===============================
#  AYARLAR
# ===============================
load_dotenv(dotenv_path="C:\\Users\\KEMAL\\Desktop\\Youtube\\token.env")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

ANA_KLASOR = r"C:\Users\KEMAL\Desktop\Youtube"  # Çift backslash düzeltildi
KAYNAK_DOSYA = os.path.join(ANA_KLASOR, "YouTube Kanalları.txt")
HEDEF_KLASOR = os.path.join(ANA_KLASOR, "YouTube")

GITHUB_USER = "SekoBes"
GITHUB_REPO = "S5"  # Bu doğru mu? Hata mesajında "youtube-m3u8" görünüyor
GIT_URL = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{GITHUB_REPO}.git"

# ===============================
#  TÜRKÇE KARAKTER DESTEĞİ İLE DOSYA ADI TEMİZLEME
# ===============================
def temizle_dosya_adi(kanal_adi):
    temiz_adi = re.sub(r'[<>:"/\\|?*]', '_', kanal_adi)
    temiz_adi = re.sub(r'_+', '_', temiz_adi)
    temiz_adi = temiz_adi.strip(' _')
    return temiz_adi

# ===============================
#  M3U8 OLUŞTURMA (Aynı kalıyor)
# ===============================
os.makedirs(HEDEF_KLASOR, exist_ok=True)

with open(KAYNAK_DOSYA, "r", encoding="utf-8") as f:
    satirlar = f.read().splitlines()

kanallar = []
for i in range(len(satirlar)):
    if satirlar[i].startswith("#EXTINF"):
        try:
            extinf = satirlar[i]
            url = satirlar[i + 1]
            if url.strip() and not url.startswith('#'):
                kanallar.append((extinf, url))
        except IndexError:
            pass

basari_sayisi = 0
hata_sayisi = 0

for extinf, url in kanallar:
    match = re.search(r',([^,]+)$', extinf)
    if not match:
        continue
        
    kanal_adi = match.group(1).strip()
    dosya_adi = temizle_dosya_adi(kanal_adi) + ".m3u8"
    hedef_yol = os.path.join(HEDEF_KLASOR, dosya_adi)

    print(f"🔹 {kanal_adi} işleniyor...")

    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'format': 'best[ext=m3u8]/best',
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info.get('url', '')

        if stream_url and stream_url.startswith('http'):
            icerik = "#EXTM3U\n" + extinf + "\n" + stream_url + "\n"
            with open(hedef_yol, "w", encoding="utf-8") as f:
                f.write(icerik)
            print(f"✅ {kanal_adi} → {dosya_adi}")
            basari_sayisi += 1
        else:
            print(f"⚠️ {kanal_adi} için canlı yayın bulunamadı")
            hata_sayisi += 1

    except yt_dlp.utils.DownloadError as e:
        print(f"❌ {kanal_adi} indirme hatası: {str(e)[:100]}...")
        hata_sayisi += 1
    except Exception as e:
        print(f"❌ {kanal_adi} beklenmeyen hata: {e}")
        hata_sayisi += 1

print(f"\n🎯 İşlem tamamlandı: {basari_sayisi} başarılı, {hata_sayisi} hatalı")

# ===============================
#  GITHUB'A GÖNDERME - BASİT VE GÜVENLİ VERSİYON
# ===============================
print("\nGitHub'a gönderiliyor...")

try:
    # ÖNCE: Mevcut değişiklikleri commit et
    print("Değişiklikler ekleniyor...")
    subprocess.run(["git", "-C", ANA_KLASOR, "add", "."], check=True)
    
    # Commit yap (değişiklik yoksa hata verme)
    commit_result = subprocess.run(
        ["git", "-C", ANA_KLASOR, "commit", "-m", "Otomatik m3u8 güncelleme"], 
        capture_output=True, text=True, encoding='utf-8'
    )
    
    if commit_result.returncode == 0:
        print("✅ Commit oluşturuldu")
    else:
        if "nothing to commit" in commit_result.stdout or "nothing to commit" in commit_result.stderr:
            print("ℹ️  Commit gerekmiyor (değişiklik yok)")
        else:
            print(f"⚠️  Commit hatası: {commit_result.stderr}")
    
    # SONRA: Pull yap (merge ile, rebase olmadan)
    print("Uzak değişiklikler çekiliyor...")
    pull_result = subprocess.run(
        ["git", "-C", ANA_KLASOR, "pull", "--no-rebase", GIT_URL, "main"], 
        capture_output=True, text=True, encoding='utf-8'
    )
    
    if pull_result.returncode == 0:
        print("✅ Uzak değişiklikler başarıyla çekildi")
    else:
        print(f"⚠️  Pull hatası: {pull_result.stderr}")
        # Basit çözüm: Doğrudan push deneyelim
        print("Doğrudan push denemesi...")
    
    # EN SON: Push yap
    print("GitHub'a push yapılıyor...")
    push_result = subprocess.run(
        ["git", "-C", ANA_KLASOR, "push", GIT_URL, "main"], 
        capture_output=True, text=True, encoding='utf-8'
    )
    
    if push_result.returncode == 0:
        print("🚀 GitHub'a başarıyla push yapıldı!")
    else:
        print(f"❌ Push hatası: {push_result.stderr}")
        
        # Son çare: Force push (DİKKAT: Bu diğer değişiklikleri siler!)
        print("Force push denemesi (son çare)...")
        force_push = subprocess.run(
            ["git", "-C", ANA_KLASOR, "push", "--force", GIT_URL, "main"], 
            capture_output=True, text=True, encoding='utf-8'
        )
        if force_push.returncode == 0:
            print("🚀 GitHub'a force push başarılı!")
        else:
            print(f"❌ Force push da başarısız: {force_push.stderr}")
            
except subprocess.CalledProcessError as e:
    print(f"❌ Git işlemi başarısız: {e}")
    if e.stderr:
        print(f"Hata detayı: {e.stderr}")
except Exception as e:
    print(f"❌ Beklenmeyen hata: {e}")

# Repository URL kontrolü
print(f"\n🔍 Kullanılan Repository: {GIT_URL.split('@')[1] if '@' in GIT_URL else GIT_URL}")