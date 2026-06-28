import pandas as pd
import numpy as np
import random
import os

def generate_mock_ratings():
    print("Generating simulated user ratings...")
    
    # 1. Read existing POIs
    if not os.path.exists("pune_pois.csv"):
        # If running from workspace root, check backend/
        if os.path.exists("backend/pune_pois.csv"):
            pois_df = pd.read_csv("backend/pune_pois.csv")
            output_path = "backend/user_ratings.csv"
        else:
            print("Error: pune_pois.csv not found!")
            return
    else:
        pois_df = pd.read_csv("pune_pois.csv")
        output_path = "user_ratings.csv"

    poi_ids = pois_df['id'].tolist()
    pois_by_type = {
        'historic': pois_df[pois_df['type'] == 'historic']['id'].tolist(),
        'museum': pois_df[pois_df['type'] == 'museum']['id'].tolist(),
        'leisure': pois_df[pois_df['type'] == 'leisure']['id'].tolist(),
        'tourism': pois_df[pois_df['type'] == 'tourism']['id'].tolist(),
    }
    
    # Define indoor and outdoor POIs
    indoor_ids = pois_df[pois_df['is_indoor'] == True]['id'].tolist()
    outdoor_ids = pois_df[pois_df['is_indoor'] == False]['id'].tolist()

    # 2. Define user profiles for realistic clusters
    # We will generate 200 users, split into 3 distinct taste profiles
    num_users = 200
    ratings_data = []

    random.seed(42)
    np.random.seed(42)

    for user_num in range(1, num_users + 1):
        user_id = f"user_{user_num:03d}"
        profile = random.choice(["history_buff", "nature_explorer", "shopping_museum"])
        
        # Number of items this user will rate (between 8 and 20)
        num_ratings = random.randint(8, 20)
        rated_pois = set()

        for _ in range(num_ratings):
            # Select POI based on user profile preferences
            if profile == "history_buff":
                # High probability of historic POIs
                if random.random() < 0.65 and pois_by_type['historic']:
                    poi_id = random.choice(pois_by_type['historic'])
                    rating = random.choices([5, 4, 3, 2, 1], weights=[0.5, 0.3, 0.1, 0.05, 0.05])[0]
                else:
                    poi_id = random.choice(poi_ids)
                    rating = random.choices([5, 4, 3, 2, 1], weights=[0.1, 0.2, 0.4, 0.2, 0.1])[0]
            
            elif profile == "nature_explorer":
                # High probability of outdoor/leisure POIs (forts, lakes, parks)
                outdoor_leisure = list(set(pois_by_type['leisure'] + pois_by_type['historic']) & set(outdoor_ids))
                if random.random() < 0.70 and outdoor_leisure:
                    poi_id = random.choice(outdoor_leisure)
                    rating = random.choices([5, 4, 3, 2, 1], weights=[0.6, 0.25, 0.1, 0.03, 0.02])[0]
                else:
                    poi_id = random.choice(poi_ids)
                    rating = random.choices([5, 4, 3, 2, 1], weights=[0.05, 0.15, 0.4, 0.25, 0.15])[0]
            
            else: # shopping_museum
                # High probability of indoor places (malls, museums, cafe hopping)
                indoor_places = list(set(pois_by_type['museum'] + pois_by_type['leisure']) & set(indoor_ids))
                if random.random() < 0.70 and indoor_places:
                    poi_id = random.choice(indoor_places)
                    rating = random.choices([5, 4, 3, 2, 1], weights=[0.55, 0.3, 0.1, 0.03, 0.02])[0]
                else:
                    poi_id = random.choice(poi_ids)
                    rating = random.choices([5, 4, 3, 2, 1], weights=[0.1, 0.2, 0.3, 0.3, 0.1])[0]

            if poi_id not in rated_pois:
                rated_pois.add(poi_id)
                ratings_data.append({
                    "user_id": user_id,
                    "poi_id": poi_id,
                    "rating": rating
                })

    df = pd.DataFrame(ratings_data)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} ratings across {num_users} users.")
    print(f"Saved dataset to {output_path}")

if __name__ == "__main__":
    generate_mock_ratings()
