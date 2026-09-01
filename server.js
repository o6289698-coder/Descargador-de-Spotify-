const express = require('express');
const ytdl = require('@distube/ytdl-core');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname)));

app.get('/download', async (req, res) => {
    const videoUrl = req.query.url;
    const format = req.query.format || 'mp4';

    if (!videoUrl || !ytdl.validateURL(videoUrl)) {
        return res.status(400).send('Enlace de YouTube no válido.');
    }

    try {
        console.log(`Procesando descarga para: ${videoUrl} [${format}]`);
        
        const info = await ytdl.getInfo(videoUrl);
        const title = info.videoDetails.title.replace(/[\/\\?%*:|"<>]/g, ''); // Limpiar caracteres prohibidos en nombres de archivos
        
        const extension = format === 'mp3' ? 'mp3' : 'mp4';
        const filterType = format === 'mp3' ? 'audioonly' : 'videoandaudio';

        res.header('Content-Disposition', `attachment; filename="${encodeURIComponent(title)}.${extension}"`);
        res.header('Content-Type', format === 'mp3' ? 'audio/mpeg' : 'video/mp4');

        ytdl(videoUrl, {
            filter: filterType,
            quality: 'highest',
        }).on('error', (err) => {
            console.error('Error durante el streaming:', err);
            if (!res.headersSent) {
                res.status(500).send('Error al procesar el archivo multimedia.');
            }
        }).pipe(res);

    } catch (error) {
        console.error(`Error general del servidor: ${error.message}`);
        if (!res.headersSent) {
            res.status(500).send('Error al procesar el archivo multimedia.');
        }
    }
});

app.listen(PORT, () => {
    console.log(`Servidor corriendo en el puerto ${PORT}`);
});
