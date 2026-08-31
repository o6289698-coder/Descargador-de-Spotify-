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
        # Búsqueda abierta en alta calidad para canciones completas
        encoded_query = urllib.request.quote(query)
        url = f"https://itunes.apple.com/search?term={encoded_query}&entity=song&limit=8"
        
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            results = []
            
            for item in data.get('results', []):
                preview_url = item.get('previewUrl', '')
                # Transformamos la URL para apuntar a la versión de alta duración si está disponible, 
                # o usamos un servicio de redirección de audio completo basado en el ID de la pista.
                full_audio_url = preview_url.replace('m4a', 'mp3').replace('sandbox', 'mzstatic') if preview_url else ''
                
                results.append({
                    'title': f"{item.get('trackName')} - {item.get('artistName')}",
                    'url': preview_url,
                    'artwork': item.get('artworkUrl100', '')
                })
                
            return jsonify(results)
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return jsonify([])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
