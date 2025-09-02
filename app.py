from flask import Flask, request, jsonify, send_file
import whisper
import yt_dlp
import ffmpeg
import os
import tempfile
import threading
import uuid
from datetime import datetime

app = Flask(__name__)

# Cargar modelo al inicio (para mejor rendimiento)
print("🚀 Cargando modelo Whisper...")
model = whisper.load_model("base")
print("✅ Modelo cargado")

# Diccionario para almacenar el estado de las tareas
tasks = {}

def transcribe_video(task_id, url):
    """Función para transcribir video en background"""
    try:
        tasks[task_id]['status'] = 'processing'
        tasks[task_id]['started_at'] = datetime.now().isoformat()
        
        # Crear directorio temporal para esta tarea
        with tempfile.TemporaryDirectory() as temp_dir:
            video_file = os.path.join(temp_dir, f"{task_id}_video.mp4")
            audio_file = os.path.join(temp_dir, f"{task_id}_audio.wav")
            
            # 1. Descargar video
            tasks[task_id]['message'] = 'Descargando video...'
            ydl_opts = {
                'outtmpl': video_file,
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 2. Extraer audio
            tasks[task_id]['message'] = 'Extrayendo audio...'
            ffmpeg.input(video_file).output(
                audio_file,
                ac=1,
                ar='16000'
            ).run(overwrite_output=True, quiet=True, capture_stdout=True, capture_stderr=True)
            
            # 3. Transcribir
            tasks[task_id]['message'] = 'Transcribiendo audio...'
            result = model.transcribe(audio_file, language="es")
            
            # 4. Guardar resultado
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['result'] = result["text"]
            tasks[task_id]['completed_at'] = datetime.now().isoformat()
            tasks[task_id]['message'] = 'Transcripción completada'
            
    except Exception as e:
        tasks[task_id]['status'] = 'error'
        tasks[task_id]['error'] = str(e)
        tasks[task_id]['message'] = f'Error: {str(e)}'

@app.route('/')
def home():
    return jsonify({
        "message": "API de Transcripción con Whisper",
        "endpoints": {
            "/transcribe": "POST - Iniciar transcripción (body: {url: 'video_url'})",
            "/status/<task_id>": "GET - Ver estado de transcripción",
            "/result/<task_id>": "GET - Obtener resultado de transcripción",
            "/health": "GET - Estado del servicio"
        }
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "model_loaded": model is not None})

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({"error": "Se requiere 'url' en el body"}), 400
        
        url = data['url']
        task_id = str(uuid.uuid4())
        
        # Inicializar tarea
        tasks[task_id] = {
            'id': task_id,
            'url': url,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'message': 'Tarea creada'
        }
        
        # Iniciar transcripción en background
        thread = threading.Thread(target=transcribe_video, args=(task_id, url))
        thread.start()
        
        return jsonify({
            "task_id": task_id,
            "status": "pending",
            "message": "Transcripción iniciada",
            "check_status": f"/status/{task_id}"
        }), 202
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status/<task_id>')
def get_status(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Tarea no encontrada"}), 404
    
    task = tasks[task_id]
    response = {
        "task_id": task_id,
        "status": task['status'],
        "message": task.get('message', ''),
        "created_at": task.get('created_at')
    }
    
    if task['status'] == 'completed':
        response['result_url'] = f"/result/{task_id}"
        response['completed_at'] = task.get('completed_at')
    elif task['status'] == 'error':
        response['error'] = task.get('error')
        
    return jsonify(response)

@app.route('/result/<task_id>')
def get_result(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Tarea no encontrada"}), 404
    
    task = tasks[task_id]
    
    if task['status'] != 'completed':
        return jsonify({
            "error": "La transcripción aún no está completa",
            "status": task['status']
        }), 400
    
    return jsonify({
        "task_id": task_id,
        "transcription": task['result'],
        "url": task['url'],
        "created_at": task['created_at'],
        "completed_at": task['completed_at']
    })

@app.route('/transcribe-sync', methods=['POST'])
def transcribe_sync():
    """Endpoint síncrono para transcripciones rápidas (no recomendado para videos largos)"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({"error": "Se requiere 'url' en el body"}), 400
        
        url = data['url']
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_file = os.path.join(temp_dir, "video.mp4")
            audio_file = os.path.join(temp_dir, "audio.wav")
            
            # Descargar video
            ydl_opts = {
                'outtmpl': video_file,
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Extraer audio
            ffmpeg.input(video_file).output(
                audio_file,
                ac=1,
                ar='16000'
            ).run(overwrite_output=True, quiet=True, capture_stdout=True, capture_stderr=True)
            
            # Transcribir
            result = model.transcribe(audio_file, language="es")
            
            return jsonify({
                "transcription": result["text"],
                "url": url
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)