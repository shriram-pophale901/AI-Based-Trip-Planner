import recommender
import pandas as pd
import json

def test_personalization():
    print("Testing Personalized Recommender...")
    
    # Let's check a few users
    # In generate_ratings.py:
    # user_001 -> nature_explorer (enjoys outdoor forts, lakes, parks)
    # Let's find a history buff user. Let's inspect some ratings to see user interests.
    ratings_df = pd.read_csv("user_ratings.csv")
    
    # We will query itinerary generation for:
    # 1. user_001 (mapped or actual)
    # 2. user_002
    # 3. None (Guest user)
    
    print("\n--- Day 1 Recommendations for Guest User (Content fallback) ---")
    guest_plan = recommender.generate_itinerary(days=1, budget="mid", group_type="family", user_id=None)
    for day, spots in guest_plan["itinerary"].items():
        print(f"{day}: {[s['name'] for s in spots]}")

    print("\n--- Day 1 Recommendations for User: user_001 ---")
    user1_plan = recommender.generate_itinerary(days=1, budget="mid", group_type="family", user_id="user_001")
    for day, spots in user1_plan["itinerary"].items():
        print(f"{day}: {[s['name'] for s in spots]}")

    print("\n--- Day 1 Recommendations for User: user_002 ---")
    user2_plan = recommender.generate_itinerary(days=1, budget="mid", group_type="family", user_id="user_002")
    for day, spots in user2_plan["itinerary"].items():
        print(f"{day}: {[s['name'] for s in spots]}")

    # Verify if they are different
    spots_guest = [s['name'] for s in guest_plan["itinerary"]["Day 1"]]
    spots_user1 = [s['name'] for s in user1_plan["itinerary"]["Day 1"]]
    spots_user2 = [s['name'] for s in user2_plan["itinerary"]["Day 1"]]
    
    print("\nVerification Results:")
    if spots_user1 != spots_guest:
        print("[SUCCESS] User 1 recommendations differ from Guest recommendations!")
    else:
        print("[FAILED] User 1 and Guest recommendations are identical.")
        
    if spots_user1 != spots_user2:
        print("[SUCCESS] User 1 and User 2 recommendations differ (personalized SVD is active)!")
    else:
        print("[FAILED] User 1 and User 2 recommendations are identical.")

if __name__ == "__main__":
    test_personalization()
