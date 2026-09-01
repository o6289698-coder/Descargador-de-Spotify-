const express = require('express');
const { Innertube } = require('youtubei.js');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname)));

app.get('/download', async (req, res) => {
    const videoUrl = req.query.url;
    const format = req.query.format || 'mp4';

    if (!videoUrl) {
        return res.status(400).send('Falta el enlace de YouTube.');
    }

    try {
        console.log(`Iniciando descarga por API para: ${videoUrl} [${format}]`);
        const youtube = await Innertube.create();
        
        // Extraer ID o usar URL directa
        const stream = await youtube.download(videoUrl, {
            type: format === 'mp3' ? 'audio' : 'video',
            quality: 'best',
            format: format === 'mp3' ? 'mp4' : 'mp4' // Contenedor seguro
        });

        const outputExtension = format === 'mp3' ? 'mp3' : 'mp4';
        const outputPath = path.join(__dirname, `output_${Date.now()}.${outputExtension}`);
        const writeStream = fs.createWriteStream(outputPath);

        stream.pipe(writeStream);

        writeStream.on('finish', () => {
            res.download(outputPath, `descarga_erick.${outputExtension}`, (err) => {
                if (err) console.error(`Error al enviar archivo: ${err}`);
                fs.unlink(outputPath, (unlinkErr) => {
                    if (unlinkErr) console.error(unlinkErr);
                });
            });
        });

        stream.on('error', (err) => {
            console.error('Error en el stream de YouTube:', err);
            if (!res.headersSent) {
                res.status(500).send('Error al procesar el archivo multimedia.');
            }
        });

    } catch (error) {
        console.error(`Error general de la API: ${error.message}`);
        return res.status(500).send('Error al procesar el archivo multimedia.');
    }
});

app.listen(PORT, () => {
    console.log(`Servidor corriendo en el puerto ${PORT}`);
});
