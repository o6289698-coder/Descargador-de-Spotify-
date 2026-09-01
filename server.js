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
        ytDlpCommand = `yt-dlp -x --audio-format mp3 -o "${outputPath}" "${videoUrl}"`;
    } else {
        // Comando robusto para asegurar que combine video y audio correctamente en un MP4 estándar
        ytDlpCommand = `yt-dlp -f "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4] / b" --merge-output-format mp4 -o "${outputPath}" "${videoUrl}"`;
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
            // Eliminar el archivo temporal del servidor después de enviarlo
            fs.unlink(outputPath, (unlinkErr) => {
                if (unlinkErr) console.error(unlinkErr);
            });
        });
    });
});

app.listen(PORT, () => {
    console.log(`Servidor corriendo en el puerto ${PORT}`);
});
