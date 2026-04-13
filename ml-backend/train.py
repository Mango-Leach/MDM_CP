import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
import joblib
import os

def train_model():
    print("Loading actual Kaggle Sephora Dataset...")
    df = pd.read_csv('dataset_1/product_info.csv')
    
    # Filter only skincare to speed up Apriori
    df = df[df['primary_category'] == 'Skincare'].dropna(subset=['ingredients']).copy()
    
    print("Formatting variables mapping ingredients to LSH-UV physiological states...")
    
    # Text search in ingredients
    df['has_Ceramides'] = df['ingredients'].str.contains('ceramide', case=False, na=False).astype(int)
    df['has_HyaluronicAcid'] = df['ingredients'].str.contains('hyaluron', case=False, na=False).astype(int)
    df['has_SPF'] = df['ingredients'].str.contains('zinc oxide|titanium dioxide|octinoxate|avobenzone', case=False, na=False).astype(int)
    df['has_Aloe'] = df['ingredients'].str.contains('aloe', case=False, na=False).astype(int)
    df['has_Niacinamide'] = df['ingredients'].str.contains('niacinamide', case=False, na=False).astype(int)
    df['has_SalicylicAcid'] = df['ingredients'].str.contains('salicylic', case=False, na=False).astype(int)

    # Correlate these ingredients to "States"
    df['state_Dehydrated'] = ((df['has_Ceramides'] == 1) | (df['has_HyaluronicAcid'] == 1)).astype(int)
    df['state_UV-Stressed'] = ((df['has_SPF'] == 1) | (df['has_Aloe'] == 1) | (df['has_Niacinamide'] == 1)).astype(int)
    df['state_Optimal'] = ((df['has_Niacinamide'] == 1) | (df['has_HyaluronicAcid'] == 1)).astype(int)

    # Prepare boolean basket for mlxtend
    features = ['state_Dehydrated', 'state_UV-Stressed', 'state_Optimal'] + \
               [col for col in df.columns if col.startswith('has_')]
    
    basket = df[features].astype(bool)
    
    print(f"Baskets prepared with {len(basket)} actual Sephora skincare products.")
    print("Running Apriori algorithm to discover frequent itemsets...")
    frequent_itemsets = apriori(basket, min_support=0.05, use_colnames=True)
    
    print("Generating association rules...")
    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)
    
    print("Saving ML artifacts...")
    os.makedirs('models', exist_ok=True)
    joblib.dump(rules, 'models/association_rules.pkl')
    
    # Save a minimal catalog for fast queries
    catalog = df[['product_name', 'brand_name'] + features].rename(columns={'brand_name': 'brand'})
    catalog.to_pickle('models/product_catalog.pkl')
    
    print("Training complete! Models saved to /models")

if __name__ == "__main__":
    train_model()
