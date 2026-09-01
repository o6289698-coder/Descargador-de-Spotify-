const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 10000;

app.use(express.static(path.join(__dirname)));

app.get('/download', (req, res) => {
    const videoUrl = req.query.url;
    const format = req.query.format || 'mp4';

    if (!videoUrl) {
        return res.status(400).send('Falta el enlace de YouTube.');
    }

    // Extraer ID de YouTube de forma segura
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    const match = videoUrl.match(regExp);
    const videoId = (match && match[2].length === 11) ? match[2] : null;

    if (!videoId) {
        return res.status(400).send('Enlace de YouTube no válido.');
    }

    console.log(`Procesando redirección para ID: ${videoId} [${format}]`);

    // Redirigir a un servicio web de descarga estable que procesa el enlace al instante
    if (format === 'mp3') {
        res.redirect(`https://loader.to/api/button/?url=${encodeURIComponent(videoUrl)}&f=mp3`);
    } else {
        res.redirect(`https://loader.to/api/button/?url=${encodeURIComponent(videoUrl)}&f=mp4`);
    }
});

app.listen(PORT, () => {
    console.log(`Servidor corriendo en el puerto ${PORT}`);
});
