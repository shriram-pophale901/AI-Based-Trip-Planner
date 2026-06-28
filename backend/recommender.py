import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt
import os
import pickle
import hashlib
import random

# Load pre-trained SVD model weights if they exist
SVD_MODEL_PATH = "backend/models/svd_weights.pkl"
if not os.path.exists(SVD_MODEL_PATH) and os.path.exists("models/svd_weights.pkl"):
    SVD_MODEL_PATH = "models/svd_weights.pkl"

svd_weights = None
if os.path.exists(SVD_MODEL_PATH):
    try:
        with open(SVD_MODEL_PATH, "rb") as f:
            svd_weights = pickle.load(f)
        print(f"Successfully loaded SVD weights from {SVD_MODEL_PATH}")
    except Exception as e:
        print(f"Error loading SVD weights: {e}")


def predict_rating(user_id: str, poi_id: str) -> float:
    """Predict rating for user_id and poi_id using custom SVD weights."""
    if svd_weights is None:
        return 3.0
        
    mu = svd_weights["mu"]
    b_u = svd_weights["b_u"]
    b_i = svd_weights["b_i"]
    P = svd_weights["P"]
    Q = svd_weights["Q"]
    
    # Hashing Firebase UIDs to map to mock users for demo purposes
    if user_id not in P:
        h = int(hashlib.md5(user_id.encode('utf-8')).hexdigest(), 16)
        mock_idx = (h % len(P)) + 1
        u_key = f"user_{mock_idx:03d}"
    else:
        u_key = user_id
        
    poi_key = poi_id
    if poi_key not in b_i and str(poi_key) in b_i:
        poi_key = str(poi_key)
    elif poi_key not in b_i and int(poi_key) in b_i:
        poi_key = int(poi_key)
        
    b_u_val = b_u.get(u_key, 0.0)
    b_i_val = b_i.get(poi_key, 0.0)
    p_val = P.get(u_key)
    q_val = Q.get(poi_key)
    
    if p_val is not None and q_val is not None:
        return mu + b_u_val + b_i_val + np.dot(p_val, q_val)
    else:
        return mu + b_u_val + b_i_val

# Average travel time between stops in hours (30 minutes)
TRAVEL_TIME_BUFFER = 0.5


def haversine(lon1, lat1, lon2, lat2):
    """Calculate the great circle distance in km between two GPS points."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return c * 6371


def time_to_minutes(t_str: str) -> int:
    """Convert 'HH:MM' string to minutes since midnight."""
    h, m = map(int, t_str.split(":"))
    return h * 60 + m


def minutes_to_time(mins: int) -> str:
    """Convert minutes since midnight to 'HH:MM' string."""
    mins = int(mins) % 1440
    h = mins // 60
    m = mins % 60
    return f"{h:02d}:{m:02d}"


def ga_tsp_tw(
    places: list,
    start_lat: float,
    start_lon: float,
    start_time_str: str,
    end_time_str: str,
    generations=60,
    pop_size=50,
):
    """
    Genetic Algorithm to solve the Traveling Salesperson Problem with Time Windows (TSP-TW).
    Sorts and filters places to minimize travel distance and respect site opening/closing hours.
    """
    if not places:
        return []

    num_places = len(places)
    start_mins = time_to_minutes(start_time_str)
    end_mins = time_to_minutes(end_time_str)

    # Parse constraints
    for p in places:
        p["open_mins"] = time_to_minutes(p.get("opening_time", "09:00"))
        p["close_mins"] = time_to_minutes(p.get("closing_time", "18:00"))
        p["duration_mins"] = int(float(p.get("avg_time_spent", 1)) * 60)

    # Fitness evaluation function
    def evaluate(individual):
        curr_mins = start_mins
        curr_lat = start_lat
        curr_lon = start_lon
        total_dist = 0.0
        time_violations = 0.0
        
        for idx in individual:
            p = places[idx]
            dist = haversine(curr_lon, curr_lat, p["lon"], p["lat"])
            total_dist += dist
            
            # Speed average: 30 km/h, min 15 minutes travel buffer
            travel_mins = max((dist / 30.0) * 60, 15)
            arrival_mins = curr_mins + travel_mins
            
            visit_start = max(arrival_mins, p["open_mins"])
            visit_end = visit_start + p["duration_mins"]
            
            # Penalty for missing the closing time window
            if visit_end > p["close_mins"]:
                time_violations += (visit_end - p["close_mins"])
                
            curr_mins = visit_end
            curr_lat = p["lat"]
            curr_lon = p["lon"]
            
        fitness = - (total_dist + time_violations * 2.0)
        
        # Penalty for exceeding user's scheduled end of day
        if curr_mins > end_mins:
            fitness -= (curr_mins - end_mins) * 1.5
            
        return fitness

    # Initialize population
    population = [random.sample(range(num_places), num_places) for _ in range(pop_size)]

    # Evolutionary loop
    for _ in range(generations):
        fitness_scores = [evaluate(ind) for ind in population]
        
        # Tournament Selection
        parents = []
        for _ in range(pop_size):
            i1, i2 = random.sample(range(pop_size), 2)
            if fitness_scores[i1] > fitness_scores[i2]:
                parents.append(population[i1])
            else:
                parents.append(population[i2])
                
        # Breed next generation (OX1 Crossover + Elitism)
        next_generation = []
        best_idx = np.argmax(fitness_scores)
        next_generation.append(population[best_idx])
        
        while len(next_generation) < pop_size:
            p1, p2 = random.sample(parents, 2)
            size = num_places
            start, end = sorted(random.sample(range(size), 2))
            
            child = [-1] * size
            child[start:end+1] = p1[start:end+1]
            
            p2_filtered = [item for item in p2 if item not in child[start:end+1]]
            
            curr_child_idx = 0
            for val in p2_filtered:
                while curr_child_idx < size and child[curr_child_idx] != -1:
                    curr_child_idx += 1
                if curr_child_idx < size:
                    child[curr_child_idx] = val
            next_generation.append(child)
            
        # Swap Mutation
        for ind in next_generation[1:]:
            if random.random() < 0.15:
                idx1, idx2 = random.sample(range(num_places), 2)
                ind[idx1], ind[idx2] = ind[idx2], ind[idx1]
                
        population = next_generation

    # Reconstruct optimal sequence
    fitness_scores = [evaluate(ind) for ind in population]
    best_ind = population[np.argmax(fitness_scores)]
    
    route = []
    curr_mins = start_mins
    curr_lat = start_lat
    curr_lon = start_lon
    
    for idx in best_ind:
        p = places[idx].copy()
        dist = haversine(curr_lon, curr_lat, p["lon"], p["lat"])
        travel_mins = max((dist / 30.0) * 60, 15)
        arrival_mins = curr_mins + travel_mins
        
        visit_start = max(arrival_mins, p["open_mins"])
        visit_end = visit_start + p["duration_mins"]
        
        # Stop inserting if arrival is after end of exploration day
        if visit_start >= end_mins:
            break
            
        p["arrival_time"] = minutes_to_time(arrival_mins)
        p["visit_time"] = minutes_to_time(visit_start)
        p["visit_end"] = minutes_to_time(visit_end)
        p["travel_mins"] = int(travel_mins)
        p["wait_mins"] = int(visit_start - arrival_mins)
        
        if visit_end > p["close_mins"]:
            p["time_warning"] = f"Site closing warning: Closes at {p['closing_time']}"
            
        route.append(p)
        
        curr_mins = visit_end
        curr_lat = p["lat"]
        curr_lon = p["lon"]
        
    return route


def proximity_cluster(df: pd.DataFrame, days: int, ref_lat: float, ref_lon: float):
    """
    Greedy proximity-aware day clustering.

    Algorithm
    ---------
    1. Sort all POIs by distance from the reference point (user location).
    2. For each day, seed the cluster with the nearest unassigned POI.
    3. Expand the cluster by adding unassigned POIs nearest to the seed
       that lie within MAX_CLUSTER_RADIUS km — keeping each day geographically tight.
    4. Repeat for subsequent days, so Day 1 is always nearest the user.
    5. Any remaining POIs (outside all cluster radii) are distributed round-robin.
    """
    MAX_CLUSTER_RADIUS = 15  # km — max spread inside a single day's cluster
    MAX_SPOTS_PER_DAY = 14   # hard cap to keep each day manageable

    df = df.copy()
    df["dist_from_ref"] = df.apply(
        lambda r: haversine(ref_lon, ref_lat, r["lon"], r["lat"]), axis=1
    )
    df = df.sort_values("dist_from_ref").reset_index(drop=True)

    assigned = [False] * len(df)
    day_indices = []  # list of lists of df row indices

    for _day in range(days):
        # Seed: nearest unassigned POI
        seed_idx = next((i for i, a in enumerate(assigned) if not a), None)
        if seed_idx is None:
            break
        assigned[seed_idx] = True
        cluster = [seed_idx]
        seed_lat = df.at[seed_idx, "lat"]
        seed_lon = df.at[seed_idx, "lon"]

        # Collect unassigned candidates sorted by distance to seed
        candidates = []
        for i, a in enumerate(assigned):
            if not a:
                d = haversine(seed_lon, seed_lat, df.at[i, "lon"], df.at[i, "lat"])
                candidates.append((d, i))
        candidates.sort()

        for dist, i in candidates:
            if len(cluster) >= MAX_SPOTS_PER_DAY:
                break
            if dist <= MAX_CLUSTER_RADIUS:
                assigned[i] = True
                cluster.append(i)

        day_indices.append(cluster)

    # Distribute any leftover POIs (outside all radii) round-robin across days
    leftover = [i for i, a in enumerate(assigned) if not a]
    for k, i in enumerate(leftover):
        if day_indices:
            day_indices[k % len(day_indices)].append(i)

    return df, day_indices


def generate_itinerary(
    days: int,
    budget: str,
    group_type: str,
    user_lat: float = None,
    user_lon: float = None,
    start_time: str = "09:00",
    end_time: str = "18:00",
    user_id: str = None,
):
    # Adjust path if running in backend directory
    csv_path = "pune_pois.csv"
    if not os.path.exists(csv_path) and os.path.exists("backend/pune_pois.csv"):
        csv_path = "backend/pune_pois.csv"
    df = pd.read_csv(csv_path)

    # 1. Budget Filter
    if budget.lower() == "budget":
        df = df[df["budget_level"] <= 1]
    elif budget.lower() == "luxury":
        df = df[df["budget_level"] >= 1]

    # Fallback if too few places after filtering
    if len(df) < days * 2:
        if not os.path.exists(csv_path) and os.path.exists("backend/pune_pois.csv"):
            csv_path = "backend/pune_pois.csv"
        df = pd.read_csv(csv_path)

    # 2. Collaborative / Content-Based Scoring & Candidate Selection
    scores = []
    for _, row in df.iterrows():
        if user_id:
            score = predict_rating(user_id, row['id'])
        else:
            # Guest fallback: Content-based heuristic weights
            group_weights = {
                "solo": {"historic": 1.2, "museum": 1.2, "leisure": 1.0, "tourism": 0.8},
                "friends": {"leisure": 1.3, "tourism": 1.1, "historic": 1.0, "museum": 0.6},
                "family": {"tourism": 1.3, "leisure": 1.2, "historic": 1.1, "museum": 0.9}
            }
            weights = group_weights.get(group_type.lower(), {"historic": 1.0, "museum": 1.0, "leisure": 1.0, "tourism": 1.0})
            score = weights.get(row['type'], 1.0)
        scores.append(score)
        
    df = df.copy()
    df["rec_score"] = scores
    
    # Sort POIs by score and keep the top K candidates
    K = max(days * 8, 25)
    df = df.sort_values(by="rec_score", ascending=False).head(K).reset_index(drop=True)

    # 2. Reference point (default to Shaniwar Wada if user didn't share location)
    ref_lat = user_lat if user_lat is not None else 18.5204
    ref_lon = user_lon if user_lon is not None else 73.8567

    # 3. Proximity-aware clustering (replaces random K-Means)
    df_sorted, day_indices = proximity_cluster(df, days, ref_lat, ref_lon)

    # Load hotels
    hotels_path = "pune_hotels.csv"
    if not os.path.exists(hotels_path) and os.path.exists("backend/pune_hotels.csv"):
        hotels_path = "backend/pune_hotels.csv"
    hotels_df = pd.read_csv(hotels_path)
    if budget.lower() == "budget":
        hotels_df = hotels_df[hotels_df["price_level"] == "budget"]
    elif budget.lower() == "luxury":
        hotels_df = hotels_df[hotels_df["price_level"] == "luxury"]
    else:
        hotels_df = hotels_df[hotels_df["price_level"] == "mid"]
        
    if len(hotels_df) < 3:
        if not os.path.exists(hotels_path) and os.path.exists("backend/pune_hotels.csv"):
            hotels_path = "backend/pune_hotels.csv"
        hotels_df = pd.read_csv(hotels_path)

    # 5. Build itinerary and find hotels per day
    itinerary = {}
    hotels = {}
    for day_num, indices in enumerate(day_indices, start=1):
        day_df = df_sorted.iloc[indices]
        day_places = day_df.to_dict("records")
        
        # Route using the Genetic Algorithm
        timed = ga_tsp_tw(
            places=day_places,
            start_lat=ref_lat,
            start_lon=ref_lon,
            start_time_str=start_time,
            end_time_str=end_time,
            generations=60,
            pop_size=50
        )
        itinerary[f"Day {day_num}"] = timed

        # Find hotels near the center of today's places
        if len(day_df) > 0:
            center_lat = day_df["lat"].mean()
            center_lon = day_df["lon"].mean()
            day_hotels = hotels_df.copy()
            day_hotels["dist"] = day_hotels.apply(
                lambda r: haversine(center_lon, center_lat, r["lon"], r["lat"]), axis=1
            )
            day_hotels = day_hotels.sort_values("dist").head(3)
            hotels[f"Day {day_num}"] = day_hotels.to_dict("records")
        else:
            hotels[f"Day {day_num}"] = []

    return {"itinerary": itinerary, "hotels": hotels}


if __name__ == "__main__":
    import pprint

    pp = pprint.PrettyPrinter(indent=2)
    plan = generate_itinerary(
        days=3,
        budget="budget",
        group_type="family",
        user_lat=18.5204,
        user_lon=73.8567,
        start_time="09:00",
        end_time="18:00",
    )
    pp.pprint(plan)
