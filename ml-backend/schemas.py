from pydantic import BaseModel
from typing import List, Optional

class TelemetryPayload(BaseModel):
    raw_hydration: float
    raw_uv: float

class RecommendedProduct(BaseModel):
    product_name: str
    brand: str
    key_ingredients: List[str]
    match_confidence: float

class RecommendationResponse(BaseModel):
    state_detected: str
    skin_score: float
    recommendations: List[RecommendedProduct]
