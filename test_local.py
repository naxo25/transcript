#!/usr/bin/env python3
"""
Script para probar la API localmente antes de subir a Render
"""

import requests
import time
import json

# URL base (cambiar cuando esté en Render)
BASE_URL = "http://localhost:10000"  # Local
# BASE_URL = "https://tu-app.onrender.com"  # Render

def test_health():
    """Probar endpoint de salud"""
    print("🔍 Probando /health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_async_transcription(video_url):
    """Probar transcripción asíncrona"""
    print(f"\n📹 Iniciando transcripción de: {video_url}")
    
    # 1. Iniciar transcripción
    print("1️⃣ Enviando request...")
    response = requests.post(
        f"{BASE_URL}/transcribe",
        json={"url": video_url}
    )
    
    if response.status_code != 202:
        print(f"❌ Error al iniciar: {response.text}")
        return
    
    data = response.json()
    task_id = data["task_id"]
    print(f"✅ Tarea creada: {task_id}")
    
    # 2. Verificar estado
    print("2️⃣ Verificando estado...")
    max_attempts = 60  # Máximo 5 minutos
    attempts = 0
    
    while attempts < max_attempts:
        response = requests.get(f"{BASE_URL}/status/{task_id}")
        status_data = response.json()
        status = status_data["status"]
        message = status_data.get("message", "")
        
        print(f"   Status: {status} - {message}")
        
        if status == "completed":
            print("✅ Transcripción completada!")
            break
        elif status == "error":
            print(f"❌ Error: {status_data.get('error')}")
            return
        
        time.sleep(5)  # Esperar 5 segundos
        attempts += 1
    
    if attempts >= max_attempts:
        print("⏱️ Timeout esperando la transcripción")
        return
    
    # 3. Obtener resultado
    print("3️⃣ Obteniendo resultado...")
    response = requests.get(f"{BASE_URL}/result/{task_id}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n📝 TRANSCRIPCIÓN:")
        print("="*50)
        print(result["transcription"])
        print("="*50)
    else:
        print(f"❌ Error obteniendo resultado: {response.text}")

def test_sync_transcription(video_url):
    """Probar transcripción síncrona (para videos cortos)"""
    print(f"\n⚡ Probando transcripción síncrona de: {video_url}")
    print("⏳ Esto puede tardar varios minutos...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/transcribe-sync",
            json={"url": video_url},
            timeout=300  # 5 minutos timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n📝 TRANSCRIPCIÓN:")
            print("="*50)
            print(result["transcription"])
            print("="*50)
        else:
            print(f"❌ Error: {response.text}")
    except requests.Timeout:
        print("⏱️ Timeout - considera usar el endpoint asíncrono")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Video de prueba (corto)
    TEST_VIDEO = "https://d5tow79zpi0qo.cloudfront.net/bcef4b8f-9930-49bb-9414-dc92aad2ec02-BAD+BOYS+FOR+LIFE+CLIP+LAT+3.mp4"
    
    print("🚀 PRUEBA DE API DE TRANSCRIPCIÓN")
    print("="*50)
    
    # Verificar salud
    if not test_health():
        print("\n⚠️ El servidor no responde. Asegúrate de que esté ejecutándose:")
        print("  python app.py")
        exit(1)
    
    # Menú de pruebas
    print("\n¿Qué deseas probar?")
    print("1. Transcripción asíncrona (recomendado)")
    print("2. Transcripción síncrona (videos cortos)")
    print("3. Ambas")
    
    choice = input("\nOpción (1/2/3): ").strip()
    
    if choice == "1":
        test_async_transcription(TEST_VIDEO)
    elif choice == "2":
        test_sync_transcription(TEST_VIDEO)
    elif choice == "3":
        test_async_transcription(TEST_VIDEO)
        test_sync_transcription(TEST_VIDEO)
    else:
        print("Opción inválida")
    
    print("\n✅ Pruebas completadas!")