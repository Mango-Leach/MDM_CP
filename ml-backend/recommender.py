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

    def get_recommendation(self, skin_state: str) -> list[RecommendedProduct]:
        """
        Maps the skin state to ingredients using Apriori rules, 
        then finds products matching those ingredients.
        """
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
            match_score = 0
            for ing in recommended_ingredients:
                if row[ing] == 1:
                    match_score += 1
            
            if match_score > 0:
                confidence = match_score / len(recommended_ingredients)
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
