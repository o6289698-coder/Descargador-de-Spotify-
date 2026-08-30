import os
import shutil
import uuid
import zipfile
import requests
from flask import Flask, render_template_string, request, jsonify, send_file, after_this_request
import yt_dlp

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spotify Downloader</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #0f172a, #1e293b); 
            color: #f8fafc; 
            text-align: center; 
            padding: 40px 20px; 
            margin: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container { 
            width: 100%;
            max-width: 520px; 
            background: rgba(30, 41, 59, 0.85); 
            backdrop-filter: blur(10px);
            padding: 30px; 
            border-radius: 16px; 
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(56, 189, 248, 0.2);
        }
        h2 {
            color: #38bdf8;
            margin-bottom: 25px;
            font-size: 1.6rem;
            letter-spacing: 0.5px;
        }
        input[type="text"] { 
            width: 88%; 
            padding: 12px 15px; 
            margin-bottom: 15px; 
            border-radius: 8px; 
            border: 1px solid #334155; 
            background: #0f172a; 
            color: #f8fafc; 
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus {
            border-color: #38bdf8;
        }
        select, button { 
            padding: 12px 20px; 
            border-radius: 8px; 
            border: none; 
            font-weight: bold; 
            cursor: pointer; 
            font-size: 0.95rem;
        }
        select {
            background: #0f172a;
            color: #f8fafc;
            border: 1px solid #334155;
            margin-right: 8px;
            outline: none;
        }
        button[type="submit"] { 
            background: linear-gradient(135deg, #0284c7, #0ea5e9); 
            color: white; 
            transition: opacity 0.2s, transform 0.1s;
        }
        button[type="submit"]:hover { 
            opacity: 0.9;
            transform: translateY(-1px);
        }
        .result { 
            margin-top: 20px; 
            word-break: break-all; 
            font-size: 0.9rem;
        }
        .result h3 {
            color: #34d399;
            font-size: 1rem;
            margin-bottom: 15px;
        }
        .preview-container {
            margin-bottom: 15px;
            display: flex;
            justify-content: center;
        }
        .preview-media {
            max-width: 100%;
            max-height: 220px;
            border-radius: 8px;
            border: 1px solid #334155;
            object-fit: cover;
        }
        .download-btn { 
            display: inline-block; 
            padding: 12px 24px; 
            background: linear-gradient(135deg, #059669, #10b981); 
            color: #fff; 
            text-decoration: none; 
            border-radius: 8px; 
            font-weight: bold; 
            margin-top: 5px;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
            transition: transform 0.1s;
        }
        .download-btn:hover {
            transform: translateY(-1px);
        }
        .heart-section { 
            margin-top: 30px; 
        }
        .heart-btn { 
            background: none; 
            border: none; 
            font-size: 2.2rem; 
            cursor: pointer; 
            color: #f43f5e; 
            outline: none; 
            transition: transform 0.2s; 
        }
        .heart-btn:hover { 
            transform: scale(1.25); 
        }
        .love-message { 
            color: #34d399; 
            font-weight: bold; 
            font-size: 1.1rem; 
            margin-top: 10px; 
            display: none; 
        }
        .dev-credit { 
            margin-top: 30px; 
            font-size: 0.85rem; 
            color: #94a3b8; 
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding-top: 15px;
        }
        .dev-credit span {
            color: #38bdf8;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Spotify Downloader</h2>
        <form id="download-form">
            <input type="text" id="url" placeholder="Pega enlace de canción o playlist de Spotify..." required><br>
            <div style="display: flex; justify-content: center; gap: 5px;">
                <select id="format">
                    <option value="mp3">Canción MP3</option>
                    <option value="zip">Playlist ZIP</option>
                </select>
                <button type="submit">Procesar</button>
            </div>
        </form>
        <div id="result" class="result"></div>

        <div class="heart-section">
            <button type="button" class="heart-btn" id="heart-btn">❤️</button>
            <div id="love-message" class="love-message">Te amo Alexa</div>
        </div>

        <div class="dev-credit">
            Desarrollado por <span>Erick</span>
        </div>
    </div>

    <script>
        document.getElementById('download-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = "<span style='color: #38bdf8;'>Procesando solicitud... Por favor espera.</span>";
            
            const url = document.getElementById('url').value;
            const format = document.getElementById('format').value;

            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 120000);

                const response = await fetch('/procesar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url, format }),
                    signal: controller.signal
                });
                clearTimeout(timeoutId);

                const data = await response.json();
                if (data.success) {
                    let previewHtml = '';
                    if (data.thumbnail && format !== 'zip') {
                        previewHtml = `<div class="preview-container"><img src="${data.thumbnail}" class="preview-media" alt="Previsualización"></div>`;
                    }

                    resultDiv.innerHTML = `
                        <h3>${data.title}</h3>
                        ${previewHtml}
                        <a href="/download_file?file=${encodeURIComponent(data.file_id)}&name=${encodeURIComponent(data.title)}&ext=${data.ext}" class="download-btn">Descargar ${data.ext.toUpperCase()}</a>
                    `;
                } else {
                    resultDiv.innerHTML = `<p style="color: #f87171;">Error: ${data.error}</p>`;
                }
            } catch (err) {
                resultDiv.innerHTML = `<p style="color: #f87171;">Error de conexión con el servidor.</p>`;
            }
        });

        document.getElementById('heart-btn').addEventListener('click', () => {
            const msg = document.getElementById('love-message');
            msg.style.display = (msg.style.display === 'block') ? 'none' : 'block';
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/procesar', methods=['POST'])
def procesar():
    data = request.get_json()
    url = data.get('url', '').strip()
    formato = data.get('format', 'mp3')

    if "spotify.com" not in url:
        return jsonify({'success': False, 'error': 'Introduce un enlace válido de Spotify.'})

    batch_id = str(uuid.uuid4())
    out_template = f'/tmp/{batch_id}_%(title)s.%(ext)s'

    try:
        oembed_res = requests.get(f"https://open.spotify.com/oembed?url={url}", timeout=8).json()
        item_title = oembed_res.get('title', 'Audio Spotify')
        thumbnail = oembed_res.get('thumbnail_url', '')

        search_query = f"ytsearch1:{item_title} audio"

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': out_template,
            'format': 'bestaudio/best',
            # Forzamos el cliente de TV para evitar el aviso de "bot" en la nube
            'extractor_args': {'youtube': {'player_client': ['tv', 'web_safari']}},
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(search_query, download=True)

        downloaded_files = []
        for f in os.listdir('/tmp'):
            if f.startswith(batch_id):
                downloaded_files.append(os.path.join('/tmp', f))

        if not downloaded_files:
            return jsonify({'success': False, 'error': 'No se pudo generar el archivo de audio.'})

        if formato == 'zip' or len(downloaded_files) > 1:
            zip_filename = f"{batch_id}.zip"
            zip_path = os.path.join('/tmp', zip_filename)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in downloaded_files:
                    zipf.write(file, os.path.basename(file))
                    try:
                        os.remove(file)
                    except:
                        pass
            
            return jsonify({
                'success': True,
                'title': f"Colección: {item_title}",
                'thumbnail': thumbnail,
                'file_id': zip_filename,
                'ext': 'zip'
            })
        else:
            single_file = downloaded_files[0]
            actual_filename = os.path.basename(single_file)
            return jsonify({
                'success': True,
                'title': item_title,
                'thumbnail': thumbnail,
                'file_id': actual_filename,
                'ext': 'mp3'
            })

    except Exception as e:
        return jsonify({'success': False, 'error': f'Error al procesar: {str(e)}'})

@app.route('/download_file')
def download_file():
    file_id = request.args.get('file')
    name = request.args.get('name', 'spotify_audio')
    ext = request.args.get('ext', 'mp3')
    
    file_path = os.path.join('/tmp', file_id)

    if not os.path.exists(file_path):
        return "El archivo ya no está disponible o caducó.", 404

    @after_this_request
    def cleanup(response):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        return response

    return send_file(file_path, as_attachment=True, download_name=f"{name}.{ext}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
        
