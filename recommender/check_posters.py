
import pandas as pd
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

DATASET_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "movieflix_movies.csv"
)

OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "poster_check_results.csv"
)

print("\nMOVIEFLIX POSTER DIAGNOSTICS")
print("=" * 60)

# Load dataset
movies = pd.read_csv(DATASET_PATH)

# Select movies with poster URLs
movies = movies[
    movies["poster_url"].notna() &
    (movies["poster_url"].astype(str).str.strip() != "")
].copy()

# Test a random sample of 100 posters
sample_size = min(100, len(movies))

sample = movies.sample(
    n=sample_size,
    random_state=42
)

print(f"\nTesting {sample_size} poster URLs...")
print("Please wait...\n")


def check_poster(movie):
    url = str(movie["poster_url"]).strip()

    result = {
        "title": movie["title"],
        "poster_url": url,
        "status_code": None,
        "content_type": None,
        "working": False
    }

    try:
        response = requests.get(
            url,
            timeout=20,
            stream=True,
            headers={
                "User-Agent": "MovieFlix Poster Checker/1.0"
            }
        )

        result["status_code"] = response.status_code
        result["content_type"] = response.headers.get(
            "Content-Type", ""
        )

        result["working"] = (
            response.status_code == 200 and
            result["content_type"].startswith("image/")
        )

        response.close()

    except requests.RequestException as error:
        result["status_code"] = "ERROR"
        result["content_type"] = str(error)

    return result


results = []

with ThreadPoolExecutor(max_workers=5) as executor:

    futures = [
        executor.submit(check_poster, row)
        for _, row in sample.iterrows()
    ]

    for future in as_completed(futures):
        results.append(future.result())


# Save diagnostic results
results_df = pd.DataFrame(results)

results_df.to_csv(OUTPUT_PATH, index=False)

# Calculate statistics
working = results_df["working"].sum()
unavailable = len(results_df) - working

print("=" * 60)
print("POSTER TEST RESULTS")
print("=" * 60)

print(f"Total tested:       {len(results_df)}")
print(f"Working posters:    {working}")
print(f"Unavailable:        {unavailable}")

print(
    f"Success rate:       "
    f"{working / len(results_df) * 100:.2f}%"
)

print("\nHTTP STATUS BREAKDOWN:")

print(results_df["status_code"].value_counts().to_string())

print("\nResults saved to:")
print(OUTPUT_PATH)

print("\nFirst 15 unavailable posters:")

print(
    results_df[
        results_df["working"] == False
    ][["title", "status_code", "poster_url"]]
    .head(15)
    .to_string(index=False)
)
