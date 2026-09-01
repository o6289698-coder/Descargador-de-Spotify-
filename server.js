const express = require('express');
const ytdl = require('@distube/ytdl-core');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 10000;

app.use(express.static(path.join(__dirname)));

app.get('/download', async (req, res) => {
    const videoUrl = req.query.url;
    const format = req.query.format || 'mp4';

    if (!ytdl.validateURL(videoUrl)) {
        return res.status(400).send('Enlace de YouTube no válido.');
    }

    try {
        console.log(`Obteniendo info para: ${videoUrl} [${format}]`);
        const info = await ytdl.getInfo(videoUrl);
        const title = info.videoDetails.title.replace(/[^\w\s]/gi, ''); // Limpiar caracteres especiales del título

        if (format === 'mp3') {
            res.header('Content-Disposition', `attachment; filename="${title}.mp3"`);
            res.header('Content-Type', 'audio/mpeg');
            ytdl(videoUrl, { quality: 'highestaudio', filter: 'audioonly' }).pipe(res);
        } else {
            res.header('Content-Disposition', `attachment; filename="${title}.mp4"`);
            res.header('Content-Type', 'video/mp4');
            ytdl(videoUrl, { quality: 'highest' }).pipe(res);
        }

    } catch (error) {
        console.error(`Error procesando video: ${error.message}`);
        res.status(500).send('Error al procesar el multimedia en el servidor. Es posible que YouTube haya bloqueado temporalmente la IP.');
    }
});

app.listen(PORT, () => {
    console.log(`Servidor corriendo en el puerto ${PORT}`);
});
