import os
from flask import Flask, render_template, request, jsonify
import urllib.request
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    if not query:
        return jsonify([])
    
    try:
        # Ampliamos la búsqueda utilizando la API global de Deezer / catálogos abiertos de streaming
        encoded_query = urllib.request.quote(query)
        url = f"https://api.deezer.com/search?q={encoded_query}&limit=15"
        
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            results = []
            
            for item in data.get('data', []):
                track_title = item.get('title', 'Sin título')
                artist_name = item.get('artist', {}).get('name', 'Artista desconocido')
                preview_url = item.get('preview', '') # Vista previa o flujo de audio
                link = item.get('link', '')
                
                # Priorizamos elementos que tengan pista de audio fluida
                if preview_url:
                    results.append({
                        'title': f"{track_title} - {artist_name}",
                        'url': preview_url,
                        'web_link': link
                    })
                
            return jsonify(results)
    except Exception as e:
        print(f"Error en búsqueda global: {e}")
        return jsonify([])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
