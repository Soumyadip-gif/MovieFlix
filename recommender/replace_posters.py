
import pandas as pd
import re
from pathlib import Path
from poster_service import PosterService

DATA_DIR = Path("data")

INPUT_FILE = DATA_DIR / "movies_2000_problem_posters.csv"
OUTPUT_FILE = DATA_DIR / "poster_replacement_test.csv"


def extract_year(title):
    match = re.search(r"\((18|19|20)\d{2}\)", str(title))

    if match:
        return int(match.group(0)[1:-1])

    return None


movies = pd.read_csv(INPUT_FILE)

movies["Release_Year"] = movies["Title"].apply(extract_year)

# Safety filter: only movies released in 2000 or later
movies = movies[
    movies["Release_Year"].notna() &
    (movies["Release_Year"] >= 2000)
].copy()

# Test only 10 movies
test_movies = movies.head(10).copy()

results = []

service = PosterService()

try:

    for _, row in test_movies.iterrows():

        title = row["Title"]

        print("\nSearching:", title)

        new_poster = service.find_poster(title)

        if new_poster:
            status = "REPLACED"
            print("Replacement found:", new_poster)
        else:
            status = "NOT_FOUND"
            print("No replacement found.")

        results.append({
            "Title": title,
            "Release_Year": row["Release_Year"],
            "Original_Poster": row.get("Poster"),
            "Replacement_Poster": new_poster,
            "Replacement_Status": status
        })

        # Save progress after each movie
        pd.DataFrame(results).to_csv(
            OUTPUT_FILE,
            index=False
        )

finally:
    service.close()

print("\n========== REPLACEMENT TEST SUMMARY ==========")

if results:
    print(
        pd.DataFrame(results)[
            "Replacement_Status"
        ].value_counts()
    )

print("\nSaved:", OUTPUT_FILE)
