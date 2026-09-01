FROM node:18-alpine

# Instalar FFmpeg, Python y dependencias del sistema
RUN apk add --no-cache ffmpeg python3 curl py3-pip

# Forzar siempre la descarga de la última versión estable de yt-dlp directamente desde GitHub
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp \
    && chmod a+rx /usr/local/bin/yt-dlp

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
