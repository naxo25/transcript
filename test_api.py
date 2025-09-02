import requests
import time
import json

# 1. Iniciar transcripción
print("🚀 Iniciando transcripción...")
response = requests.post(
    "https://transcript-mu0r.onrender.com/transcribe",
    json={"url": "https://d5tow79zpi0qo.cloudfront.net/bcef4b8f-9930-49bb-9414-dc92aad2ec02-BAD+BOYS+FOR+LIFE+CLIP+LAT+3.mp4"}
)

print(f"Respuesta: {response.text}")

if response.status_code != 202:
    print(f"❌ Error: {response.text}")
    exit()

data = response.json()
task_id = data["task_id"]
print(f"✅ Task ID: {task_id}")

# 2. Verificar estado cada 5 segundos
while True:
    status_response = requests.get(f"https://transcript-mu0r.onrender.com/status/{task_id}")
    status = status_response.json()
    print(f"📊 Estado: {status['status']} - {status.get('message', '')}")
    
    if status['status'] == 'completed':
        print("✅ ¡Completado!")
        break
    elif status['status'] == 'error':
        print(f"❌ Error: {status.get('error')}")
        break
    
    time.sleep(5)

# 3. Obtener resultado
if status['status'] == 'completed':
    result_response = requests.get(f"https://transcript-mu0r.onrender.com/result/{task_id}")
    result = result_response.json()
    print("\n📝 TRANSCRIPCIÓN:")
    print("="*50)
    print(result['transcription'])
    print("="*50)