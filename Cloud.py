#!/usr/bin/python3
import os
import json
import requests
import subprocess
import sys
import time
import re
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==================== AYARLAR ====================
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_PATH, "config.json")
TV_ORDER_FILE = os.path.join(BASE_PATH, "Dizin.txt")
YOUTUBE_FILE = os.path.join(BASE_PATH, "YouTube.txt")
IPTV_FILE = os.path.join(BASE_PATH, "TV.txt")
OUTPUT_FILE = os.path.join(BASE_PATH, "TV.m3u")
FALLBACK_URL = "http://radyodejavu.80.yayin.com.tr/stream/1/"

print("📺 IPTV PLAYLİST OLUŞTURMA")

# ==================== CONFIG KONTROLÜ ====================
if not os.path.exists(CONFIG_FILE):
    print(f"❌ Config dosyası bulunamadı: {CONFIG_FILE}")
    sys.exit(1)

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)

# ==================== DOSYA OKUMA ====================
def read_channels_file(file_path, is_youtube=False):
    channels = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                i = 0
                while i < len(lines):
                    if lines[i].startswith('#EXTINF:'):
                        extinf_line = lines[i]
                        if i + 1 < len(lines) and not lines[i + 1].startswith('#'):
                            url = lines[i + 1].strip()
                            name_parts = extinf_line.split(',', 1)
                            if len(name_parts) > 1:
                                name = name_parts[1].strip()
                                if name not in channels:
                                    channels[name] = []
                                channels[name].append((extinf_line, url, is_youtube))
                    i += 1
            
            # Sayım ve Raporlama (Mükerrer isimleri de tek tek sayar)
            total_url_count = sum(len(v) for v in channels.values())
            print(f"📖 {os.path.basename(file_path)}: {total_url_count} Kanal Okundu")
            
        except Exception as e:
            print(f"❌ {file_path} okuma hatası: {e}")
    else:
        print(f"⚠️ Dosya bulunamadı: {file_path}")
    
    return channels

def read_order_file(file_path):
    order = []
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                order = [line.strip() for line in f if line.strip()]
            print(f"📋 Dizin.txt: {len(order)} Kanal Sırası Okundu")
        except Exception as e:
            print(f"❌ Dizin.txt okuma hatası: {e}")
    else:
        print(f"⚠️  Dizin.txt bulunamadı")
    return order

# ==================== YOUTUBE STREAM ALMA ====================
def get_youtube_stream(url, max_retries=2):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(1)
                print(f"   ↻ Yeniden deneme {attempt}/{max_retries}")

            cmd = [
                'python', '-m', 'yt-dlp',
                '--quiet',
                '--no-warnings',
                '--user-agent', user_agent,
                '--format', 'best[height<=1080]',
                '--get-url',
                '--no-playlist',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                stream_url = result.stdout.strip()
                
                cmd_info = [
                    'python', '-m', 'yt-dlp',
                    '--quiet',
                    '--no-warnings',
                    '--user-agent', user_agent,
                    '--print', '%(height)s',
                    '--no-playlist',
                    url
                ]
                
                result_info = subprocess.run(cmd_info, capture_output=True, text=True, check=True)
                height = result_info.stdout.strip()
                
                return stream_url, f"{height}p" if height.isdigit() else "OK"
                
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else "Bilinmeyen hata"
            print(f"   ↻ yt-dlp hatası: {error_msg[:80]}")
            continue
        except Exception as e:
            print(f"   ↻ Genel hata: {str(e)[:50]}")
            continue
    
    return None, None

def process_youtube_channels(youtube_channels_dict):
    youtube_results = {}
    tasks = []
    for name, entries in youtube_channels_dict.items():
        for extinf_line, url, is_youtube in entries:
            if is_youtube:
                tasks.append({
                    'name': name,
                    'url': url,
                    'extinf': extinf_line
                })

    total_youtube = len(tasks)
    processed = 0
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_channel = {
            executor.submit(get_youtube_stream, task['url']): task 
            for task in tasks
        }

        for future in as_completed(future_to_channel):
            task = future_to_channel[future]
            processed += 1
            name = task['name']
            
            try:
                stream_url, res = future.result()
                if stream_url:
                    if name not in youtube_results:
                        youtube_results[name] = []

                    youtube_results[name].append((task['extinf'], stream_url, True))
                    
                    print(f"   [{processed}/{total_youtube}] ✅ {name}...")
                    print(f"   ✅ {res if res else 'OK'} stream alındı!")
                else:
                    print(f"   [{processed}/{total_youtube}] ❌ {name}... Başarısız")
            except Exception as e:
                print(f"   [{processed}/{total_youtube}] ⚠️ {name} Hata!")

    actual_count = sum(len(v) for v in youtube_results.values())
    print(f"\n✅ YouTube İşlemi Tamamlandı: {actual_count} Kanal Alındı.")
    return youtube_results

# ==================== SABİT LİNKLER İÇİN FONKSİYONLAR ====================
def clean_filename(name):
    """Kanal adını dosya adına çevir"""
    tr_to_en = {
        'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G',
        'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S',
        'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'
    }
    
    for tr, en in tr_to_en.items():
        name = name.replace(tr, en)
    
    name = re.sub(r'[^\w]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    name = name.upper()
    
    return name

def create_all_static_links(tv_order, iptv_channels, youtube_processed):
    """Sabit linkleri Dizin.txt sırasına göre hazırlar"""
    
    all_links = {}
    
    # Sıralama için Dizin.txt'yi baz alıyoruz
    for name in tv_order:
        # IPTV kanalları
        if name in iptv_channels and iptv_channels[name]:
            extinf_line, url, _ = iptv_channels[name][0]
            filename = f"{clean_filename(name)}.m3u8"
            
            if filename not in all_links:
                all_links[filename] = {
                    'name': name,
                    'extinf': extinf_line,
                    'stream_url': url,
                    'type': 'iptv',
                    'filename': filename
                }
        
        # YouTube kanalları
        if name in youtube_processed and youtube_processed[name]:
            extinf_line, stream_url, _ = youtube_processed[name][0]
            
            base_filename = clean_filename(name)
            filename = f"{base_filename}_YT.m3u8"
            
            tv_filename = f"{base_filename}.m3u8"
            if tv_filename not in all_links:
                filename = f"{base_filename}.m3u8"
            
            if filename not in all_links:
                all_links[filename] = {
                    'name': f"{name} (YouTube)",
                    'extinf': extinf_line,
                    'stream_url': stream_url,
                    'type': 'youtube',
                    'filename': filename
                }
    
    return all_links

# ==================== PLAYLIST OLUŞTURMA ====================
def create_playlist(tv_order, iptv_channels, youtube_processed):
    # 1. ADIM: Tüm kanalları bir 'havuz' listesinde topla (Sözlük değil, Liste!)
    # Böylece aynı isimli kanallar asla birbirini silmez.
    pool = []
    
    # IPTV kanallarını havuza ekle
    for name, entries in iptv_channels.items():
        for entry in entries:
            pool.append({'name': name, 'data': entry, 'is_youtube': False})
            
    # YouTube kanallarını havuza ekle
    for name, entries in youtube_processed.items():
        for entry in entries:
            pool.append({'name': name, 'data': entry, 'is_youtube': True})

    playlist = ["#EXTM3U refresh=\"1\""]
    iptv_count = 0
    youtube_count = 0
    fallback_count = 0
    fallback_channels = []

    # 2. ADIM: Dizin.txt sırasına göre havuzdan kanal çek
    for channel_name in tv_order:
        found = False
        # Havuzda bu isme uygun İLK kanalı bul
        for i, item in enumerate(pool):
            if item['name'] == channel_name:
                extinf_line, url, _ = item['data']
                playlist.extend([extinf_line, url])
                
                if item['is_youtube']:
                    youtube_count += 1
                else:
                    iptv_count += 1
                
                # ÖNEMLİ: Bulunan kanalı havuzdan sil ki bir sonraki 
                # aynı isimli Dizin satırı, havuzdaki diğer URL'yi alabilsin!
                pool.pop(i)
                found = True
                break
        
        # Eğer havuzda kalmadıysa fallback ver
        if not found:
            fallback_extinf = f'#EXTINF:-1 tvg-name="{channel_name}.tr" ,{channel_name}'
            playlist.extend([fallback_extinf, FALLBACK_URL])
            fallback_count += 1
            fallback_channels.append(channel_name)

    # 3. ADIM: Dosyaya yaz ve raporla
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(playlist))
        
    total_channels = (len(playlist) - 1) // 2
    
    print(f"\n📊 PLAYLIST İSTATİSTİKLERİ:")
    print(f"   📡 IPTV Kanalları: {iptv_count}")
    print(f"   🎥 YouTube Kanalları: {youtube_count}")
    print(f"   📺 Toplam Kanal: {total_channels}") 
    print(f"   ❌ Fallback Kanal: {fallback_count}")

    return {
        'playlist_content': "\n".join(playlist),
        'iptv_count': iptv_count,
        'youtube_count': youtube_count,
        'total_channels': total_channels,
        'fallback_count': fallback_count,
        'fallback_channels': fallback_channels
    }

def upload_to_cloudflare_with_links(playlist_content, stats, all_links):
    """Playlist'i Cloudflare Worker'a yükle - Orijinal Panel Koduyla!"""
    
    cf_config = config['cloudflare']
    account_id = cf_config['account_id']
    worker_name = cf_config['worker_name']
    worker_url = cf_config['worker_url']
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{worker_name}"
    
    headers = {
        'Authorization': f'Bearer {cf_config["api_token"]}',
        'Content-Type': 'application/javascript'
    }

    all_links_js = "const ALL_CHANNEL_LINKS = new Map([\n"
    for filename, data in all_links.items():
        safe_extinf = data['extinf'].replace('`', '\\`').replace('${', '\\${')
        safe_name = data['name'].replace("'", "\\'").replace('"', '\\"')
        all_links_js += f"  ['{filename}', {{name: '{safe_name}', type: '{data['type']}', extinf: `{safe_extinf}`, stream: `{data['stream_url']}`}}],\n"
    all_links_js += "]);"

    # HTML İçeriği (Gönderdiğin Orijinal Hali - Dokunulmadı)
    html_template = '''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📺 IPTV API PANEL - SEKOBES</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #f0f0f0;
            line-height: 1.6;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        header {
            text-align: center; margin-bottom: 30px; padding: 30px;
            background: rgba(255, 255, 255, 0.05); border-radius: 15px;
            backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1);
        }
        h1 { color: #fff; font-size: 2.2rem; display: flex; align-items: center; justify-content: center; gap: 15px; }
        .grid-layout { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 30px; }
        
        .static-links-info {
            grid-column: 1 / -1;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            border: 1px dashed rgba(76, 201, 240, 0.5);
        }
        .static-links-info a { color: #4cc9f0; text-decoration: none; font-weight: bold; }

        .card {
            background: rgba(255, 255, 255, 0.05); border-radius: 15px; padding: 25px;
            backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex; flex-direction: column; justify-content: space-between;
        }
        .card.blue { border-top: 5px solid #4cc9f0; }
        .card.pink { border-top: 5px solid #f72585; }
        .card.indigo { border-top: 5px solid #4361ee; }
        .card.green { border-top: 5px solid #4ade80; }
        .card.purple { border-top: 5px solid #9d4edd; }
        .card.orange { border-top: 5px solid #f8961e; }
        .card:hover { transform: translateY(-8px); background: rgba(255, 255, 255, 0.08); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4); }
        .stat-header { display: flex; align-items: center; gap: 15px; margin-bottom: 10px; }
        .stat-value { font-size: 2rem; font-weight: bold; color: #fff; }
        .stat-label { color: #a0a0c0; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px; }
        .url-title { font-size: 1.1rem; font-weight: bold; margin-bottom: 12px; }
        .url-code {
            background: rgba(0, 0, 0, 0.3); padding: 12px; border-radius: 8px; font-family: monospace;
            font-size: 0.85rem; word-break: break-all; margin-bottom: 15px; color: #a0e0ff; border-left: 3px solid rgba(255,255,255,0.2);
        }
        .btn-group { display: flex; gap: 10px; }
        .btn {
            flex: 1; padding: 12px; border-radius: 8px; text-decoration: none; text-align: center;
            font-weight: 600; cursor: pointer; border: none; display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 0.9rem; transition: 0.2s;
        }
        .btn-copy { background: rgba(255, 255, 255, 0.1); color: #fff; border: 1px solid rgba(255,255,255,0.2); }
        .btn-download { background: #f8961e; color: #000; }
        .btn-purple { background: #9d4edd; color: #fff; }
        .system-footer { grid-column: 1 / -1; display: flex; flex-direction: row; justify-content: space-around; padding: 20px; text-align: center; }
        @media (max-width: 768px) { .grid-layout { grid-template-columns: 1fr; } .system-footer { flex-direction: column; gap: 15px; } }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1><span class="logo">📺</span> IPTV API PANEL <span class="logo">⚡</span></h1>
            <p style="color: #a0a0c0; font-size: 0.9rem; margin-top: 5px;">SEKOBES Bulut Yönetim Paneli</p>
        </header>
        <div class="grid-layout">
            <div class="static-links-info">
                <p>
                    📝 <strong>Not:</strong> {{STATIC_COUNT}} adet sabit link mevcut. 
                    Tüm listeyi görmek için <a href="/tv">/tv</a> 
                    ve <a href="/youtube">/youtube</a> sayfalarını ziyaret edin.
                </p>
            </div>

            <div class="card blue">
                <div class="stat-header">
                    <span style="font-size: 2.2rem;">📡</span>
                    <div><div class="stat-value">{{IPTV_COUNT}}</div><div class="stat-label">TV Kanalları</div></div>
                </div>
                <p style="font-size: 0.85rem; color: #888;">TV Kanallarına ait IPTV linklerini içermektedir.</p>
            </div>
            <div class="card pink">
                <div class="stat-header">
                    <span style="font-size: 2.2rem;">🎥</span>
                    <div><div class="stat-value">{{YOUTUBE_COUNT}}</div><div class="stat-label">YouTube Kanalları</div></div>
                </div>
                <p style="font-size: 0.85rem; color: #888;">YouTube üzerinden canlı yayın yapan kanalların linklerini içermektedir.</p>
            </div>
            
            <div class="card indigo">
                <div class="url-title">🔗 Normal Playlist</div>
                <div class="url-code" id="url1">{{WORKER_URL}}/playlist.m3u</div>
                <div class="btn-group">
                    <button class="btn btn-copy" onclick="copy('url1')">📋 Kopyala</button>
                    <a href="{{WORKER_URL}}/playlist.m3u" download="sekobes_playlist.m3u" class="btn btn-download">📥 İndir</a>
                </div>
            </div>

            <div class="card purple">
                <div class="url-title">🔄 Sabit Linkli Playlist (Yeni)</div>
                <div class="url-code" id="urlStatic">{{WORKER_URL}}/sabit.m3u</div>
                <div class="btn-group">
                    <button class="btn btn-copy" onclick="copy('urlStatic')">📋 Kopyala</button>
                    <a href="{{WORKER_URL}}/sabit.m3u" download="sabit.m3u" class="btn btn-download">📥 İndir</a>
                </div>
            </div>

            <div class="card green">
                <div class="url-title">🔄 Yedek Playlist</div>
                <div class="url-code" id="url2">https://sekobes.pythonanywhere.com/files/SEKO5-2.m3u</div>
                <div class="btn-group">
                    <button class="btn btn-copy" onclick="copy('url2')">📋 Kopyala</button>
                    <a href="https://sekobes.pythonanywhere.com/files/SEKO5-2.m3u" download="sekobes_fresh.m3u" class="btn btn-download">📥 İndir</a>
                </div>
            </div>

            <div class="card orange system-footer">
                <div><strong style="display:block; color:#f8961e; font-size:0.7rem;">SİSTEM DURUMU</strong><span style="color: #4ade80;">● Aktif</span></div>
                <div><strong style="display:block; color:#f8961e; font-size:0.7rem;">ALTYAPI</strong><span>Cloudflare Edge</span></div>
                <div><strong style="display:block; color:#f8961e; font-size:0.7rem;">GÜNCEL SAAT</strong><span id="currentTime">00:00:00</span></div>
            </div>
        </div>
        <footer style="text-align: center; color: #444; font-size: 0.75rem; padding-bottom: 20px;">
            © 2026 SEKOBES IPTV | Panel v2.9.0
        </footer>
    </div>
    <script>
        function copy(id) {
            const text = document.getElementById(id).innerText;
            navigator.clipboard.writeText(text).then(() => {
                const el = document.getElementById(id);
                const original = el.innerText;
                el.innerText = "✅ Link Kopyalandı!";
                setTimeout(() => { el.innerText = original; }, 1500);
            });
        }
        function updateClock() { document.getElementById('currentTime').innerText = new Date().toLocaleTimeString('tr-TR'); }
        setInterval(updateClock, 1000); updateClock();
    </script>
</body>
</html>'''

    html_content = html_template.replace('{{IPTV_COUNT}}', str(stats['iptv_count']))
    html_content = html_content.replace('{{YOUTUBE_COUNT}}', str(stats['youtube_count']))
    html_content = html_content.replace('{{STATIC_COUNT}}', str(len(all_links)))
    html_content = html_content.replace('{{WORKER_URL}}', worker_url)

    safe_html = html_content.replace('`', '\\`').replace('${', '\\${')
    
    # Worker JavaScript Kodu - Dizin.txt Sırasıyla Oluşturulur
    new_worker_code = f'''
addEventListener('fetch', event => {{
  event.respondWith(handleRequest(event.request))
}})

const PLAYLIST_CONTENT = `{playlist_content}`;
{all_links_js}

const ncHeaders = {{
  'Access-Control-Allow-Origin': '*',
  'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
  'Pragma': 'no-cache',
  'Expires': '0',
  'Surrogate-Control': 'no-store'
}};

const STATIC_PLAYLIST = (() => {{
  let lines = ['#EXTM3U refresh="1"'];
  for (const [filename, d] of ALL_CHANNEL_LINKS) {{
    lines.push(d.extinf);
    const proxyPath = d.type === 'iptv' ? '/tv/' : '/youtube/';
    lines.push(`{worker_url}${{proxyPath}}${{filename}}`);
  }}
  return lines.join('\\n');
}})();

async function handleRequest(request) {{
  const url = new URL(request.url);

  if (url.pathname === '/sabit.m3u') {{
    return new Response(STATIC_PLAYLIST, {{
      headers: {{ ...ncHeaders, 'Content-Type': 'audio/x-mpegurl' }}
    }});
  }}

  if (url.pathname === '/playlist.m3u') {{
    return new Response(PLAYLIST_CONTENT, {{
      headers: {{ ...ncHeaders, 'Content-Type': 'audio/x-mpegurl' }}
    }});
  }}

  if (url.pathname === '/' || url.pathname === '/index.html') {{
    return new Response(`{safe_html}`, {{
      headers: {{ 'Content-Type': 'text/html; charset=utf-8' }}
    }});
  }}

  if (url.pathname === '/tv' || url.pathname === '/tv/') {{
    let html = `<!DOCTYPE html><html><head><meta charset="UTF-8">
    <title>📺 TV Kanalları</title>
    <style>
      body{{font-family:Arial;margin:20px;background:#1a1a2e;color:white}}
      .channel{{padding:15px;margin:10px 0;background:rgba(255,255,255,0.05);border-radius:8px}}
      a{{color:white;text-decoration:none;font-weight:bold}}
    </style></head><body>
    <h1>📺 TV Kanalları</h1><a href="/">← Ana Sayfaya Dön</a>`;
    for (const [filename, d] of ALL_CHANNEL_LINKS) {{
      if (d.type === 'iptv')
        html += `<div class="channel"><a href="/tv/${{filename}}">📺 ${{d.name}}</a></div>`;
    }}
    html += '</body></html>';
    return new Response(html, {{ headers: {{ 'Content-Type': 'text/html; charset=utf-8' }} }});
  }}

  if (url.pathname === '/youtube' || url.pathname === '/youtube/') {{
    let html = `<!DOCTYPE html><html><head><meta charset="UTF-8">
    <title>🎥 YouTube Kanalları</title>
    <style>
      body{{font-family:Arial;margin:20px;background:#1a1a2e;color:white}}
      .channel{{padding:15px;margin:10px 0;background:rgba(255,255,255,0.05);border-radius:8px}}
      a{{color:white;text-decoration:none;font-weight:bold}}
    </style></head><body>
    <h1>🎥 YouTube Kanalları</h1><a href="/">← Ana Sayfaya Dön</a>`;
    for (const [filename, d] of ALL_CHANNEL_LINKS) {{
      if (d.type === 'youtube')
        html += `<div class="channel"><a href="/youtube/${{filename}}">🎥 ${{d.name}}</a></div>`;
    }}
    html += '</body></html>';
    return new Response(html, {{ headers: {{ 'Content-Type': 'text/html; charset=utf-8' }} }});
  }}

  const p = url.pathname.split('/');
  if ((p[1] === 'tv' || p[1] === 'youtube') && p[2]) {{
    const d = ALL_CHANNEL_LINKS.get(p[2]);
    if (d) return Response.redirect(d.stream, 302);
  }}

  return new Response("Not Found", {{ status: 404 }});
}}
'''
    try:
        r = requests.put(
            url,
            headers=headers,
            data=new_worker_code.encode('utf-8'),
            timeout=20
        )
        return r.status_code == 200
    except:
        return False

# ==================== PYTHONANYWHERE UPLOAD ====================
def upload_to_pythonanywhere():
    """PythonAnywhere'e yedek yükle"""
    if not os.path.exists(OUTPUT_FILE):
        return False
    try:
        pa_config = config['pythonanywhere']
        with open(OUTPUT_FILE, 'rb') as f:
            response = requests.post(
                pa_config['upload_url'],
                files={"file": ("SEKO5.m3u", f, "application/octet-stream")},
                headers={"Authorization": f"Bearer {pa_config['token']}"},
                timeout=10
            )
        return response.status_code == 200
    except:
        return False

# ==================== ANA İŞLEM ====================
def main_process():
    print("=" * 50)
    print("🚀 İşlemler Başlatıldı.")
    print("=" * 50)
    
    # 1. Dosyaları oku
    print("📁 Dosyalar okunuyor...")
    print("-" * 50)
    
    iptv_channels = read_channels_file(IPTV_FILE, is_youtube=False)
    youtube_channels = read_channels_file(YOUTUBE_FILE, is_youtube=True)
    tv_order = read_order_file(TV_ORDER_FILE)

    actual_iptv_count = sum(len(v) for v in iptv_channels.values())
    actual_yt_count = sum(len(v) for v in youtube_channels.values())
    total_url_sum = actual_iptv_count + actual_yt_count
    
    print(f"📊 TOPLAM: {total_url_sum} Kanal ({actual_iptv_count} IPTV + {actual_yt_count} YouTube)")
 
    # 2. YouTube stream'leri al
    print("=" * 50)
    print("🔄 YouTube Stream URL'leri Alınıyor...")
    print("-" * 50)
  
    youtube_processed = process_youtube_channels(youtube_channels)

    playlist_result = create_playlist(tv_order, iptv_channels, youtube_processed)
    all_links = create_all_static_links(tv_order, iptv_channels, youtube_processed)
    
    stats = {
        'total_channels': playlist_result['total_channels'],
        'iptv_count': playlist_result['iptv_count'],
        'youtube_count': playlist_result['youtube_count'],
        'fallback_count': playlist_result['fallback_count']
    }
    
    cloudflare_success = upload_to_cloudflare_with_links(
        playlist_result['playlist_content'], 
        stats,
        all_links
    )
    
    pythonanywhere_success = upload_to_pythonanywhere()
    
    print("\n" + "=" * 50)
    print("🎉 İŞLEM TAMAMLANDI - SONUÇ RAPORU")
    print("=" * 50)
    print(f"✅ Cloudflare: {'BAŞARILI' if cloudflare_success else 'BAŞARISIZ'}")
    print(f"✅ PythonAnywhere: {'BAŞARILI' if pythonanywhere_success else 'BAŞARISIZ'}")
    print("=" * 50)

# ============================================
# 6. ÇALIŞTIR
# ============================================
if __name__ == "__main__":
    try:
        # GitHub'da döngüye gerek yok, Actions bunu 4 saatte bir tetikleyecek.
        main_process()
    except Exception as e:
        print(f"\n\n❌ Hata oluştu: {e}")
