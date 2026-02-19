// Cloudflare Worker - TV-2 (Otomatik oluşturuldu: 2026-02-19 23:26:46)
// GitHub Private Repo'dan M3U8 dosyalarını servis eder

const GITHUB_USER = 'SekoBes';
const GITHUB_REPO = 'S5';
const GITHUB_BRANCH = 'main';

async function handleRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname;
  
  // Ana playlist
  if (path === '/playlist.m3u' || path === '/playlist.m3u8') {
    return await servePlaylist();
  }
  
  // Tek kanal isteği
  if (path.endsWith('.m3u8')) {
    const fileName = path.substring(1);
    return await serveM3U8(fileName);
  }
  
  // Ana sayfa
  if (path === '/') {
    return new Response('TV-2 Proxy Çalışıyor - 55 Kanal', {
      headers: { 'Content-Type': 'text/plain' }
    });
  }
  
  return new Response('Bulunamadı', { status: 404 });
}

async function servePlaylist() {
  try {
    const githubUrl = `https://api.github.com/repos/${GITHUB_USER}/${GITHUB_REPO}/contents/TV?ref=${GITHUB_BRANCH}`;
    
    const response = await fetch(githubUrl, {
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'User-Agent': 'Cloudflare-Worker',
        'Accept': 'application/vnd.github.v3+json'
      }
    });
    
    if (!response.ok) {
      return new Response(`GitHub hatası: ${response.status}`, { status: 500 });
    }
    
    const files = await response.json();
    
    if (!Array.isArray(files) || files.length === 0) {
      return new Response('TV klasöründe dosya bulunamadı', { status: 404 });
    }
    
    let playlist = '#EXTM3U\n';
    playlist += '#EXTINF:-1,TV-2 Kanal Listesi\n\n';
    
    for (const file of files) {
      if (file.name && file.name.endsWith('.m3u8')) {
        const kanalAdi = file.name.replace('.m3u8', '').replace(/_/g, ' ');
        playlist += `#EXTINF:-1 tvg-id="${kanalAdi}" tvg-name="${kanalAdi}",${kanalAdi}\n`;
        playlist += `https://tv-2.sekobes.workers.dev/${file.name}\n\n`;
      }
    }
    
    return new Response(playlist, {
      headers: {
        'Content-Type': 'application/vnd.apple.mpegurl',
        'Cache-Control': 'no-cache',
        'Access-Control-Allow-Origin': '*'
      }
    });
    
  } catch (error) {
    return new Response(`Sunucu hatası: ${error.message}`, { status: 500 });
  }
}

async function serveM3U8(fileName) {
  try {
    if (!fileName.endsWith('.m3u8') || fileName.includes('..')) {
      return new Response('Geçersiz dosya adı', { status: 400 });
    }
    
    const githubUrl = `https://api.github.com/repos/${GITHUB_USER}/${GITHUB_REPO}/contents/TV/${fileName}?ref=${GITHUB_BRANCH}`;
    
    const response = await fetch(githubUrl, {
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'User-Agent': 'Cloudflare-Worker',
        'Accept': 'application/vnd.github.v3+json'
      }
    });
    
    if (!response.ok) {
      return new Response('Dosya bulunamadı', { status: 404 });
    }
    
    const data = await response.json();
    
    if (!data.content) {
      return new Response('Dosya içeriği boş', { status: 500 });
    }
    
    // Base64'ü çöz
    const content = atob(data.content.replace(/\n/g, ''));
    
    return new Response(content, {
      headers: {
        'Content-Type': 'application/vnd.apple.mpegurl',
        'Cache-Control': 'no-cache',
        'Access-Control-Allow-Origin': '*'
      }
    });
    
  } catch (error) {
    return new Response(`Dosya okuma hatası: ${error.message}`, { status: 500 });
  }
}

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});
