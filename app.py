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
        # Ampliamos la búsqueda a 15 opciones para dar mayor variedad de resultados
        encoded_query = urllib.request.quote(query)
        url = f"https://itunes.apple.com/search?term={encoded_query}&entity=song&limit=15"
        
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            results = []
            
            for item in data.get('results', []):
                track_name = item.get('trackName', 'Sin título')
                artist_name = item.get('artistName', 'Artista desconocido')
                track_view_url = item.get('trackViewUrl', '') # Enlace completo a la pista
                
                if track_name:
                    results.append({
                        'title': f"{track_name} - {artist_name}",
                        'query_term': f"{track_name} {artist_name}",
                        'full_link': track_view_url
                    })
                
            return jsonify(results)
    except Exception as e:
        print(f"Error en búsqueda global: {e}")
        return jsonify([])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
