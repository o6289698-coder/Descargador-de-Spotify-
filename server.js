const express = require('express');
const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname)));

app.get('/download', (req, res) => {
    const videoUrl = req.query.url;
    const format = req.query.format || 'mp4';

    if (!videoUrl) {
        return res.status(400).send('Falta el enlace de YouTube.');
    }

    const uniqueId = Date.now();
    const outputExtension = format === 'mp3' ? 'mp3' : 'mp4';
    const outputPath = path.join(__dirname, `output_${uniqueId}.${outputExtension}`);

    let ytDlpCommand = '';
    if (format === 'mp3') {
        // Comando optimizado para MP3
        ytDlpCommand = `yt-dlp --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" -x --audio-format mp3 -o "${outputPath}" "${videoUrl}"`;
    } else {
        // Comando seguro y estable para MP4 combinando streams de manera genérica
        ytDlpCommand = `yt-dlp --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" -f "best[ext=mp4]/best" -o "${outputPath}" "${videoUrl}"`;
    }

    console.log(`Ejecutando descarga: ${ytDlpCommand}`);

    exec(ytDlpCommand, (error, stdout, stderr) => {
        if (error) {
            console.error(`Error de yt-dlp: ${error.message}`);
            return res.status(500).send('Error al procesar el archivo multimedia.');
        }

        if (!fs.existsSync(outputPath)) {
            return res.status(500).send('No se pudo generar el archivo.');
        }

        res.download(outputPath, `descarga_erick.${outputExtension}`, (err) => {
            if (err) {
                console.error(`Error al enviar archivo: ${err}`);
            }
            // Limpiar archivo temporal del servidor
            fs.unlink(outputPath, (unlinkErr) => {
                if (unlinkErr) console.error(unlinkErr);
            });
        });
    });
});

app.listen(PORT, () => {
    console.log(`Servidor corriendo en el puerto ${PORT}`);
});
