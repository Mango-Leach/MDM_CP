import joblib
import pandas as pd
import os
from schemas import RecommendedProduct

class SkinRecommender:
    def __init__(self):
        self.rules = None
        self.catalog = None
        self.load_models()

    def load_models(self):
        try:
            if os.path.exists('models/association_rules.pkl') and os.path.exists('models/product_catalog.pkl'):
                self.rules = joblib.load('models/association_rules.pkl')
                self.catalog = pd.read_pickle('models/product_catalog.pkl')
                print("ML Models loaded successfully.")
            else:
                print("Warning: Models not found. Please run train.py first.")
        except Exception as e:
            print(f"Error loading models: {e}")

    def get_recommendation(self, skin_state: str, profile: dict = None) -> list[RecommendedProduct]:
        """
        Maps the skin state to ingredients using Apriori rules, 
        then finds products matching those ingredients.
        Filters out products containing any blacklisted allergy ingredients,
        and boosts confidence scores based on skin type and sensitivities.
        """
        profile = profile or {}
        blacklist = profile.get("allergy_ingredients", [])
        skin_type = (profile.get("skin_type") or "").lower()
        sensitivities = [s.lower().strip() for s in profile.get("sensitivities", []) if s]

        # Normalize blacklist to lowercase for case-insensitive matching
        blacklist_lower = [b.lower().strip() for b in blacklist if b]

        if self.rules is None or self.catalog is None:
            # Fallback mock recommendations if not trained
            return [RecommendedProduct(
                product_name="Mock Hydrating Serum",
                brand="Generic",
                key_ingredients=["Glycerin", "Water"],
                match_confidence=0.9
            )]
        
        # State mapping based on Apriori antecedents
        target_antecedent = f"state_{skin_state}"
        
        # Find rules where the antecedent contains our target state
        # In a real apriori setup, antecedents are frozensets
        matching_rules = self.rules[self.rules['antecedents'].apply(lambda x: target_antecedent in x)]
        
        recommended_ingredients = set()
        for consec in matching_rules['consequents']:
            for item in consec:
                if item.startswith("has_"):
                    recommended_ingredients.add(item)
                    
        if not recommended_ingredients:
            # Default fallback if state doesn't have a strong rule
            return []

        # Find products in catalog that have these ingredients
        best_matches = []
        for idx, row in self.catalog.iterrows():
            # Check allergy blacklist — skip product if it contains a blacklisted ingredient
            if blacklist_lower and 'ingredients' in row.index:
                product_ingredients = str(row.get('ingredients', '')).lower()
                if any(allergen in product_ingredients for allergen in blacklist_lower):
                    continue

            match_score = 0
            for ing in recommended_ingredients:
                if row[ing] == 1:
                    match_score += 1
            
            if match_score > 0:
                confidence = match_score / len(recommended_ingredients)
                
                # --- Profile Boosting Logic ---
                text_to_search = f"{row.get('product_name', '')} {row.get('ingredients', '')}".lower()
                
                # 1. Boost if product matches skin type
                if skin_type and skin_type in text_to_search:
                    confidence += 0.15
                    
                # 2. Boost based on sensitivities
                if 'sun' in sensitivities and ('spf' in text_to_search or 'sunscreen' in text_to_search):
                    confidence += 0.20
                if 'wind' in sensitivities and ('ceramide' in text_to_search or 'barrier' in text_to_search):
                    confidence += 0.15
                    
                confidence = min(1.0, confidence) # Cap at 100%
                
                best_matches.append(RecommendedProduct(
                    product_name=row['product_name'],
                    brand=row['brand'],
                    key_ingredients=[i.replace("has_", "") for i in recommended_ingredients],
                    match_confidence=round(confidence, 2)
                ))
        
        # Sort by confidence
        return sorted(best_matches, key=lambda x: x.match_confidence, reverse=True)[:3]

# Singleton instance
recommender_system = SkinRecommender()
