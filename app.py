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
    
    # Configuramos yt-dlp simulando un cliente de Android para evitar bloqueos de IP en Render
    ydl_opts = {
        'default_search': 'ytsearch5',
        'extract_flat': True,
        'quiet': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }
    
    results = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        results.append({
                            'id': entry.get('id'),
                            'title': entry.get('title'),
                            'url': f"https://www.youtube.com/watch?v={entry.get('id')}"
                        })
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        
    return jsonify(results)

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    if not url:
        return "URL no válida", 400
    
    output_template = os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')
    
    # Forzamos el cliente de Android para el proceso de descarga del MP3
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
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
    
