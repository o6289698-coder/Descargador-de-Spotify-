let currentSongs = [];
let currentPlaylist = null;

async function extractPlaylist() {
    const url = document.getElementById('playlistUrl').value.trim();
    
    if (!url) {
        showError('Por favor ingresa una URL de playlist');
        return;
    }
    
    showLoading(true);
    hideError();
    hideResults();
    
    try {
        const response = await fetch('/api/extract-playlist', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        currentPlaylist = data;
        currentSongs = data.songs;
        displayResults(data);
        
    } catch (error) {
        showError('Error: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function displayResults(data) {
    document.getElementById('playlistName').textContent = data.playlist_name;
    document.getElementById('trackCount').textContent = `${data.total_tracks} canciones`;
    
    if (data.playlist_image) {
        document.getElementById('playlistImage').src = data.playlist_image;
    }
    
    const songsList = document.getElementById('songsList');
    songsList.innerHTML = '';
    
    data.songs.forEach((song, index) => {
        const songEl = createSongElement(song, index + 1);
        songsList.appendChild(songEl);
    });
    
    document.getElementById('results').classList.remove('hidden');
}

function createSongElement(song, number) {
    const div = document.createElement('div');
    div.className = 'song-item';
    
    const duration = formatDuration(song.duration);
    
    div.innerHTML = `
        <input type="checkbox" class="song-checkbox" data-id="${song.id}" checked>
        <span class="song-number">${number}</span>
        <div class="song-info">
            <div class="song-title">${escapeHtml(song.name)}</div>
            <div class="song-artist">${escapeHtml(song.artist)} - ${escapeHtml(song.album)}</div>
        </div>
        <span class="song-duration">${duration}</span>
        <div class="song-actions">
            <button onclick="downloadSingle('${song.id}')" class="btn btn-primary btn-small">
                ⬇️ MP3
            </button>
        </div>
    `;
    
    return div;
}

async function downloadSingle(songId) {
    const song = currentSongs.find(s => s.id === songId);
    if (!song) return;
    
    showModal();
    updateProgress(1, 1, 'Descargando...');
    
    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                songs: [song],
                format: 'mp3'
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            downloadBlob(blob, `${song.name} - ${song.artist}.mp3`);
            updateProgress(1, 1, '¡Descarga completada!');
        } else {
            const data = await response.json();
            throw new Error(data.error || 'Error en la descarga');
        }
        
    } catch (error) {
        alert('Error: ' + error.message);
        closeModal();
    }
}

async function downloadSelected() {
    const checkboxes = document.querySelectorAll('.song-checkbox:checked');
    const selectedIds = Array.from(checkboxes).map(cb => cb.dataset.id);
    const selectedSongs = currentSongs.filter(s => selectedIds.includes(s.id));
    
    if (selectedSongs.length === 0) {
        alert('No hay canciones seleccionadas');
        return;
    }
    
    await downloadSongs(selectedSongs, selectedSongs.length === 1 ? 'mp3' : 'zip');
}

async function downloadAll() {
    if (currentSongs.length === 0) return;
    await downloadSongs(currentSongs, 'zip');
}

async function downloadSongs(songs, format) {
    showModal();
    
    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                songs: songs,
                format: format
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const filename = format === 'zip' ? 'playlist.zip' : 'cancion.mp3';
            downloadBlob(blob, filename);
            updateProgress(songs.length, songs.length, '¡Descarga completada!');
        } else {
            const data = await response.json();
            throw new Error(data.error || 'Error en la descarga');
        }
        
    } catch (error) {
        alert('Error: ' + error.message);
        closeModal();
    }
}

function formatDuration(ms) {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function selectAll() {
    document.querySelectorAll('.song-checkbox').forEach(cb => cb.checked = true);
}

function deselectAll() {
    document.querySelectorAll('.song-checkbox').forEach(cb => cb.checked = false);
}

function showLoading(show) {
    document.getElementById('loading').classList.toggle('hidden', !show);
}

function showError(message) {
    const errorEl = document.getElementById('error');
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
}

function hideError() {
    document.getElementById('error').classList.add('hidden');
}

function hideResults() {
    document.getElementById('results').classList.add('hidden');
}

function showModal() {
    document.getElementById('downloadModal').classList.remove('hidden');
    updateProgress(0, 0, 'Preparando...');
}

function closeModal() {
    document.getElementById('downloadModal').classList.add('hidden');
}

function updateProgress(current, total, text) {
    const percentage = total > 0 ? (current / total) * 100 : 0;
    document.getElementById('progressFill').style.width = percentage + '%';
    document.getElementById('progressText').textContent = text || `${current} / ${total}`;
}

document.getElementById('playlistUrl')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') extractPlaylist();
});

// ============== FUNCIONES DE AMOR ==============

function showLove() {
    createHeartParticles();
    
    const modal = document.getElementById('loveModal');
    modal.classList.remove('hidden');
    
    if (navigator.vibrate) {
        navigator.vibrate([50, 100, 50]);
    }
}

function closeLoveModal() {
    const modal = document.getElementById('loveModal');
    modal.classList.add('hidden');
}

function createHeartParticles() {
    const heartBtn = document.getElementById('loveHeart');
    const rect = heartBtn.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    const particles = ['💕', '💖', '💗', '💝', '💞', '❤️', '💓', '💘'];
    
    for (let i = 0; i < 12; i++) {
        const particle = document.createElement('span');
        particle.className = 'heart-particle';
        particle.textContent = particles[Math.floor(Math.random() * particles.length)];
        
        particle.style.left = centerX + 'px';
        particle.style.top = centerY + 'px';
        
        const angle = (Math.PI * 2 * i) / 12;
        const distance = 100 + Math.random() * 100;
        const tx = Math.cos(angle) * distance;
        const ty = Math.sin(angle) * distance - 100;
        
        particle.style.setProperty('--tx', tx + 'px');
        particle.style.setProperty('--ty', ty + 'px');
        
        const rotation = Math.random() * 360;
        particle.style.transform = `rotate(${rotation}deg)`;
        
        document.body.appendChild(particle);
        
        setTimeout(() => {
            particle.remove();
        }, 1000);
    }
}

document.addEventListener('click', (e) => {
    const modal = document.getElementById('loveModal');
    if (e.target === modal) {
        closeLoveModal();
    }
});

let keyBuffer = '';
document.addEventListener('keypress', (e) => {
    keyBuffer += e.key.toUpperCase();
    keyBuffer = keyBuffer.slice(-5);
    
    if (keyBuffer === 'ALEXA') {
        showLove();
        keyBuffer = '';
    }
});
