from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from schemas import TelemetryPayload, RecommendationResponse
from recommender import recommender_system
import supabase_client as db
from weather_service import get_uv_forecast
from personalization import compute_user_baseline, detect_trends, classify_state_personalized

app = FastAPI(title="LSH-UV Node ML Backend", version="2.0.0")

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


# ─── Pydantic models for new endpoints ────────────────────────────────────────

class SkinProfilePayload(BaseModel):
    skin_type: Optional[str] = None
    age: Optional[int] = None
    sensitivities: Optional[List[str]] = None
    allergy_ingredients: Optional[List[str]] = None


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "LSH-UV ML Backend API", "version": "2.0.0"}


@app.get("/api/latest")
def get_latest_telemetry():
    """Real final version UI natively polls this endpoint to get live hardware data"""
    data = db.get_latest_reading()
    if not data:
        return {"status": "waiting"}
    return {"status": "active", "data": data}


@app.post("/api/telemetry", response_model=RecommendationResponse)
def process_telemetry(payload: TelemetryPayload):
    """
    Receives strictly raw sensor values from STM32,
    calculates Skin Score, and determines the state dynamically.
    Now persists every reading to Supabase.
    """
    # 1. PDR Mathematical Algorithm: Score = (w1 * H) - (w2 * U)
    w1 = 1.0 # Hydration Weight
    w2 = 2.0 # UV Penalty Weight
    
    calculated_score = payload.raw_hydration * (1 - payload.raw_uv / 10)
    
    # Keep score between 0 and 100
    calculated_score = max(0.0, min(100.0, calculated_score)) 
    
    # 2. State Classification — uses personalized baseline when enough data exists
    baseline = compute_user_baseline(days=30)
    state = classify_state_personalized(payload.raw_hydration, payload.raw_uv, baseline)
    
    # 3. Query Apriori (with full profile constraints)
    profile = db.get_skin_profile()
    products = recommender_system.get_recommendation(state, profile=profile)
    
    response_payload = RecommendationResponse(
        state_detected=state,
        skin_score=calculated_score,
        recommendations=products
    )
    
    # 4. Persist to Supabase
    reading = db.insert_reading(
        hydration=payload.raw_hydration,
        uv_index=payload.raw_uv,
        skin_score=round(calculated_score, 1),
        state=state
    )
    if reading:
        db.insert_recommendations(
            reading_id=reading["id"],
            products=[p.model_dump() for p in products]
        )
    
    return response_payload


# ─── History & Profile Endpoints ──────────────────────────────────────────────

@app.get("/api/history")
def get_telemetry_history(days: int = 7):
    """Return telemetry readings for the last N days (for trend graphs)."""
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="days must be between 1 and 365")
    readings = db.get_readings_history(days=days)
    return {"count": len(readings), "readings": readings}


@app.get("/api/profile")
def get_profile():
    """Return the current skin profile."""
    profile = db.get_skin_profile()
    if not profile:
        return {"status": "not_set", "profile": None}
    return {"status": "active", "profile": profile}


@app.post("/api/profile")
def update_profile(payload: SkinProfilePayload):
    """Create or update the skin profile."""
    result = db.upsert_skin_profile(
        skin_type=payload.skin_type,
        age=payload.age,
        sensitivities=payload.sensitivities,
        allergy_ingredients=payload.allergy_ingredients
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to update profile in database")
    return {"status": "updated", "profile": result}


# ─── Insights & Personalization ───────────────────────────────────────────────

@app.get("/api/insights")
def get_insights(days: int = 7):
    """Return trend analysis and personalized insights."""
    baseline = compute_user_baseline(days=30)
    trends = detect_trends(days=days)
    return {
        "baseline": baseline,
        "trends": trends,
        "period_days": days,
    }


# ─── UV Forecast ──────────────────────────────────────────────────────────────

@app.get("/api/uv-forecast")
async def uv_forecast(lat: float = 28.6139, lon: float = 77.2090):
    """Get hourly UV forecast from Tomorrow.io. Defaults to New Delhi coordinates."""
    forecast = await get_uv_forecast(lat, lon)
    if "error" in forecast:
        raise HTTPException(status_code=502, detail=forecast["error"])
    return forecast


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
