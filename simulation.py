import requests
import json
import threading
import time
from ucimlrepo import fetch_ucirepo

# 1. Fetch the CDC Diabetes Health Indicators Dataset
print("Fetching CDC Dataset...")
cdc_diabetes_health_indicators = fetch_ucirepo(id=891)
X = cdc_diabetes_health_indicators.data.features
# Convert to dictionary for easy iteration
records = X.to_dict(orient='records')

# 2. Configuration
BROKER_URL = "http://127.0.0.1:5002/"  # Your Local Broker URL
NUM_REQUESTS = 1000  # Total patients to simulate
CONCURRENT_THREADS = 20  # Number of simultaneous IoT devices

def send_request(patient_data, request_id):
    try:
        start_time = time.time()
        response = requests.post(BROKER_URL, json=patient_data)
        latency = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"[Request {request_id}] Success! Broker chose Worker: {result.get('worker_ip')} | Latency: {latency:.4f}s")
        else:
            print(f"[Request {request_id}] Failed with status: {response.status_code}")
    except Exception as e:
        print(f"[Request {request_id}] Error: {e}")

# 3. Simulation Loop
threads = []
print(f"Starting simulation of {NUM_REQUESTS} IoT requests...")

for i in range(NUM_REQUESTS):
    # Select a unique patient record from the dataset
    patient = records[i % len(records)]
    
    t = threading.Thread(target=send_request, args=(patient, i))
    threads.append(t)
    t.start()

    # Control the rate of "injection"
    if len(threads) >= CONCURRENT_THREADS:
        for t in threads:
            t.join()
        threads = []

print("Simulation Complete.")