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
        # Usamos la API pública oficial de iTunes para buscar pistas de audio limpias y legales sin bloqueos de servidor
        encoded_query = urllib.request.quote(query)
        url = f"https://itunes.apple.com/search?term={encoded_query}&entity=song&limit=6"
        
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            results = []
            
            for item in data.get('results', []):
                results.append({
                    'title': f"{item.get('trackName')} - {item.get('artistName')}",
                    'url': item.get('previewUrl') # Enlace directo al archivo de audio MP4/MP3 optimizado
                })
                
            return jsonify(results)
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return jsonify([])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
