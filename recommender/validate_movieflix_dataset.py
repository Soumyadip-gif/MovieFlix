
import pandas as pd
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_FILE = BASE_DIR / "data" / "movieflix_movies.csv"

def main():

    print("\nMOVIEFLIX DATASET VALIDATION")
    print("=" * 50)

    if not DATASET_FILE.exists():
        print("ERROR: Final dataset not found!")
        return

    movies = pd.read_csv(DATASET_FILE)

    print("Total movies:", len(movies))
    print("Total columns:", len(movies.columns))

    print("\nRequired columns:")

    required = [
        "imdb_id", "title", "genres", "overview",
        "poster_path", "poster_url", "IMDB Score",
        "cast", "director", "keywords"
    ]

    for column in required:
        print(
            f"{column}:",
            "OK" if column in movies.columns else "MISSING"
        )

    print("\nDATA QUALITY")
    print("-" * 50)

    for column in [
        "poster_url", "overview", "genres",
        "IMDB Score", "cast", "director", "keywords"
    ]:
        if column in movies.columns:
            if column == "IMDB Score":
                available = movies[column].notna().sum()
            else:
                available = (
                    movies[column]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                    .ne("")
                    .sum()
                )

            print(f"{column}: {available} available")

    print("\nDUPLICATE IMDb IDs:")

    print(
        movies["imdb_id"]
        .dropna()
        .duplicated()
        .sum()
    )

    print("\nPOSTER URL TEST")
    print("-" * 50)

    samples = movies[
        movies["poster_url"].notna()
        & (movies["poster_url"].astype(str).str.strip() != "")
    ].head(10)

    for _, movie in samples.iterrows():

        url = movie["poster_url"]

        try:
            response = requests.get(
                url,
                stream=True,
                timeout=15
            )

            content_type = response.headers.get(
                "Content-Type", ""
            )

            if response.status_code == 200 and "image" in content_type.lower():
                status = "WORKING"
            else:
                status = f"CHECK: HTTP {response.status_code}"

            print(f"{movie['title']}: {status}")

            response.close()

        except requests.RequestException as error:
            print(f"{movie['title']}: FAILED - {error}")

    print("\nVALIDATION COMPLETED")

if __name__ == "__main__":
    main()
