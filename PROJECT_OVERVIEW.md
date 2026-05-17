# LSH-UV Project Overview

## 1. Project Summary
The **LSH-UV (Live Skin Health - UV) Node** is an end-to-end, real-time physiological monitoring and product recommendation system. It simulates continuous tracking of skin hydration and UV exposure, translates those metrics into actionable skin conditions, and dynamically recommends targeted skincare interventions. The project is structured with an embedded hardware bridge interface, a FastAPI ML backend, and a modern JS-driven investor demonstration dashboard.

## 2. Data Flow
The system's data flows linearly from hardware telemetry to user interface:

1. **Telemetry Generation / Edge (`serial_bridge.py`)**: 
   The STM32 hardware node collects hydration and UV index readings. A Python-based serial bridge intercepts these readings (e.g., `{"h": 45.2, "u": 5.1}`). If hardware is disconnected, it defaults to a mock mode generating realistic, randomized dummy payloads.
2. **Telemetry Ingestion & Processing (`api.py`)**: 
   The serial bridge sends an HTTP POST request with the sensor payload to the FastAPI `/api/telemetry` endpoint. The backend processes these raw inputs, calculating a dynamic "Skin Score" and evaluating the "Skin State". It then queries the recommender model and stores this holistic state snapshot in a global cache (`latest_state_cache`).
3. **Client Polling & Visualization (`app.js`)**: 
   When the user activates "Sync" on the investor dashboard UI, it begins polling the `/api/latest` endpoint every 2 seconds. The frontend receives the finalized dataset (hydration, UV, score, state, and recommended products) and selectively updates the DOM with animated metrics and rendered product cards.

## 3. How Everything is Working
The core components collaborate as follows:

* **Scoring & Classification Algorithm**: 
  The backend calculates an overall skin health score out of 100 using a proprietary formula: `Calculated Score = (1.0 * Hydration) - (2.0 * UV)`. 
  * **Where it came from:** This equation is based on the Product Design Requirements (PDR) established for the LSH-UV Node prototype.
  * **Why only this formula:** It functions as a rapid, lightweight heuristic designed to run optimally on low-power edge devices and microcontrollers without requiring heavy compute. It assigns a penalty weight of `2.0` to UV because active UV radiation poses a significantly higher, acute danger to skin cell integrity than standard baseline dehydration (weight `1.0`), ensuring the score plummets aggressively when the user enters dangerous sunlight.
  * Depending on the readings, it classifies the user into states:
    * **UV-Stressed**: `raw_uv >= 5.0`
    * **Dehydrated**: `raw_hydration <= 40.0`
    * **Optimal**: All other stable conditions.
* **Apriori Association Rules (`recommender.py`)**: 
  Based on the classified state, the recommender system uses pre-trained ML association rules to identify the optimal chemical interventions. For example, if a user is `Dehydrated`, the rules determine they need `Ceramides` and `Hyaluronic Acid`. 
* **Product Matching**: 
  The backend queries an internalized product catalog to find retail items possessing those exact recommended ingredients. It calculates a "Match Confidence" based on how many identified ingredients the item has, and supplies the top matches back to the endpoint.
* **Investor UI Elements**: 
  The frontend uses vanilla JS and CSS to render smooth, dynamic updates. SVGs are algorithmically styled to reflect the skin score (circle fill/dash offset), states are color-coded (red/yellow/green alerts), and products smoothly fade in.

## 4. What Datasets are Used and Why
**Dataset Used:** The Kaggle Sephora Product Dataset (`dataset_1/product_info.csv`).

**Why it was used:**
1. **Real-world Ingredient Profiles**: To perform legitimate skincare matching, the system needed a catalog with highly detailed ingredient lists (`ingredients` column). The Sephora dataset is massive and thoroughly tags real products.
2. **Apriori ML Training Capability (`train.py`)**: The data facilitates Market Basket/Association Rule learning. The algorithm maps real Sephora products matching certain ingredients (`Ceramides`, `Aloe`, `SPF`) iteratively to designated skin profiles. It allows the Apriori algorithm to discover genuine functional relationships between cosmetic item ingredients to ensure logical, scientifically plausible recommendations.
3. **Building Demo Credibility**: Presenting recognizable brands and named actual products ensures high confidence during investor demonstrations, compared to mocked or generic item returns.
