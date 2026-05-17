"""
Seed Database for Investor Demo.
Generates 14 days of realistic mock telemetry data so that 
Trend Graphs and Personalized Insights work immediately for the presentation.
"""

import os
import random
from datetime import datetime, timedelta, timezone
import supabase_client as db

def generate_mock_data(days=14):
    print(f"Generating {days} days of mock data for demo...")
    
    # We want to show a clear trend: maybe hydration started bad and got better,
    # or UV had a sudden spike recently.
    
    now = datetime.now(timezone.utc)
    records_inserted = 0
    
    # Generate 3-5 readings per day
    for day_offset in range(days, -1, -1):
        target_date = now - timedelta(days=day_offset)
        num_readings = random.randint(3, 5)
        
        for i in range(num_readings):
            # Calculate a time within that day
            reading_time = target_date.replace(
                hour=random.randint(8, 20), 
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )
            
            # Let's create a narrative:
            # Older data (days 14 to 7): Low hydration (30-45%), Moderate UV (2-4)
            # Newer data (days 6 to 0): Improving hydration (45-65%), Higher UV (4-7)
            
            if day_offset > 7:
                h = random.uniform(30.0, 45.0)
                u = random.uniform(2.0, 4.0)
            else:
                h = random.uniform(45.0, 65.0)
                u = random.uniform(4.0, 7.0)
                
            # Score formula: H * (1 - U/10)
            score = h * (1.0 - (u / 10.0))
            score = max(0.0, min(100.0, score))
            
            # Simplified state logic for seed
            if u > 6:
                state = "UV-Stressed"
            elif h < 35:
                state = "Barrier-Compromised"
            elif h < 45:
                state = "Dehydrated"
            elif u > 4 and h < 50:
                state = "At-Risk"
            else:
                state = "Optimal"
                
            # Insert directly via Supabase client, specifying created_at
            try:
                data, _ = db.supabase.table("telemetry_readings").insert({
                    "hydration": round(h, 1),
                    "uv_index": round(u, 1),
                    "skin_score": round(score, 1),
                    "state": state,
                    "created_at": reading_time.isoformat()
                }).execute()
                records_inserted += 1
            except Exception as e:
                print(f"Error inserting record: {e}")

    print(f"Successfully seeded {records_inserted} historical records!")
    print("Refresh your dashboard to see Trends and Insights.")

if __name__ == "__main__":
    # Ensure tables exist (they should if you've run the app)
    generate_mock_data(14)
