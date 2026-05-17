# LSH-UV Node System

The **LSH-UV Node** is an end-to-end hardware and software ecosystem designed to monitor live skin health telemetry (Hydration and UV Index), calculate real-time skin scores, and provide machine-learning-driven skincare product interventions.

## 🚀 Project Overview

The project is split into two main components:
1. **Frontend Web Dashboard (`/investor-demo`)**: A modern, responsive HTML/CSS/JS dashboard that fetches data from the backend to visualize telemetry and display product recommendations.
2. **ML Backend (`/ml-backend`)**: A Python/FastAPI server that processes STM32 sensor data, runs an Apriori Collaborative Filtering Engine for product recommendations, and acts as a bridge between the physical hardware and the web interface.

## 🛠️ Prerequisites

- **Python 3.11+** installed and added to your system `PATH`.
- **Node.js** (optional) for serving the frontend via `npx serve`.
- **STM32 Hardware** connected via USB/Serial, outputting JSON telemetry (e.g., `{"h": 45.2, "u": 5.1}`).

## 📦 Setup & Installation

1. **Set up Python Virtual Environment (Recommended):**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. **Install Backend Dependencies:**
   ```powershell
   cd ml-backend
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Train the ML Models (Optional):**
   *Note: Ensure the required Kaggle dataset is located at `ml-backend/dataset_1/product_info.csv` before running.*
   ```powershell
   python train.py
   ```

## ⚙️ How to Run the Project

To run the complete system, you need to open **three separate terminal windows** and run the following components concurrently.

### Terminal 1: Start the Backend API
This starts the local FastAPI server that processes telemetry data and serves the frontend.
```powershell
cd ml-backend
python api.py
```
*(Runs on `http://0.0.0.0:8000`)*

### Terminal 2: Start the STM32 Serial Bridge
This script captures the real-time data streaming from your STM32 microcontroller and forwards it to the API. Replace `COM11` with your actual device port.
```powershell
cd ml-backend
python serial_bridge.py --port COM11 --baud 115200
```
*(If no hardware is connected, you can run it with mock data using the `--mock` flag).*

### Terminal 3: Start the Frontend Web Dashboard
Serve the web UI locally. 
```powershell
cd investor-demo
npx serve .
```
*(Alternatively, use `python -m http.server 3000`)*

Once running, open the localhost URL (usually `http://localhost:3000`) in your browser and click **"Simulate Hardware Sync" / "Connect to Node"** to view real-time data!

## 📂 Architecture

- `api.py`: FastAPI server handling routes and ML model interfacing.
- `serial_bridge.py`: Python serial reader that captures STM32 data blocks and POSTs them to the FastAPI server.
- `recommender.py / train.py`: The Apriori algorithm backend that manages state classifications (Dehydrated, UV-Stressed, Optimal) and matches them to skincare ingredients.
- `app.js`: Connects the frontend UI dashboard directly to the local backend endpoints seamlessly.
