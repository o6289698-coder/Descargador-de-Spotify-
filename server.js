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

    console.log(`Procesando con yt-dlp: ${videoUrl} [${format}]`);
    
    const outputId = Date.now();
    const ext = format === 'mp3' ? 'mp3' : 'mp4';
    const outputPath = path.join(__dirname, `output_${outputId}.${ext}`);

    // Comando yt-dlp (si tienes un archivo cookies.txt en tu repo, usará --cookies cookies.txt automáticamente)
    const cookiesParam = fs.existsSync(path.join(__dirname, 'cookies.txt')) ? `--cookies cookies.txt` : '';
    
    let command = '';
    if (format === 'mp3') {
        command = `yt-dlp ${cookiesParam} -x --audio-format mp3 -o "${outputPath}" "${videoUrl}"`;
    } else {
        command = `yt-dlp ${cookiesParam} -f "best[ext=mp4]/best" -o "${outputPath}" "${videoUrl}"`;
    }

    exec(command, (error, stdout, stderr) => {
        if (error) {
            console.error(`Error de ejecución: ${error.message}`);
            return res.status(500).send('Error al procesar el archivo multimedia.');
        }

        if (fs.existsSync(outputPath)) {
            res.download(outputPath, `descarga_erick.${ext}`, (err) => {
                if (err) console.error(`Error al enviar archivo: ${err}`);
                fs.unlink(outputPath, () => {}); // Limpiar archivo local después de enviar
            });
        } else {
            res.status(500).send('No se generó el archivo de salida.');
        }
    });
});

app.listen(PORT, () => {
    console.log(`Servidor corriendo en el puerto ${PORT}`);
});
