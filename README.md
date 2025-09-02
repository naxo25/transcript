# API de Transcripción con Whisper para Render

## 📋 Descripción
API REST para transcribir videos a texto usando OpenAI Whisper, optimizada para desplegar en Render.

## 🚀 Despliegue en Render

### Opción 1: Despliegue con GitHub (Recomendado)

1. **Sube tu código a GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin tu-repo-github.git
   git push -u origin main
   ```

2. **En Render:**
   - Ve a [render.com](https://render.com) y crea una cuenta
   - Click en "New +" → "Web Service"
   - Conecta tu cuenta de GitHub
   - Selecciona tu repositorio
   - Render detectará automáticamente el `render.yaml`
   - Click en "Create Web Service"

### Opción 2: Despliegue Manual

1. **En Render Dashboard:**
   - Click en "New +" → "Web Service"
   - Selecciona "Build and deploy from a Git repository"
   - Configura:
     - **Name:** whisper-transcription-api
     - **Runtime:** Docker
     - **Build Command:** (dejar vacío)
     - **Start Command:** (dejar vacío, usa el del Dockerfile)

## 📁 Estructura del Proyecto

```
whisper-api/
├── app.py              # API Flask principal
├── requirements.txt    # Dependencias Python
├── Dockerfile         # Configuración del contenedor
├── render.yaml        # Configuración de Render
└── README.md          # Este archivo
```

## 🔧 Configuración Importante

### Limitaciones del Plan Gratuito de Render:
- **RAM:** 512 MB (puede ser limitado para videos largos)
- **CPU:** Compartida
- **Tiempo de build:** 15 minutos máximo
- **El servicio se suspende después de 15 minutos de inactividad**

### Recomendaciones:
- Para producción, considera usar al menos el plan **Starter** ($7/mes) que incluye:
  - 2 GB RAM
  - CPU dedicada
  - Sin suspensión automática

## 📡 Endpoints de la API

### 1. **POST /transcribe** (Asíncrono - Recomendado)
```bash
curl -X POST https://tu-app.onrender.com/transcribe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://url-del-video.mp4"}'
```

Respuesta:
```json
{
  "task_id": "uuid-aqui",
  "status": "pending",
  "message": "Transcripción iniciada",
  "check_status": "/status/uuid-aqui"
}
```

### 2. **GET /status/<task_id>**
```bash
curl https://tu-app.onrender.com/status/uuid-aqui
```

### 3. **GET /result/<task_id>**
```bash
curl https://tu-app.onrender.com/result/uuid-aqui
```

### 4. **POST /transcribe-sync** (Síncrono - Videos cortos)
```bash
curl -X POST https://tu-app.onrender.com/transcribe-sync \
  -H "Content-Type: application/json" \
  -d '{"url": "https://url-del-video.mp4"}'
```

## ⚠️ Consideraciones de Rendimiento

1. **Modelo Whisper:**
   - El código usa el modelo `base` por defecto
   - Para mejor precisión pero más lento: cambia a `small` o `medium`
   - Para más velocidad pero menor precisión: usa `tiny`

2. **Timeout:**
   - Render tiene un timeout de 30 segundos para requests en plan gratuito
   - Por eso usamos endpoints asíncronos para videos largos

3. **Memoria:**
   - Si tienes errores de memoria, considera:
     - Usar modelo `tiny` de Whisper
     - Actualizar a un plan pago
     - Limitar la duración de videos

## 🔍 Monitoreo y Logs

En el dashboard de Render puedes:
- Ver logs en tiempo real
- Monitorear uso de CPU y memoria
- Configurar alertas
- Ver métricas de requests

## 🛠️ Solución de Problemas

### Error: "Out of Memory"
- Solución: Usa un modelo más pequeño o actualiza el plan

### Error: "Request Timeout"
- Solución: Usa el endpoint asíncrono `/transcribe` en lugar del síncrono

### Error: "ffmpeg not found"
- Solución: Asegúrate de usar el Dockerfile proporcionado

## 📝 Variables de Entorno (Opcional)

Puedes configurar estas en Render Dashboard:

```env
WHISPER_MODEL=base     # tiny, base, small, medium, large
PORT=10000             # Puerto (Render lo configura automáticamente)
```

## 🔐 Seguridad

Para producción, considera agregar:
- Autenticación con API keys
- Rate limiting
- CORS configurado
- Validación de URLs

## 📚 Recursos

- [Documentación de Render](https://docs.render.com)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [Flask Documentation](https://flask.palletsprojects.com)

## 💡 Mejoras Futuras

- [ ] Agregar soporte para múltiples idiomas
- [ ] Implementar cache de resultados
- [ ] Agregar webhook para notificaciones
- [ ] Soporte para subtítulos (SRT/VTT)
- [ ] Integración con almacenamiento en la nube

---

**Nota:** Recuerda que el servicio gratuito de Render se suspende después de 15 minutos de inactividad. La primera request después de la suspensión puede tardar ~30 segundos mientras se reactiva.