"""
Personalization engine for LSH-UV.
Computes user-specific baselines from historical data and detects trends.
"""

import supabase_client as db
from datetime import datetime, timedelta, timezone


def compute_user_baseline(days: int = 30) -> dict | None:
    """
    Calculate the user's personal baseline hydration and UV averages
    from the last N days of telemetry data.
    Returns None if insufficient data (< 10 readings).
    """
    readings = db.get_readings_history(days=days)
    
    if len(readings) < 10:
        return None  # Not enough data yet for personalization
    
    hydrations = [r["hydration"] for r in readings]
    uvs = [r["uv_index"] for r in readings]
    scores = [r["skin_score"] for r in readings]
    
    avg_hydration = sum(hydrations) / len(hydrations)
    avg_uv = sum(uvs) / len(uvs)
    avg_score = sum(scores) / len(scores)
    
    # Simple standard deviation
    std_hydration = (sum((h - avg_hydration) ** 2 for h in hydrations) / len(hydrations)) ** 0.5
    std_uv = (sum((u - avg_uv) ** 2 for u in uvs) / len(uvs)) ** 0.5
    
    return {
        "avg_hydration": round(avg_hydration, 1),
        "avg_uv": round(avg_uv, 1),
        "avg_score": round(avg_score, 1),
        "std_hydration": round(std_hydration, 1),
        "std_uv": round(std_uv, 1),
        "total_readings": len(readings),
        "period_days": days,
    }


def detect_trends(days: int = 7) -> list[dict]:
    """
    Compare this period's averages to the previous period and generate
    human-readable insight strings.
    """
    current_readings = db.get_readings_history(days=days)
    previous_readings = db.get_readings_history(days=days * 2)
    
    if len(current_readings) < 3 or len(previous_readings) < 6:
        return [{"type": "info", "message": "Not enough data yet to detect trends. Keep using your device!"}]
    
    # Split previous_readings into the older half
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    older_readings = [
        r for r in previous_readings
        if datetime.fromisoformat(r["created_at"]) < cutoff
    ]
    
    if len(older_readings) < 3:
        return [{"type": "info", "message": "Building your baseline... trends will appear after more readings."}]
    
    insights = []
    
    # Hydration trend
    curr_hydration = sum(r["hydration"] for r in current_readings) / len(current_readings)
    prev_hydration = sum(r["hydration"] for r in older_readings) / len(older_readings)
    hydration_change = ((curr_hydration - prev_hydration) / prev_hydration) * 100 if prev_hydration else 0
    
    if hydration_change < -10:
        insights.append({
            "type": "warning",
            "metric": "hydration",
            "message": f"Your hydration has dropped {abs(hydration_change):.0f}% compared to last {days} days. Increase water intake and moisturizer use.",
            "change_pct": round(hydration_change, 1),
        })
    elif hydration_change > 10:
        insights.append({
            "type": "positive",
            "metric": "hydration",
            "message": f"Great news! Your hydration improved by {hydration_change:.0f}% this period.",
            "change_pct": round(hydration_change, 1),
        })
    
    # UV exposure trend
    curr_uv = sum(r["uv_index"] for r in current_readings) / len(current_readings)
    prev_uv = sum(r["uv_index"] for r in older_readings) / len(older_readings)
    uv_change = ((curr_uv - prev_uv) / prev_uv) * 100 if prev_uv else 0
    
    if uv_change > 20:
        insights.append({
            "type": "warning",
            "metric": "uv_exposure",
            "message": f"Your UV exposure has increased {uv_change:.0f}% — consider adjusting outdoor time or applying stronger sunscreen.",
            "change_pct": round(uv_change, 1),
        })
    
    # Score trend
    curr_score = sum(r["skin_score"] for r in current_readings) / len(current_readings)
    prev_score = sum(r["skin_score"] for r in older_readings) / len(older_readings)
    score_change = curr_score - prev_score
    
    if score_change < -5:
        insights.append({
            "type": "warning",
            "metric": "skin_score",
            "message": f"Your skin score dropped by {abs(score_change):.1f} points. Check your routine for any changes.",
            "change_pct": round(score_change, 1),
        })
    elif score_change > 5:
        insights.append({
            "type": "positive",
            "metric": "skin_score",
            "message": f"Your skin score improved by {score_change:.1f} points — your routine is working!",
            "change_pct": round(score_change, 1),
        })
    
    # State distribution analysis
    state_counts = {}
    for r in current_readings:
        s = r["state"]
        state_counts[s] = state_counts.get(s, 0) + 1
    
    total = len(current_readings)
    for state, count in state_counts.items():
        pct = (count / total) * 100
        if state != "Optimal" and pct > 40:
            insights.append({
                "type": "alert",
                "metric": "state_frequency",
                "message": f"You've been in '{state}' state {pct:.0f}% of the time this period. Consider adjustments.",
                "state": state,
                "frequency_pct": round(pct, 1),
            })
    
    if not insights:
        insights.append({
            "type": "positive",
            "message": "Your skin metrics are stable — looking good! Keep up your current routine.",
        })
    
    return insights


def classify_state_personalized(hydration: float, uv: float, baseline: dict | None) -> str:
    """
    Classify skin state using the user's personal baseline when available.
    Falls back to static thresholds if no baseline exists.
    """
    if not baseline:
        # Static fallback (same as default)
        if uv > 6:
            return "UV-Stressed"
        elif hydration < 25:
            return "Barrier-Compromised"
        elif uv > 4 and hydration < 35:
            return "Inflamed"
        elif hydration < 40:
            return "Dehydrated"
        elif uv > 3 and hydration < 50:
            return "At-Risk"
        else:
            return "Optimal"
    
    # Personalized classification using user's own norms
    avg_h = baseline["avg_hydration"]
    std_h = baseline["std_hydration"]
    avg_uv = baseline["avg_uv"]
    std_uv = baseline["std_uv"]
    
    # UV significantly above user's normal
    if uv > avg_uv + 2 * std_uv or uv > 6:
        return "UV-Stressed"
    # Hydration critically below user's normal
    elif hydration < avg_h - 2 * std_h or hydration < 25:
        return "Barrier-Compromised"
    # Both metrics stressed
    elif uv > avg_uv + std_uv and hydration < avg_h - std_h:
        return "Inflamed"
    # Hydration below user's normal
    elif hydration < avg_h - std_h:
        return "Dehydrated"
    # Borderline
    elif uv > avg_uv + 0.5 * std_uv and hydration < avg_h:
        return "At-Risk"
    else:
        return "Optimal"
