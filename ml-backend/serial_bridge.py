import serial
import requests
import time
import json
import argparse
import random

# Default API URL
API_URL = "http://localhost:8000/api/telemetry"

def generate_dummy_payload():
    scenarios = [
        {"h": 30.5, "u": 8.5},
        {"h": 85.0, "u": 1.2},
        {"h": 20.0, "u": 2.1}
    ]
    data = random.choice(scenarios)
    return json.dumps(data)

def start_bridge(port, baudrate, use_mock=False):
    ser = None
    if not use_mock:
        try:
            ser = serial.Serial(port, baudrate, timeout=1)
            print(f"Connected to real STM32 on {port} at {baudrate} baud.")
        except serial.SerialException as e:
            print(f"Failed to connect to Serial Port {port}: {e}")
            print("Falling back to MOCK mode for investor presentation...")
            use_mock = True

    print(f"Forwarding serial telemetry to {API_URL} ...\nWaiting for data...\n")

    while True:
        try:
            line = ""
            if use_mock:
                line = generate_dummy_payload()
                time.sleep(5) # Emit new data every 5 seconds
            else:
                if ser and ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
            
            if line:
                # Expected format from STM32: {"h": 45.2, "u": 5.1}
                if line.startswith("{") and line.endswith("}"):
                    try:
                        data = json.loads(line)
                        payload = {
                            "raw_hydration": data.get("h", 0.0),
                            "raw_uv": data.get("u", 0.0)
                        }
                        
                        response = requests.post(API_URL, json=payload)
                        if response.status_code == 200:
                            print(f"[Success] State Detected: {response.json().get('state_detected')} | Score: {response.json().get('skin_score')}")
                        else:
                            print(f"[Error] Backend returned {response.status_code}: {response.text}")
                            
                    except json.JSONDecodeError:
                        print(f"[Parse Error] Raw line not valid JSON: {line}")
                else:
                    print(f"STM32 Log: {line}")
                    
        except KeyboardInterrupt:
            print("\nShutting down bridge.")
            if ser:
                ser.close()
            break
        except Exception as e:
            print(f"Bridge exception: {e}")
            time.sleep(2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="STM32 to FastAPI Serial Bridge")
    parser.add_argument("--port", type=str, default="COM3", help="Serial port (e.g., COM3 or /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument("--mock", action="store_true", help="Force mock data generation without hardware")
    args = parser.parse_args()
    
    start_bridge(args.port, args.baud, args.mock)
