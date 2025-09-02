from flask import Flask, request, jsonify
import whisper
import yt_dlp
import ffmpeg
import os
import tempfile
import threading
import uuid
from datetime import datetime
import gc  # Garbage collector para limpiar memoria

app = Flask(__name__)

# OPTIMIZACIÓN 1: Usar modelo TINY (39MB) en lugar de BASE (74MB)
# Configuración del modelo desde variable de entorno
MODEL_NAME = os.environ.get('WHISPER_MODEL', 'tiny')
print(f"🚀 Usando modelo Whisper: {MODEL_NAME}")

# OPTIMIZACIÓN 2: Lazy loading - NO cargar el modelo al inicio
model = None
model_lock = threading.Lock()

def get_model():
    """Carga el modelo solo cuando se necesita"""
    global model
    if model is None:
        with model_lock:
            if model is None:  # Double-check
                print(f"📦 Cargando modelo {MODEL_NAME}...")
                model = whisper.load_model(MODEL_NAME)
                print("✅ Modelo cargado")
    return model

# Diccionario para almacenar el estado de las tareas (máximo 10 tareas en memoria)
tasks = {}
MAX_TASKS = 10

def cleanup_old_tasks():
    """Limpia tareas antiguas para liberar memoria"""
    global tasks
    if len(tasks) > MAX_TASKS:
        # Ordenar por fecha de creación y mantener solo las últimas MAX_TASKS
        sorted_tasks = sorted(tasks.items(), 
                            key=lambda x: x[1].get('created_at', ''), 
                            reverse=True)
        tasks = dict(sorted_tasks[:MAX_TASKS])
        gc.collect()  # Forzar recolección de basura

def transcribe_video(task_id, url):
    """Función para transcribir video en background"""
    try:
        tasks[task_id]['status'] = 'processing'
        tasks[task_id]['started_at'] = datetime.now().isoformat()
        
        # Crear directorio temporal para esta tarea
        with tempfile.TemporaryDirectory() as temp_dir:
            video_file = os.path.join(temp_dir, f"{task_id}_video.mp4")
            audio_file = os.path.join(temp_dir, f"{task_id}_audio.wav")
            
            # 1. Descargar video con límite de calidad
            tasks[task_id]['message'] = 'Descargando video...'
            # En la función transcribe_video, en ydl_opts:
            ydl_opts = {
                'outtmpl': video_file,
                'quiet': True,
                'no_warnings': True,
                'format': 'worst[ext=mp4]/worst',
                # AGREGAR ESTOS LÍMITES:
                'max_filesize': 50000000,  # Máximo 50MB
                'socket_timeout': 30,       # Timeout de descarga
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 2. Extraer audio con compresión
            tasks[task_id]['message'] = 'Extrayendo audio...'
            # OPTIMIZACIÓN 4: Reducir calidad de audio para ahorrar memoria
            ffmpeg.input(video_file).output(
                audio_file,
                ac=1,      # Mono
                ar='16000', # 16kHz (mínimo para Whisper)
                ab='32k'    # Bitrate bajo
            ).run(overwrite_output=True, quiet=True, capture_stdout=True, capture_stderr=True)
            
            # Eliminar video inmediatamente para liberar memoria
            if os.path.exists(video_file):
                os.remove(video_file)
            
            # 3. Transcribir
            tasks[task_id]['message'] = 'Transcribiendo audio...'
            
            # Obtener modelo (lazy loading)
            current_model = get_model()
            
            # OPTIMIZACIÓN 5: Opciones de transcripción para menor uso de memoria
            result = current_model.transcribe(
                audio_file, 
                language="es",
                fp16=False,  # No usar FP16 (puede causar problemas en CPU)
                verbose=False,
                # Opciones para reducir memoria:
                best_of=1,  # Solo 1 beam search en lugar de 5
                beam_size=1,  # Reducir beam size
                temperature=0  # Sin sampling múltiple
            )
            
            # 4. Guardar resultado
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['result'] = result["text"]
            tasks[task_id]['completed_at'] = datetime.now().isoformat()
            tasks[task_id]['message'] = 'Transcripción completada'
            
            # OPTIMIZACIÓN 6: Limpiar memoria después de transcribir
            del result
            gc.collect()
            
            # Limpiar tareas antiguas
            cleanup_old_tasks()
            
    except Exception as e:
        tasks[task_id]['status'] = 'error'
        tasks[task_id]['error'] = str(e)
        tasks[task_id]['message'] = f'Error: {str(e)}'
        
        # Limpiar memoria en caso de error
        gc.collect()

@app.route('/')
def home():
    # Información sobre memoria
    memory_info = {
        "model": MODEL_NAME,
        "model_loaded": model is not None,
        "active_tasks": len(tasks)
    }
    
    return jsonify({
        "message": "API de Transcripción con Whisper (Optimizada)",
        "memory_optimization": memory_info,
        "endpoints": {
            "/transcribe": "POST - Iniciar transcripción (body: {url: 'video_url'})",
            "/status/<task_id>": "GET - Ver estado de transcripción",
            "/result/<task_id>": "GET - Obtener resultado de transcripción",
            "/health": "GET - Estado del servicio",
            "/clear-cache": "POST - Limpiar caché y memoria"
        }
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy", 
        "model": MODEL_NAME,
        "model_loaded": model is not None,
        "tasks_in_memory": len(tasks)
    })

@app.route('/clear-cache', methods=['POST'])
def clear_cache():
    """Endpoint para limpiar memoria manualmente"""
    global model, tasks
    
    # Limpiar modelo
    if model is not None:
        del model
        model = None
    
    # Limpiar tareas completadas
    tasks = {k: v for k, v in tasks.items() 
             if v.get('status') not in ['completed', 'error']}
    
    # Forzar recolección de basura
    gc.collect()
    
    return jsonify({
        "message": "Memoria limpiada",
        "model_unloaded": True,
        "remaining_tasks": len(tasks)
    })

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({"error": "Se requiere 'url' en el body"}), 400
        
        url = data['url']
        task_id = str(uuid.uuid4())
        
        # Verificar límite de tareas
        if len(tasks) >= MAX_TASKS * 2:
            cleanup_old_tasks()
        
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
        thread.daemon = True  # Daemon thread para que no bloquee el shutdown
        thread.start()
        
        return jsonify({
            "task_id": task_id,
            "status": "pending",
            "message": "Transcripción iniciada",
            "check_status": f"/status/{task_id}",
            "model": MODEL_NAME
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
    
    # Preparar respuesta
    response = jsonify({
        "task_id": task_id,
        "transcription": task['result'],
        "url": task['url'],
        "created_at": task['created_at'],
        "completed_at": task['completed_at']
    })
    
    # OPTIMIZACIÓN 7: Opción para limpiar resultado después de entregarlo
    # (descomenta si quieres liberar memoria agresivamente)
    # del tasks[task_id]['result']
    # tasks[task_id]['result'] = "Resultado ya fue entregado"
    
    return response

if __name__ == '__main__':
    # OPTIMIZACIÓN 8: Solo 1 worker para reducir memoria
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, threaded=True)