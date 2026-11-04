
import pandas as pd
from pathlib import Path

# File paths
MOVIES_FILE = Path("data/cleaned_movies.csv")
SCAN_FILE = Path("data/poster_scan_results.csv")
OUTPUT_FILE = Path("data/movies_final.csv")

# Load datasets
movies = pd.read_csv(MOVIES_FILE)
scan = pd.read_csv(SCAN_FILE)

# Keep only movies whose posters are available
available_titles = set(
    scan.loc[scan["Status"] == "AVAILABLE", "Title"]
)

final_movies = movies[
    movies["Title"].isin(available_titles)
].copy()

# Save filtered dataset
final_movies.to_csv(OUTPUT_FILE, index=False)

print("\n========== MOVIEFLIX DATASET CLEANUP ==========")
print("Original movies:", len(movies))
print("Movies with available posters:", len(final_movies))
print("Movies removed:", len(movies) - len(final_movies))
print("Final dataset:", OUTPUT_FILE)
