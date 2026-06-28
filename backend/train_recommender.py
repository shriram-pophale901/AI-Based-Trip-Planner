import pandas as pd
import numpy as np
import pickle
import os

def train_svd(ratings_file="user_ratings.csv", model_output="models/svd_weights.pkl", latent_dim=15, epochs=100, lr=0.005, reg=0.02):
    print("Starting SVD training pipeline...")
    
    # Adjust paths if running from workspace root
    if not os.path.exists(ratings_file) and os.path.exists("backend/" + ratings_file):
        ratings_file = "backend/" + ratings_file
        
    model_output_dir = os.path.dirname(model_output)
    if not os.path.exists(model_output) and os.path.exists("backend"):
        model_output = "backend/" + model_output
        model_output_dir = os.path.dirname(model_output)
        
    if model_output_dir and not os.path.exists(model_output_dir):
        os.makedirs(model_output_dir)

    if not os.path.exists(ratings_file):
        print(f"Error: Ratings file {ratings_file} not found. Please run generate_ratings.py first!")
        return

    # Load ratings
    df = pd.read_csv(ratings_file)
    print(f"Loaded {len(df)} ratings.")

    # Unique users and items
    users = df['user_id'].unique()
    pois = df['poi_id'].unique()
    
    num_users = len(users)
    num_pois = len(pois)
    
    print(f"Unique Users: {num_users}, Unique POIs: {num_pois}")

    # Build mappings
    user_to_idx = {uid: idx for idx, uid in enumerate(users)}
    poi_to_idx = {pid: idx for idx, pid in enumerate(pois)}
    
    idx_to_user = {idx: uid for uid, idx in user_to_idx.items()}
    idx_to_poi = {idx: pid for pid, idx in poi_to_idx.items()}

    # Calculate global mean
    mu = df['rating'].mean()
    print(f"Global mean rating: {mu:.4f}")

    # Initialize biases to 0
    b_u = np.zeros(num_users)
    b_i = np.zeros(num_pois)

    # Initialize latent vectors with small random values
    np.random.seed(42)
    P = np.random.normal(0, 0.1, (num_users, latent_dim))
    Q = np.random.normal(0, 0.1, (num_pois, latent_dim))

    # Convert ratings df to list of tuples for fast iteration (u_idx, i_idx, rating)
    ratings_list = []
    for _, row in df.iterrows():
        u_idx = user_to_idx[row['user_id']]
        i_idx = poi_to_idx[row['poi_id']]
        r = float(row['rating'])
        ratings_list.append((u_idx, i_idx, r))

    # Stochastic Gradient Descent (SGD)
    print("Training SVD model...")
    for epoch in range(1, epochs + 1):
        # Shuffle ratings for SGD
        random_indices = np.random.permutation(len(ratings_list))
        
        loss = 0
        for idx in random_indices:
            u, i, r = ratings_list[idx]
            
            # Predict rating
            pred = mu + b_u[u] + b_i[i] + np.dot(P[u], Q[i])
            
            # Error
            err = r - pred
            loss += err ** 2
            
            # Update biases
            b_u[u] += lr * (err - reg * b_u[u])
            b_i[i] += lr * (err - reg * b_i[i])
            
            # Update latent matrices
            P_old_u = P[u].copy()
            P[u] += lr * (err * Q[i] - reg * P[u])
            Q[i] += lr * (err * P_old_u - reg * Q[i])
            
        rmse = np.sqrt(loss / len(ratings_list))
        if epoch == 1 or epoch % 10 == 0 or epoch == epochs:
            print(f"Epoch {epoch}/{epochs} - Loss (MSE): {loss/len(ratings_list):.4f} - RMSE: {rmse:.4f}")

    # Convert mapping indices back to dictionary maps of user_id/poi_id for easy runtime prediction
    weights = {
        "mu": float(mu),
        "b_u": {idx_to_user[idx]: float(b) for idx, b in enumerate(b_u)},
        "b_i": {idx_to_poi[idx]: float(b) for idx, b in enumerate(b_i)},
        "P": {idx_to_user[idx]: P[idx].tolist() for idx in range(num_users)},
        "Q": {idx_to_poi[idx]: Q[idx].tolist() for idx in range(num_pois)},
        "latent_dim": latent_dim,
        "global_avg_fallback": float(mu)
    }

    # Save to file
    with open(model_output, "wb") as f:
        pickle.dump(weights, f)
        
    print(f"Model trained successfully. Saved SVD weights to {model_output}")

if __name__ == "__main__":
    train_svd()
