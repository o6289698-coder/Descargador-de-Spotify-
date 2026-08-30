import os
import re
import zipfile
import io
import random
import time
import json
import threading
from datetime import datetime, timedelta
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import requests

app = Flask(__name__)
CORS(app)

# Configuración de Spotify
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')

client_credentials_manager = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# ============== SISTEMA DE PROXIES ==============

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.failed_proxies = set()
        self.current_index = 0
        self.lock = threading.Lock()
        self.last_refresh = datetime.now()
        self.load_proxies()
    
    def load_proxies(self):
        """Carga proxies desde múltiples fuentes"""
        self.proxies = []
        
        # 1. Proxies desde variable de entorno (recomendado para producción)
        env_proxies = os.environ.get('PROXY_LIST', '')
        if env_proxies:
            self.proxies.extend([p.strip() for p in env_proxies.split(',') if p.strip()])
        
        # 2. Proxies pagados (BrightData, Oxylabs, etc.)
        self._load_paid_proxies()
        
        # 3. Proxies gratuitos (backup, menos confiables)
        if len(self.proxies) < 3:
            self._fetch_free_proxies()
        
        print(f"[ProxyManager] Cargados {len(self.proxies)} proxies")
        self.last_refresh = datetime.now()
    
    def _load_paid_proxies(self):
        """Configuración para proxies residenciales pagados"""
        # BrightData (Luminati)
        brightdata_user = os.environ.get('BRIGHTDATA_USER', '')
        brightdata_pass = os.environ.get('BRIGHTDATA_PASS', '')
        brightdata_port = os.environ.get('BRIGHTDATA_PORT', '22225')
        
        if brightdata_user and brightdata_pass:
            for i in range(10):
                session_id = f"session_{random.randint(100000, 999999)}"
                proxy = f"http://{brightdata_user}-session-{session_id}:{brightdata_pass}@brd.superproxy.io:{brightdata_port}"
                self.proxies.append(proxy)
        
        # Oxylabs
        oxylabs_user = os.environ.get('OXYLABS_USER', '')
        oxylabs_pass = os.environ.get('OXYLABS_PASS', '')
        
        if oxylabs_user and oxylabs_pass:
            for i in range(10):
                proxy = f"http://{oxylabs_user}:{oxylabs_pass}@pr.oxylabs.io:7777"
                self.proxies.append(proxy)
        
        # Smartproxy
        smartproxy_user = os.environ.get('SMARTPROXY_USER', '')
        smartproxy_pass = os.environ.get('SMARTPROXY_PASS', '')
        smartproxy_port = os.environ.get('SMARTPROXY_PORT', '10000')
        
        if smartproxy_user and smartproxy_pass:
            for i in range(10):
                session_id = random.randint(1000000, 9999999)
                proxy = f"http://{smartproxy_user}:{smartproxy_pass}@gate.smartproxy.com:{smartproxy_port}"
                self.proxies.append(proxy)
    
    def _fetch_free_proxies(self):
        """Obtiene proxies gratuitos de APIs públicas (menos confiables)"""
        try:
            urls = [
                'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&simplified=true',
                'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
                'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
            ]
            
            for url in urls:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        lines = response.text.strip().split('\n')
                        for line in lines[:20]:
                            line = line.strip()
                            if ':' in line and line not in self.proxies:
                                self.proxies.append(f"http://{line}")
                except:
                    continue
                    
        except Exception as e:
            print(f"[ProxyManager] Error fetching free proxies: {e}")
    
    def get_proxy(self):
        """Obtiene el siguiente proxy disponible"""
        with self.lock:
            if datetime.now() - self.last_refresh > timedelta(minutes=30):
                self.load_proxies()
            
            available = [p for p in self.proxies if p not in self.failed_proxies]
            
            if not available:
                self.failed_proxies.clear()
                available = self.proxies
            
            if not available:
                return None
            
            proxy = available[self.current_index % len(available)]
            self.current_index += 1
            return proxy
    
    def mark_failed(self, proxy):
        """Marca un proxy como fallido"""
        with self.lock:
            self.failed_proxies.add(proxy)
            print(f"[ProxyManager] Proxy marcado como fallido: {proxy[:50]}...")
    
    def get_yt_dlp_proxy(self):
        """Obtiene proxy formateado para yt-dlp"""
        proxy_url = self.get_proxy()
        if not proxy_url:
            return None
        return proxy_url

# Instancia global del gestor de proxies
proxy_manager = ProxyManager()

# ============== CONFIGURACIÓN ANTI-DETECCIÓN ==============

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def get_yt_dlp_opts(use_proxy=True):
    """Configuración anti-detección avanzada para yt-dlp"""
    opts = {
        'quiet': True,
        'no_warnings': True,
        'user_agent': get_random_user_agent(),
        'headers': {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['web'],
                'player_skip': ['webpage', 'configs'],
                'max_comments': [0],
            }
        },
        'socket_timeout': 30,
        'retries': 10,
        'fragment_retries': 10,
        'file_access_retries': 10,
        'extractor_retries': 10,
        'skip_unavailable_fragments': True,
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'prefer_insecure': False,
        'cookiesfrombrowser': None,
    }
    
    if use_proxy:
        proxy = proxy_manager.get_yt_dlp_proxy()
        if proxy:
            opts['proxy'] = proxy
            print(f"[yt-dlp] Usando proxy: {proxy[:50]}...")
    
    return opts

# ============== RUTAS DE LA APP ==============

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/proxy-status')
def proxy_status():
    """Endpoint para ver estado de proxies"""
    return jsonify({
        'total_proxies': len(proxy_manager.proxies),
        'failed_proxies': len(proxy_manager.failed_proxies),
        'available': len(proxy_manager.proxies) - len(proxy_manager.failed_proxies),
        'last_refresh': proxy_manager.last_refresh.isoformat()
    })

@app.route('/api/extract-playlist', methods=['POST'])
def extract_playlist():
    data = request.json
    playlist_url = data.get('url')
    
    if not playlist_url:
        return jsonify({'error': 'URL requerida'}), 400
    
    try:
        playlist_id = extract_playlist_id(playlist_url)
        if not playlist_id:
            return jsonify({'error': 'URL de playlist inválida'}), 400
        
        playlist = sp.playlist(playlist_id)
        tracks = []
        
        results = sp.playlist_tracks(playlist_id)
        tracks.extend(results['items'])
        
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
        
        songs = []
        for item in tracks:
            track = item['track']
            if track:
                song = {
                    'id': track['id'],
                    'name': track['name'],
                    'artist': ', '.join([artist['name'] for artist in track['artists']]),
                    'album': track['album']['name'],
                    'duration': track['duration_ms'],
                    'search_query': f"{track['name']} {track['artists'][0]['name']}"
                }
                songs.append(song)
        
        return jsonify({
            'success': True,
            'playlist_name': playlist['name'],
            'playlist_image': playlist['images'][0]['url'] if playlist['images'] else None,
            'total_tracks': len(songs),
            'songs': songs
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download_songs():
    data = request.json
    songs = data.get('songs', [])
    format_type = data.get('format', 'mp3')
    
    if not songs:
        return jsonify({'error': 'No hay canciones para descargar'}), 400
    
    try:
        if format_type == 'zip' and len(songs) > 1:
            return download_as_zip(songs)
        else:
            return download_single(songs[0], format_type)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def extract_playlist_id(url):
    patterns = [
        r'playlist/([a-zA-Z0-9]+)',
        r'open\.spotify\.com/playlist/([a-zA-Z0-9]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def download_with_retry(song, ydl_opts, max_retries=3):
    """Descarga con reintentos y rotación de proxies"""
    search_query = song.get('search_query', f"{song['name']} {song['artist']}")
    
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(2, 5))
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_results = ydl.extract_info(
                    f"ytsearch1:{search_query} official audio", 
                    download=False
                )
                
                if not search_results or not search_results.get('entries'):
                    search_results = ydl.extract_info(
                        f"ytsearch1:{search_query}", 
                        download=False
                    )
                
                if not search_results or not search_results.get('entries'):
                    return None, 'No se encontró la canción'
                
                video = search_results['entries'][0]
                ydl.download([video['webpage_url']])
                return True, None
                
        except Exception as e:
            error_str = str(e).lower()
            
            if 'proxy' in error_str or 'connection' in error_str or 'timeout' in error_str:
                if 'proxy' in ydl_opts:
                    proxy_manager.mark_failed(ydl_opts['proxy'])
                    ydl_opts['proxy'] = proxy_manager.get_yt_dlp_proxy()
                    print(f"[Retry] Cambiando proxy, intento {attempt + 1}/{max_retries}")
            else:
                print(f"[Retry] Error: {e}, intento {attempt + 1}/{max_retries}")
            
            if attempt < max_retries - 1:
                time.sleep(random.uniform(3, 6))
            else:
                return None, str(e)
    
    return None, 'Max retries exceeded'

def download_single(song, format_type):
    try:
        ydl_opts = get_yt_dlp_opts()
        ydl_opts['outtmpl'] = f"downloads/{song['id']}.%(ext)s"
        ydl_opts['format'] = 'bestaudio/best' if format_type == 'mp3' else 'best'
        
        if format_type == 'mp3':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        success, error = download_with_retry(song, ydl_opts)
        
        if not success:
            return jsonify({'error': error}), 500
        
        filename = f"downloads/{song['id']}.mp3"
        if os.path.exists(filename):
            return send_file(
                filename,
                as_attachment=True,
                download_name=f"{song['name']} - {song['artist']}.mp3"
            )
        
        return jsonify({'error': 'Archivo no encontrado después de descargar'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def download_as_zip(songs):
    memory_file = io.BytesIO()
    downloaded = 0
    failed = []
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, song in enumerate(songs):
            try:
                print(f"[ZIP] Descargando {i+1}/{len(songs)}: {song['name']}")
                
                ydl_opts = get_yt_dlp_opts()
                ydl_opts['outtmpl'] = f"temp_{song['id']}.%(ext)s"
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
                
                success, error = download_with_retry(song, ydl_opts)
                
                if success:
                    temp_file = f"temp_{song['id']}.mp3"
                    if os.path.exists(temp_file):
                        safe_name = re.sub(r'[<>:"/\\|?*]', '', f"{song['name']} - {song['artist']}")
                        arcname = f"{i+1:03d} - {safe_name[:50]}.mp3"
                        zf.write(temp_file, arcname)
                        os.remove(temp_file)
                        downloaded += 1
                else:
                    failed.append(f"{song['name']} - {error}")
                    
            except Exception as e:
                failed.append(f"{song['name']} - {str(e)}")
                continue
    
    memory_file.seek(0)
    print(f"[ZIP] Completado: {downloaded}/{len(songs)} descargadas")
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'playlist_{downloaded}_canciones.zip'
    )

@app.route('/api/search-sources', methods=['POST'])
def search_sources():
    data = request.json
    query = data.get('query')
    
    if not query:
        return jsonify({'error': 'Query requerida'}), 400
    
    try:
        time.sleep(random.uniform(1, 2))
        
        ydl_opts = get_yt_dlp_opts()
        
        sources = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch5:{query} audio", download=False)
            if results and results.get('entries'):
                for entry in results['entries']:
                    sources.append({
                        'platform': 'YouTube',
                        'title': entry['title'],
                        'url': entry['webpage_url'],
                        'duration': entry.get('duration'),
                        'thumbnail': entry.get('thumbnail')
                    })
        
        return jsonify({
            'success': True,
            'sources': sources
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

os.makedirs('downloads', exist_ok=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))