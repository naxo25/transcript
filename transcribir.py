import whisper
import yt_dlp
import ffmpeg
import os

# URL del video
URL = "https://d5tow79zpi0qo.cloudfront.net/bcef4b8f-9930-49bb-9414-dc92aad2ec02-BAD+BOYS+FOR+LIFE+CLIP+LAT+3.mp4"

# Nombres de archivos temporales
VIDEO_FILE = "video_descargado.mp4"
AUDIO_FILE = "audio.wav"
TRANSCRIPT_FILE = "transcripcion.txt"

print("🚀 Iniciando proceso de transcripción...\n")

# === 1. Descargar el video ===
print("1. Descargando el video...")
ydl_opts = {
    'outtmpl': VIDEO_FILE,
    'quiet': True,
}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([URL])
print("✅ Video descargado.")

# === 2. Extraer audio (16kHz, mono) ===
print("2. Extrayendo audio...")
try:
    ffmpeg.input(VIDEO_FILE).output(
        AUDIO_FILE,
        ac=1,          # 1 canal (mono)
        ar='16000'     # 16kHz (ideal para Whisper)
    ).run(overwrite_output=True, quiet=True)
    print("✅ Audio extraído.")
except ffmpeg.Error as e:
    print("❌ Error al extraer audio:", e.stderr.decode() if e.stderr else e)
    exit(1)

# === 3. Cargar modelo Whisper y transcribir ===
print("3. Cargando modelo Whisper (base-es)...")

# Opción recomendada: usar modelo en español para mejor rendimiento
# Nota: Whisper no tiene modelo "base-es" oficial, pero podemos forzar idioma
model = whisper.load_model("base")  # Puedes usar "small" si tienes más RAM

print("4. Transcribiendo audio al español...")
result = model.transcribe(AUDIO_FILE, language="es")
texto = result["text"]

# === 4. Guardar en archivo de texto ===
with open(TRANSCRIPT_FILE, "w", encoding="utf-8") as f:
    f.write(texto)

print("\n🎉 Transcripción completada!")
print("="*50)
print(texto)
print("="*50)
print(f"📄 Guardado en: {TRANSCRIPT_FILE}")

# === 5. Opcional: limpiar archivos temporales ===
# Descomenta las siguientes líneas si quieres borrar los archivos
# os.remove(VIDEO_FILE)
# os.remove(AUDIO_FILE)
# print("🧹 Archivos temporales eliminados.")

