"""
Supabase client wrapper for the LSH-UV backend.
Handles all database operations: telemetry persistence, history queries, and skin profiles.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# Load .env from project root (one level up from ml-backend)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("WARNING: SUPABASE_URL or SUPABASE_KEY not set. Database features disabled.")
    supabase: Client = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"Supabase client initialized for: {SUPABASE_URL}")


# ─── Telemetry ────────────────────────────────────────────────────────────────

def insert_reading(hydration: float, uv_index: float, skin_score: float, state: str) -> dict | None:
    """Insert a single telemetry reading and return the created row."""
    if not supabase:
        return None
    try:
        result = supabase.table("telemetry_readings").insert({
            "hydration": hydration,
            "uv_index": uv_index,
            "skin_score": skin_score,
            "state": state,
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"[Supabase] Error inserting reading: {e}")
        return None


def insert_recommendations(reading_id: int, products: list[dict]) -> None:
    """Insert recommendation rows linked to a telemetry reading."""
    if not supabase or not products:
        return
    try:
        rows = [
            {
                "reading_id": reading_id,
                "product_name": p["product_name"],
                "brand": p["brand"],
                "key_ingredients": p["key_ingredients"],
                "match_confidence": p["match_confidence"],
            }
            for p in products
        ]
        supabase.table("recommendations").insert(rows).execute()
    except Exception as e:
        print(f"[Supabase] Error inserting recommendations: {e}")


def get_latest_reading() -> dict | None:
    """Fetch the most recent telemetry reading with its recommendations."""
    if not supabase:
        return None
    try:
        result = (
            supabase.table("telemetry_readings")
            .select("*, recommendations(*)")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            row = result.data[0]
            return {
                "hydration_percentage": row["hydration"],
                "uv_index": row["uv_index"],
                "skin_score": row["skin_score"],
                "state_detected": row["state"],
                "timestamp": row["created_at"],
                "recommendations": [
                    {
                        "product_name": r["product_name"],
                        "brand": r["brand"],
                        "key_ingredients": r["key_ingredients"],
                        "match_confidence": r["match_confidence"],
                    }
                    for r in row.get("recommendations", [])
                ],
            }
        return None
    except Exception as e:
        print(f"[Supabase] Error fetching latest: {e}")
        return None


def get_readings_history(days: int = 7) -> list[dict]:
    """Fetch telemetry readings from the last N days for trend graphs."""
    if not supabase:
        return []
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        result = (
            supabase.table("telemetry_readings")
            .select("created_at, hydration, uv_index, skin_score, state")
            .gte("created_at", cutoff)
            .order("created_at", desc=False)
            .execute()
        )
        return result.data if result.data else []
    except Exception as e:
        print(f"[Supabase] Error fetching history: {e}")
        return []


# ─── Skin Profile ─────────────────────────────────────────────────────────────

def get_skin_profile() -> dict | None:
    """Get the current skin profile (single-user mode: always row id=1)."""
    if not supabase:
        return None
    try:
        result = (
            supabase.table("skin_profile")
            .select("*")
            .order("id", desc=False)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"[Supabase] Error fetching profile: {e}")
        return None


def upsert_skin_profile(skin_type: str = None, age: int = None,
                         sensitivities: list[str] = None,
                         allergy_ingredients: list[str] = None) -> dict | None:
    """Create or update the skin profile."""
    if not supabase:
        return None
    try:
        existing = get_skin_profile()
        payload = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if skin_type is not None:
            payload["skin_type"] = skin_type
        if age is not None:
            payload["age"] = age
        if sensitivities is not None:
            payload["sensitivities"] = sensitivities
        if allergy_ingredients is not None:
            payload["allergy_ingredients"] = allergy_ingredients

        if existing:
            result = (
                supabase.table("skin_profile")
                .update(payload)
                .eq("id", existing["id"])
                .execute()
            )
        else:
            result = supabase.table("skin_profile").insert(payload).execute()

        return result.data[0] if result.data else None
    except Exception as e:
        print(f"[Supabase] Error upserting profile: {e}")
        return None
