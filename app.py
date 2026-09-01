import os
import tempfile
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# Configurar las cookies desde la variable de entorno de Render de forma segura
COOKIES_PATH = None
cookies_env = os.environ.get("YT_COOKIES")
if cookies_env:
    tf = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt")
    tf.write(cookies_env)
    tf.close()
    COOKIES_PATH = tf.name

# HTML, CSS y JavaScript integrados con la estética y el corazón
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reproductor y Descargador Musical</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --accent: #f43f5e;
            --accent-hover: #e11d48;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: var(--bg-color); color: var(--text-main); min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 20px; }
        
        .container { width: 100%; max-width: 700px; background: var(--card-bg); padding: 25px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); border: 1px solid var(--border); position: relative; }
        
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; border-bottom: 1px solid var(--border); padding-bottom: 15px; }
        h1 { font-size: 1.4rem; color: var(--text-main); display: flex; align-items: center; gap: 8px; }
        
        /* Botón del Corazón */
        .heart-btn { background: none; border: none; font-size: 1.8rem; cursor: pointer; transition: transform 0.2s; position: relative; }
        .heart-btn:hover { transform: scale(1.15); }
        .heart-tooltip {
            position: absolute; right: 0; top: 40px; background: var(--accent); color: white;
            padding: 5px 12px; border-radius: 8px; font-size: 0.8rem; white-space: nowrap;
            opacity: 0; pointer-events: none; transition: opacity 0.3s ease; box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        }
        .heart-btn.active .heart-tooltip { opacity: 1; }

        /* Buscador */
        .search-box { display: flex; gap: 10px; margin-bottom: 25px; }
        input[type="text"] {
            flex: 1; padding: 12px 16px; border-radius: 10px; border: 1px solid var(--border);
            background: #0f172a; color: white; font-size: 1rem; outline: none; transition: border-color 0.2s;
        }
        input[type="text"]:focus { border-color: var(--accent); }
        button.search-submit {
            background: var(--accent); color: white; border: none; padding: 0 20px;
            border-radius: 10px; font-weight: bold; cursor: pointer; transition: background 0.2s;
        }
        button.search-submit:hover { background: var(--accent-hover); }

        /* Resultados de Coincidencias */
        .results-list { display: flex; flex-direction: column; gap: 12px; max-height: 450px; overflow-y: auto; }
        .result-item {
            display: flex; align-items: center; justify-content: space-between; background: rgba(15, 23, 42, 0.6);
            padding: 10px 15px; border-radius: 10px; border: 1px solid var(--border); gap: 15px;
        }
        .result-thumb { width: 80px; height: 45px; object-fit: cover; border-radius: 6px; background: #000; }
        .result-info { flex: 1; overflow: hidden; }
        .result-title { font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px; }
        .result-channel { font-size: 0.8rem; color: var(--text-muted); }
        
        .download-btn {
            background: #10b981; color: white; border: none; padding: 8px 14px;
            border-radius: 8px; cursor: pointer; font-size: 0.85rem; font-weight: bold; text-decoration: none;
            transition: background 0.2s; white-space: nowrap;
        }
        .download-btn:hover { background: #059669; }

        .loading { text-align: center; color: var(--text-muted); padding: 20px; font-style: italic; }
    </style>
</head>
<body>

    <div class="container">
        <header>
            <h1>🎵 Descargador Musical</h1>
            <!-- Botón del Corazón que dice Te amo Deyra -->
            <button class="heart-btn" id="heartBtn" onclick="toggleLove()">
                ❤️
                <span class="heart-tooltip" id="heartTooltip">Te amo Deyra</span>
            </button>
        </header>

        <div class="search-box">
            <input type="text" id="queryInput" placeholder="Ej. La Banda del Recodo o La Palma Luis Pérez Meza..." onkeypress="handleKeyPress(event)">
            <button class="search-submit" onclick="searchMusic()">Buscar</button>
        </div>

        <div id="resultsContainer" class="results-list">
            <div class="loading">Escribe una canción o artista para ver todas las coincidencias...</div>
        </div>
    </div>

    <script>
        function toggleLove() {
            const btn = document.getElementById('heartBtn');
            btn.classList.add('active');
            setTimeout(() => {
                btn.classList.remove('active');
            }, 3000); // Se oculta a los 3 segundos
        }

        function handleKeyPress(e) {
            if (e.key === 'Enter') {
                searchMusic();
            }
        }

        async function searchMusic() {
            const query = document.getElementById('queryInput').value.trim();
            const container = document.getElementById('resultsContainer');
            
            if (!query) return;

            container.innerHTML = '<div class="loading">Buscando coincidencias... 🎶</div>';

            try {
                const response = await fetch('/search?q=' + encodeURIComponent(query));
                const data = await response.json();

                if (data.error) {
                    container.innerHTML = `<div class="loading" style="color: var(--accent);">${data.error}</div>`;
                    return;
                }

                if (data.length === 0) {
                    container.innerHTML = '<div class="loading">No se encontraron coincidencias.</div>';
                    return;
                }

                let html = '';
                data.forEach(item => {
                    html += `
                        <div class="result-item">
                            <img src="${item.thumbnail}" class="result-thumb" alt="Thumbnail">
                            <div class="result-info">
                                <div class="result-title" title="${item.title}">${item.title}</div>
                                <div class="result-channel">${item.channel}</div>
                            </div>
                            <a href="/download?url=${encodeURIComponent(item.url)}" class="download-btn">Descargar MP3</a>
                        </div>
                    `;
                });
                container.innerHTML = html;

            } catch (err) {
                container.innerHTML = '<div class="loading" style="color: var(--accent);">Hubo un error al realizar la búsqueda.</div>';
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/search")
def search():
    query = request.args.get("q", "")
    if not query:
        return jsonify([])

    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
    }
    if COOKIES_PATH:
        ydl_opts['cookiefile'] = COOKIES_PATH

    try:
        # Buscamos múltiples coincidencias (por ejemplo, las primeras 15 opciones que arroje YouTube)
        search_query = f"ytsearch15:{query}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            entries = info.get('entries', [])
            
            results = []
            for entry in entries:
                if entry:
                    results.append({
                        'title': entry.get('title', 'Sin título'),
                        'url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                        'channel': entry.get('uploader', 'Desconocido'),
                        'thumbnail': entry.get('thumbnail', '')
                    })
            return jsonify(results)
    except Exception as e:
        return jsonify({"error": f"Error en la búsqueda: {str(e)}"})

@app.route("/download")
def download():
    url = request.args.get("url")
    if not url:
        return "URL no proporcionada", 400

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
    }
    if COOKIES_PATH:
        ydl_opts['cookiefile'] = COOKIES_PATH

    try:
        # Nota: En Render o entornos serverless efímeros, la descarga directa por streaming requiere manejo de archivo temporal, 
        # pero con esto puedes estructurar la lógica base que ya probamos.
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_filename = os.path.splitext(filename)[0] + ".mp3"
            
            from flask import send_file
            return send_file(mp3_filename, as_attachment=True)
    except Exception as e:
        return f"Error al descargar: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    
