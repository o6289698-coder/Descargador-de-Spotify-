const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname)));

app.get('/download', (req, res) => {
    const videoUrl = req.query.url;
    const format = req.query.format || 'mp4';

    if (!videoUrl) {
        return res.status(400).send('Falta el enlace de YouTube.');
    }

    console.log(`Procesando enlace para formato ${format}: ${videoUrl}`);

    let ytDlpArgs = [];
    if (format === 'mp3') {
        ytDlpArgs = [
            '-x', '--audio-format', 'mp3',
            '--output', '-',
            videoUrl
        ];
        res.header('Content-Type', 'audio/mpeg');
        res.header('Content-Disposition', 'attachment; filename="audio_erick.mp3"');
    } else {
        ytDlpArgs = [
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '--output', '-',
            videoUrl
        ];
        res.header('Content-Type', 'video/mp4');
        res.header('Content-Disposition', 'attachment; filename="video_erick.mp4"');
    }

    const ytDlpProcess = spawn('yt-dlp', ytDlpArgs);

    ytDlpProcess.stdout.pipe(res);

    ytDlpProcess.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
    });

    ytDlpProcess.on('close', (code) => {
        if (code !== 0) {
            console.log(`Proceso finalizado con código ${code}`);
        }
    });

    req.on('close', () => {
        ytDlpProcess.kill();
    });
});

app.listen(PORT, () => {
    console.log(`Servidor corriendo en el puerto ${PORT}`);
});
