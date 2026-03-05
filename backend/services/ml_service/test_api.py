import requests
import json
import os

BASE_URL = "http://localhost:8004"
IMAGE_PATH = "datasets/samples/dummy_fundus.jpg"

def test_health():
    print("Testing /health...")
    resp = requests.get(f"{BASE_URL}/health")
    print(f"Status: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2))
    print()

def test_predict():
    print("Testing /predict/pathology...")
    if not os.path.exists(IMAGE_PATH):
        print(f"File not found: {IMAGE_PATH}")
        return
        
    with open(IMAGE_PATH, 'rb') as f:
        files = {'file': ('dummy_fundus.jpg', f, 'image/jpeg')}
        resp = requests.post(f"{BASE_URL}/predict/pathology", files=files)
        
    print(f"Status: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2))
    print()

def test_explain():
    print("Testing /explain/pathology (Grad-CAM)...")
    with open(IMAGE_PATH, 'rb') as f:
        files = {'file': ('dummy_fundus.jpg', f, 'image/jpeg')}
        resp = requests.post(f"{BASE_URL}/explain/pathology", files=files)
        
    print(f"Status: {resp.status_code}")
    data = resp.json()
    if 'heatmap_base64' in data:
        data['heatmap_base64'] = data['heatmap_base64'][:50] + "... [TRUNCATED]"
    print(json.dumps(data, indent=2))
    print()

if __name__ == "__main__":
    test_health()
    test_predict()
    test_explain()
