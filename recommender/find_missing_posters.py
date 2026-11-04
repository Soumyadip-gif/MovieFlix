
import pandas as pd
import requests
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from PIL import Image

# File paths
INPUT_FILE = Path("data/cleaned_movies.csv")
OUTPUT_FILE = Path("data/poster_scan_results.csv")
MISSING_FILE = Path("data/movies_missing_posters.csv")

# Scanner settings
TIMEOUT = 12
MAX_WORKERS = 8

# Load dataset
df = pd.read_csv(INPUT_FILE)

if "Title" not in df.columns or "Poster" not in df.columns:
    raise ValueError("Dataset must contain Title and Poster columns.")

print("=" * 55)
print("MOVIEFLIX - COMPLETE POSTER SCANNER")
print("=" * 55)
print("Total movies:", len(df))


def check_poster(row):
    title = str(row["Title"])
    raw_url = row["Poster"]

    result = {
        "Title": title,
        "Poster": raw_url,
        "Status": "",
        "HTTP_Status": "",
        "Content_Type": "",
        "Final_URL": "",
        "Error": ""
    }

    # Check missing URL
    if pd.isna(raw_url) or not str(raw_url).strip():
        result["Status"] = "MISSING_URL"
        return result

    url = str(raw_url).strip()
    parsed = urlparse(url)

    # Check invalid URL
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        result["Status"] = "INVALID_URL"
        return result

    try:
        response = requests.get(
            url,
            timeout=TIMEOUT,
            stream=True,
            allow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 MovieFlixPosterScanner/1.0"
            }
        )

        result["HTTP_Status"] = response.status_code
        result["Content_Type"] = response.headers.get("Content-Type", "")
        result["Final_URL"] = response.url

        if response.status_code != 200:
            result["Status"] = "BROKEN_LINK"

        elif not result["Content_Type"].lower().startswith("image/"):
            result["Status"] = "NOT_AN_IMAGE"

        else:
            try:
                image_data = response.content
                image = Image.open(BytesIO(image_data))
                image.verify()

                result["Status"] = "AVAILABLE"

            except Exception as error:
                result["Status"] = "INVALID_IMAGE"
                result["Error"] = str(error)

        response.close()

    except requests.exceptions.Timeout:
        result["Status"] = "TIMEOUT"

    except requests.exceptions.RequestException as error:
        result["Status"] = "REQUEST_ERROR"
        result["Error"] = str(error)

    return result


# Scan all movies
results = []

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [
        executor.submit(check_poster, row)
        for _, row in df.iterrows()
    ]

    for index, future in enumerate(as_completed(futures), start=1):
        results.append(future.result())

        if index % 500 == 0:
            print(f"Checked {index}/{len(df)} movies")


# Create results dataframe
results_df = pd.DataFrame(results)

# Identify duplicate poster URLs
valid_urls = results_df["Poster"].dropna().astype(str)
duplicate_urls = valid_urls[
    valid_urls.duplicated(keep=False)
].unique()

results_df["Duplicate_URL"] = (
    results_df["Poster"].astype(str).isin(duplicate_urls)
)

# Save complete scan report
results_df.to_csv(OUTPUT_FILE, index=False)

# Extract all potentially unavailable posters
unavailable_statuses = [
    "MISSING_URL",
    "INVALID_URL",
    "BROKEN_LINK",
    "NOT_AN_IMAGE",
    "INVALID_IMAGE",
    "TIMEOUT",
    "REQUEST_ERROR"
]

missing_df = results_df[
    results_df["Status"].isin(unavailable_statuses)
].copy()

missing_df.to_csv(MISSING_FILE, index=False)


# Display summary
print("\n" + "=" * 55)
print("POSTER SCAN SUMMARY")
print("=" * 55)

print(results_df["Status"].value_counts().to_string())

print("\nTotal movies scanned:", len(results_df))
print("Available posters:", (results_df["Status"] == "AVAILABLE").sum())
print("Unavailable/problematic posters:", len(missing_df))
print("Movies with duplicate poster URLs:", results_df["Duplicate_URL"].sum())

print("\nReports saved:")
print("1.", OUTPUT_FILE)
print("2.", MISSING_FILE)

print("\nPoster scan completed!")
