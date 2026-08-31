import os
from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp

app = Flask(__name__)
DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    if not query:
        return jsonify([])
    
    # Configuramos yt-dlp para realizar una búsqueda general y amplia en la web
    ydl_opts = {
        'default_search': 'auto', # 'auto' permite buscar en múltiples plataformas web, no solo YouTube
        'extract_flat': True,
        'quiet': True,
        'playlistend': 5 # Limita a las primeras 5 mejores coincidencias globales
    }
    
    results = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Añadimos un prefijo de búsqueda general si el usuario ingresa texto plano
            search_query = f"ytsearch5:{query}" if not query.startswith('http') else query
            info = ydl.extract_info(search_query, download=False)
            
            entries = info.get('entries', [info]) if 'entries' in info else [info]
            for entry in entries:
                if entry:
                    results.append({
                        'id': entry.get('id', 'unknown'),
                        'title': entry.get('title', 'Resultado sin título'),
                        'url': entry.get('webpage_url') or entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                    })
    except Exception as e:
        print(f"Error en búsqueda global: {e}")
        
    return jsonify(results)

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    if not url:
        return "URL no válida", 400
    
    output_template = os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_filename = os.path.splitext(filename)[0] + '.mp3'
            
        return send_file(mp3_filename, as_attachment=True)
    except Exception as e:
        return f"Error al procesar el audio: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
