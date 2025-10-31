import os
import yt_dlp
import re
import subprocess

# ===============================
#  AYARLAR
# ===============================
ANA_KLASOR = r"C:\Users\KEMAL\Desktop\Youtube"
KAYNAK_DOSYA = os.path.join(ANA_KLASOR, "YouTube Kanalları.txt")
HEDEF_KLASOR = os.path.join(ANA_KLASOR, "YouTube")

# GitHub bilgileri
GITHUB_USER = "KULLANICI_ADIN"  # 👈 kendi GitHub kullanıcı adını yaz
GITHUB_REPO = "youtube-m3u8"    # 👈 depo adın
GITHUB_TOKEN = "GITHUB_TOKENIN" # 👈 access token (şifre yerine)
GIT_URL = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{GITHUB_REPO}.git"

# ===============================
#  M3U8 OLUŞTURMA
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
            kanallar.append((extinf, url))
        except IndexError:
            pass

for extinf, url in kanallar:
    match = re.search(r',([^,]+)$', extinf)
    if not match:
        continue
    kanal_adi = match.group(1).strip()
    dosya_adi = re.sub(r'[^A-Za-z0-9]+', '_', kanal_adi) + ".m3u8"
    hedef_yol = os.path.join(HEDEF_KLASOR, dosya_adi)

    print(f"🔹 {kanal_adi} işleniyor...")

    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'format': 'best[ext=m3u8]/best',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info.get('url', '')

        if stream_url:
            icerik = "#EXTM3U\n" + extinf + "\n" + stream_url + "\n"
            with open(hedef_yol, "w", encoding="utf-8") as f:
                f.write(icerik)
            print(f"✅ {kanal_adi} → {dosya_adi}")
        else:
            print(f"⚠️ {kanal_adi} için yayın bulunamadı")

    except Exception as e:
        print(f"❌ {kanal_adi} hatası: {e}")

print("\n🎯 Tüm kanallar işlendi. Şimdi GitHub'a gönderiliyor...")

# ===============================
#  GITHUB'A GÖNDERME (PUSH)
# ===============================
try:
    subprocess.run(["git", "-C", ANA_KLASOR, "add", "."], check=True)
    subprocess.run(["git", "-C", ANA_KLASOR, "commit", "-m", "Otomatik m3u8 güncelleme"], check=True)
    subprocess.run(["git", "-C", ANA_KLASOR, "push", "-u", GIT_URL, "main"], check=True)
    print("🚀 GitHub güncellemesi başarıyla gönderildi!")
except Exception as e:
    print(f"❌ GitHub'a gönderme başarısız: {e}")