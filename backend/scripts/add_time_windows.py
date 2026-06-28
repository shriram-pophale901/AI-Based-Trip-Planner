import pandas as pd
import os

def add_time_windows():
    print("Augmenting pune_pois.csv with opening/closing hours...")
    
    csv_path = "pune_pois.csv"
    if not os.path.exists(csv_path) and os.path.exists("backend/pune_pois.csv"):
        csv_path = "backend/pune_pois.csv"
        
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found!")
        return

    df = pd.read_csv(csv_path)
    
    opening_times = []
    closing_times = []
    
    for _, row in df.iterrows():
        poi_type = str(row['type']).lower()
        poi_name = str(row['name']).lower()
        
        # Default fallback values
        open_t = "09:00"
        close_t = "18:00"
        
        if "mall" in poi_name or "market" in poi_name or "shopping" in poi_name:
            open_t = "11:00"
            close_t = "21:30"
        elif "water park" in poi_name or "sentosa" in poi_name or "wet n joy" in poi_name or "krushnai" in poi_name or "diamond" in poi_name:
            open_t = "10:00"
            close_t = "18:00"
        elif "temple" in poi_name or "mandir" in poi_name or "ganpati" in poi_name or "ashram" in poi_name or "samadhi" in poi_name:
            # Temples open early and close late, sometimes closed in the afternoon but let's keep it simple
            open_t = "06:00"
            close_t = "21:00"
        elif "fort" in poi_name:
            # Forts open very early, close by sunset
            open_t = "07:00"
            close_t = "18:00"
        elif poi_type == "museum":
            open_t = "10:00"
            close_t = "17:30"
        elif poi_type == "historic":
            open_t = "09:00"
            close_t = "18:00"
        elif poi_type == "leisure":
            # Parks and gardens
            open_t = "08:00"
            close_t = "20:00"
        elif poi_type == "tourism":
            open_t = "09:00"
            close_t = "18:30"
            
        opening_times.append(open_t)
        closing_times.append(close_t)
        
    df['opening_time'] = opening_times
    df['closing_time'] = closing_times
    
    df.to_csv(csv_path, index=False)
    print(f"Successfully added time windows to {csv_path}!")

if __name__ == "__main__":
    add_time_windows()
