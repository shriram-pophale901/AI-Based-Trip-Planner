import overpy
import pandas as pd
import time

def fetch_pune_pois():
    print("Initializing Overpass API...")
    api = overpy.Overpass()
    
    # Overpass QL query to get tourism, historic, and leisure places in Pune
    query = """
    [out:json];
    area["name"="Pune"]["admin_level"="8"]->.searchArea;
    (
      node["tourism"~"museum|viewpoint|gallery"](area.searchArea);
      way["tourism"~"museum|viewpoint|gallery"](area.searchArea);
      rel["tourism"~"museum|viewpoint|gallery"](area.searchArea);
      node["historic"~"fort|monument"](area.searchArea);
      way["historic"~"fort|monument"](area.searchArea);
      rel["historic"~"fort|monument"](area.searchArea);
      node["leisure"~"park|garden"](area.searchArea);
      way["leisure"~"park|garden"](area.searchArea);
      rel["leisure"~"park|garden"](area.searchArea);
    );
    out center;
    """
    
    print("Fetching data from OSM...")
    try:
        result = api.query(query)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return
    
    places = []
    
    for node in result.nodes:
        name = node.tags.get("name", "Unknown")
        if name == "Unknown":
            continue
        places.append({
            "id": node.id,
            "name": name,
            "type": node.tags.get("tourism") or node.tags.get("historic") or node.tags.get("leisure"),
            "lat": node.lat,
            "lon": node.lon
        })
        
    for way in result.ways:
        name = way.tags.get("name", "Unknown")
        if name == "Unknown":
            continue
        places.append({
            "id": way.id,
            "name": name,
            "type": way.tags.get("tourism") or way.tags.get("historic") or way.tags.get("leisure"),
            "lat": way.center_lat if hasattr(way, 'center_lat') and way.center_lat else None,
            "lon": way.center_lon if hasattr(way, 'center_lon') and way.center_lon else None,
        })
        
    df = pd.DataFrame(places)
    df = df.dropna(subset=['lat', 'lon'])
    
    print(f"Found {len(df)} locations.")
    
    output_file = "pune_pois.csv"
    df.to_csv(output_file, index=False)
    print(f"Data saved to {output_file} successfully.")

if __name__ == "__main__":
    fetch_pune_pois()
