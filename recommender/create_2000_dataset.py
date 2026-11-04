
import pandas as pd
import re
from pathlib import Path

DATA_DIR = Path("data")

movies = pd.read_csv(DATA_DIR / "cleaned_movies.csv")
scan = pd.read_csv(DATA_DIR / "poster_scan_results.csv")

def extract_year(title):
    if pd.isna(title):
        return None

    # Prefer the year inside parentheses, e.g. (1998)
    match = re.search(r"\((18|19|20)\d{2}\)", str(title))

    if match:
        return int(match.group(0)[1:-1])

    return None


movies["Release_Year"] = movies["Title"].apply(extract_year)
scan["Release_Year"] = scan["Title"].apply(extract_year)

# Only movies released from 2000 onwards
recent_movies = movies[
    movies["Release_Year"].notna() &
    (movies["Release_Year"] >= 2000)
].copy()

problem_statuses = [
    "BROKEN_LINK",
    "MISSING_URL",
    "TIMEOUT",
    "INVALID_URL",
    "NOT_AN_IMAGE",
    "INVALID_IMAGE",
    "REQUEST_ERROR"
]

problem_movies = scan[
    scan["Release_Year"].notna() &
    (scan["Release_Year"] >= 2000) &
    scan["Status"].isin(problem_statuses)
].copy()

recent_movies.to_csv(
    DATA_DIR / "movies_2000_onwards.csv",
    index=False
)

problem_movies.to_csv(
    DATA_DIR / "movies_2000_problem_posters.csv",
    index=False
)

print("\n========== CORRECTED DATASET SUMMARY ==========")
print("Movies from 2000 onwards:", len(recent_movies))
print("Problematic posters:", len(problem_movies))
print("\nProblem breakdown:")
print(problem_movies["Status"].value_counts())

print("\nSaved corrected datasets successfully.")
