#!/bin/bash

echo "🚀 Iniciando transcripción..."

# Iniciar y guardar respuesta en archivo
curl -s -X POST https://transcript-mu0r.onrender.com/transcribe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://d5tow79zpi0qo.cloudfront.net/bcef4b8f-9930-49bb-9414-dc92aad2ec02-BAD+BOYS+FOR+LIFE+CLIP+LAT+3.mp4"}' > response.json

cat response.json
echo ""

# Extraer task_id con grep y cut
TASK_ID=$(grep -o '"task_id":"[^"]*' response.json | cut -d'"' -f4)
echo "📝 Task ID: $TASK_ID"

# Esperar y verificar
echo "⏳ Esperando 20 segundos..."
sleep 20

echo "📊 Verificando estado..."
curl "https://transcript-mu0r.onrender.com/status/$TASK_ID"
echo ""

echo "💡 Si el status es 'completed', puedes ver el resultado en:"
echo "https://transcript-mu0r.onrender.com/result/$TASK_ID"