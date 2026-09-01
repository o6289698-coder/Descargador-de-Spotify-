const express = express = require('express');
const path = require('path');
const https = require('https');

const app = express();
const PORT = process.env.PORT || 10000;

app.use(express.static(path.join(__dirname)));

app.get('/download', (req, res) => {
    const videoUrl = req.query.url;
    const format = req.query.format || 'mp4';

    if (!videoUrl) {
        return res.status(400).send('Falta el enlace de YouTube.');
    }

    // Extraer el ID del video de YouTube de forma segura
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    const match = videoUrl.match(regExp);
    const videoId = (match && match[2].length === 11) ? match[2] : null;

    if (!videoId) {
        return res.status(400).send('Enlace de YouTube no válido.');
    }

    console.log(`Redirigiendo descarga para ID: ${videoId} [${format}]`);

    // Usamos una API externa pública y estable para proveer el stream multimedia sin bloqueos en Render
    if (format === 'mp3') {
        // Redirigir a un servicio público de conversión de audio
        const apiAudioUrl = `https://p.oceanserver.net/ajax/download.php?copyright=0&format=mp3&url=${encodeURIComponent(videoUrl)}`;
        return res.redirect(apiAudioUrl);
    } else {
        // Redirigir a un servicio público de descarga de video
        const apiVideoUrl = `https://co.wuk.sh/api/json`;
        
        // Petición POST a la API pública de Cobalt (muy estable para descargas limpias sin anuncios)
        const data = JSON.stringify({
            url: videoUrl,
            vQuality: '720'
        });

        const options = {
            hostname: 'co.wuk.sh',
            path: '/api/json',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        };

        const apiReq = https.request(options, (apiRes) => {
            let body = '';
            apiRes.on('data', (chunk) => { body += chunk; });
            apiRes.on('end', () => {
                try {
                    const response = JSON.parse(body);
                    if (response.status === 'redirect' || response.status === 'stream') {
                        return res.redirect(response.url);
                    } else if (response.url) {
                        return res.redirect(response.url);
                    } else {
                        res.status(500).send('No se pudo obtener el enlace de descarga de la API externa.');
                    }
                } catch (e) {
                    res.status(500).send('Error procesando la respuesta del servicio externo.');
                }
            });
        });

        apiReq.on('error', () => {
            res.status(500).send('Error de conexión con la API externa.');
        });

        apiReq.write(data);
        apiReq.end();
    }
});

app.listen(PORT, () => {
    console.log(`Servidor corriendo en el puerto ${PORT}`);
});
