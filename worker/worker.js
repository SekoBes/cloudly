// Cloudflare Worker - TV-2 (Otomatik oluşturuldu: 2026-02-19 22:26:22)
const GITHUB_USER = 'SekoBes';
const GITHUB_REPO = 'S5';
const GITHUB_BRANCH = 'main';
const GITHUB_TOKEN = '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';

async function handleRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname;
  
  // Ana playlist
  if (path === '/playlist.m3u') {
    return await servePlaylist();
  }
  
  // Kanal bazlı yönlendirmeler
    if (path === '/A_HABER.m3u8') return await serveM3U8('A_HABER.m3u8');
    if (path === '/A_PARA.m3u8') return await serveM3U8('A_PARA.m3u8');
    if (path === '/CNN_TURK.m3u8') return await serveM3U8('CNN_TURK.m3u8');
    if (path === '/NTV.m3u8') return await serveM3U8('NTV.m3u8');
    if (path === '/A_NEWS.m3u8') return await serveM3U8('A_NEWS.m3u8');
    if (path === '/HABER_GLOBAL.m3u8') return await serveM3U8('HABER_GLOBAL.m3u8');
    if (path === '/24.m3u8') return await serveM3U8('24.m3u8');
    if (path === '/HABER_TURK.m3u8') return await serveM3U8('HABER_TURK.m3u8');
    if (path === '/TVNET.m3u8') return await serveM3U8('TVNET.m3u8');
    if (path === '/ULKE_TV.m3u8') return await serveM3U8('ULKE_TV.m3u8');
    if (path === '/EKOTURK.m3u8') return await serveM3U8('EKOTURK.m3u8');
    if (path === '/TGRT_HABER.m3u8') return await serveM3U8('TGRT_HABER.m3u8');
    if (path === '/TV100.m3u8') return await serveM3U8('TV100.m3u8');
    if (path === '/CNBC-E.m3u8') return await serveM3U8('CNBC-E.m3u8');
    if (path === '/BLOOMBERG_HT.m3u8') return await serveM3U8('BLOOMBERG_HT.m3u8');
    if (path === '/SHOW_MAX.m3u8') return await serveM3U8('SHOW_MAX.m3u8');
    if (path === '/7_NUMARA.m3u8') return await serveM3U8('7_NUMARA.m3u8');
    if (path === '/DIYANET_TV.m3u8') return await serveM3U8('DIYANET_TV.m3u8');
    if (path === '/SEMERKAND.m3u8') return await serveM3U8('SEMERKAND.m3u8');
    if (path === '/VAV_TV.m3u8') return await serveM3U8('VAV_TV.m3u8');
    if (path === '/AL_SUNNAH_AL_NABAWIYAH.m3u8') return await serveM3U8('AL_SUNNAH_AL_NABAWIYAH.m3u8');
    if (path === '/AL_QURAN_AL_KAREEM.m3u8') return await serveM3U8('AL_QURAN_AL_KAREEM.m3u8');
    if (path === '/DIYANET_COCUK.m3u8') return await serveM3U8('DIYANET_COCUK.m3u8');
    if (path === '/NILOYA.m3u8') return await serveM3U8('NILOYA.m3u8');
    if (path === '/KRAL_AKUSTIK_TV.m3u8') return await serveM3U8('KRAL_AKUSTIK_TV.m3u8');
    if (path === '/A_SPOR.m3u8') return await serveM3U8('A_SPOR.m3u8');
    if (path === '/HT_SPOR.m3u8') return await serveM3U8('HT_SPOR.m3u8');
    if (path === '/beIN_SPORTS_HABER.m3u8') return await serveM3U8('beIN_SPORTS_HABER.m3u8');
    if (path === '/SIFIR_TV.m3u8') return await serveM3U8('SIFIR_TV.m3u8');
    if (path === '/TGRT_BELGESEL.m3u8') return await serveM3U8('TGRT_BELGESEL.m3u8');
    if (path === '/BIZIMEV_TV.m3u8') return await serveM3U8('BIZIMEV_TV.m3u8');
    if (path === '/LIDER_HABER.m3u8') return await serveM3U8('LIDER_HABER.m3u8');
    if (path === '/BENGUTURK.m3u8') return await serveM3U8('BENGUTURK.m3u8');
    if (path === '/ULUSAL_KANAL.m3u8') return await serveM3U8('ULUSAL_KANAL.m3u8');
    if (path === '/FLASH_HABER.m3u8') return await serveM3U8('FLASH_HABER.m3u8');
    if (path === '/HALK_TV.m3u8') return await serveM3U8('HALK_TV.m3u8');
    if (path === '/KRAL_AKUSTIK_RADYO.m3u8') return await serveM3U8('KRAL_AKUSTIK_RADYO.m3u8');
    if (path === '/SOZCU_TV.m3u8') return await serveM3U8('SOZCU_TV.m3u8');
    if (path === '/ABC_NEWS.m3u8') return await serveM3U8('ABC_NEWS.m3u8');
    if (path === '/SLOW_TIME.m3u8') return await serveM3U8('SLOW_TIME.m3u8');
    if (path === '/DADA_RADYO.m3u8') return await serveM3U8('DADA_RADYO.m3u8');
    if (path === '/RADYO_7_AKUSTIK_TURKU.m3u8') return await serveM3U8('RADYO_7_AKUSTIK_TURKU.m3u8');
    if (path === '/RADYO_7_HIT_TURKULER.m3u8') return await serveM3U8('RADYO_7_HIT_TURKULER.m3u8');
    if (path === '/RADYO_DAMAR.m3u8') return await serveM3U8('RADYO_DAMAR.m3u8');
    if (path === '/AKUSTIK_TURKULER.m3u8') return await serveM3U8('AKUSTIK_TURKULER.m3u8');
    if (path === '/RADYO_DRAM.m3u8') return await serveM3U8('RADYO_DRAM.m3u8');
    if (path === '/PLATONIK_FM.m3u8') return await serveM3U8('PLATONIK_FM.m3u8');
    if (path === '/RELAXING_I.m3u8') return await serveM3U8('RELAXING_I.m3u8');
    if (path === '/RELAXING_II.m3u8') return await serveM3U8('RELAXING_II.m3u8');
    if (path === '/DERT_FM.m3u8') return await serveM3U8('DERT_FM.m3u8');
    if (path === '/PLATONIK_FM.m3u8') return await serveM3U8('PLATONIK_FM.m3u8');
    if (path === '/SOMINE_I.m3u8') return await serveM3U8('SOMINE_I.m3u8');
    if (path === '/SOMINE_II.m3u8') return await serveM3U8('SOMINE_II.m3u8');
    if (path === '/SOMINE_IIII.m3u8') return await serveM3U8('SOMINE_IIII.m3u8');
    if (path === '/SOMINE_III.m3u8') return await serveM3U8('SOMINE_III.m3u8');
  
  return new Response('TV-2 Proxy - Bulunamadı', { status: 404 });
}

async function servePlaylist() {
  try {
    const githubUrl = `https://api.github.com/repos/${GITHUB_USER}/${GITHUB_REPO}/contents/TV?ref=${GITHUB_BRANCH}`;
    
    const response = await fetch(githubUrl, {
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'User-Agent': 'Cloudflare-Worker'
      }
    });
    
    if (!response.ok) {
      return new Response('GitHub hatası', { status: 500 });
    }
    
    const files = await response.json();
    let playlist = '#EXTM3U\n#EXTINF:-1,TV-2 Kanal Listesi\n';
    
    for (const file of files) {
      if (file.name.endsWith('.m3u8')) {
        const kanalAdi = file.name.replace('.m3u8', '').replace(/_/g, ' ');
        playlist += `#EXTINF:-1 tvg-id="${kanalAdi}" tvg-name="${kanalAdi}",${kanalAdi}\n`;
        playlist += `https://tv-2.sekobes.workers.dev/${file.name}\n`;
      }
    }
    
    return new Response(playlist, {
      headers: {
        'content-type': 'application/vnd.apple.mpegurl',
        'Cache-Control': 'no-cache',
        'Access-Control-Allow-Origin': '*'
      }
    });
    
  } catch (error) {
    return new Response(`Hata: ${error.message}`, { status: 500 });
  }
}

async function serveM3U8(fileName) {
  try {
    const githubUrl = `https://api.github.com/repos/${GITHUB_USER}/${GITHUB_REPO}/contents/TV/${fileName}?ref=${GITHUB_BRANCH}`;
    
    const response = await fetch(githubUrl, {
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'User-Agent': 'Cloudflare-Worker'
      }
    });
    
    if (!response.ok) {
      return new Response('Dosya bulunamadı', { status: 404 });
    }
    
    const data = await response.json();
    const content = atob(data.content);
    
    return new Response(content, {
      headers: {
        'content-type': 'application/vnd.apple.mpegurl',
        'Cache-Control': 'no-cache',
        'Access-Control-Allow-Origin': '*'
      }
    });
    
  } catch (error) {
    return new Response(`Hata: ${error.message}`, { status: 500 });
  }
}

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});
