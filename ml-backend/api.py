from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import TelemetryPayload, RecommendationResponse
from recommender import recommender_system

app = FastAPI(title="LSH-UV Node ML Backend", version="1.0.0")

# Allow Web UI to fetch from backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Attempt to reload models in case train.py was run after server start
    recommender_system.load_models()

# Store the latest broadcasted state for the Web UI to poll
latest_state_cache = None

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "LSH-UV ML Backend API"}

@app.get("/api/latest")
def get_latest_telemetry():
    """Real final version UI natively polls this endpoint to get live hardware data"""
    if not latest_state_cache:
        return {"status": "waiting"}
    return {"status": "active", "data": latest_state_cache}

@app.post("/api/telemetry", response_model=RecommendationResponse)
def process_telemetry(payload: TelemetryPayload):
    """
    Receives strictly raw sensor values from STM32,
    calculates Skin Score, and determines the state dynamically.
    """
    global latest_state_cache
    
    # 1. PDR Mathematical Algorithm: Score = (w1 * H) - (w2 * U)
    w1 = 1.0 # Hydration Weight
    w2 = 2.0 # UV Penalty Weight
    
    calculated_score = (w1 * payload.raw_hydration) - (w2 * payload.raw_uv)
    
    # Keep score between 0 and 100
    calculated_score = max(0.0, min(100.0, calculated_score)) 
    
    # 2. State Classification Logic (Moved from Edge MCU to Backend)
    if payload.raw_uv >= 5.0:
        state = "UV-Stressed"
    elif payload.raw_hydration <= 40.0:
        state = "Dehydrated"
    else:
        state = "Optimal"
    
    # 3. Query Apriori
    products = recommender_system.get_recommendation(state)
    
    response_payload = RecommendationResponse(
        state_detected=state,
        skin_score=calculated_score,
        recommendations=products
    )
    
    # Update cache for UI
    latest_state_cache = {
        "hydration_percentage": payload.raw_hydration,
        "uv_index": payload.raw_uv,
        "skin_score": round(calculated_score, 1),
        "state_detected": state,
        "recommendations": [p.model_dump() for p in products]
    }
    
    return response_payload

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
