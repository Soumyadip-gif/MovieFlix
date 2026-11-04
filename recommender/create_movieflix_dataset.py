
import ast
import pandas as pd
from pathlib import Path


# --------------------------------------------------
# FILE PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw" / "tmdb_dataset"

METADATA_FILE = RAW_DIR / "movies_metadata.csv"
CREDITS_FILE = RAW_DIR / "credits.csv"
KEYWORDS_FILE = RAW_DIR / "keywords.csv"
OLD_DATASET_FILE = DATA_DIR / "MovieGenre.csv"

OUTPUT_FILE = DATA_DIR / "movieflix_movies.csv"

POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def parse_list(value):
    """
    Safely parse Python-style list/dictionary strings
    from the TMDB CSV files.
    """

    if pd.isna(value):
        return []

    if isinstance(value, list):
        return value

    try:
        result = ast.literal_eval(str(value))

        if isinstance(result, list):
            return result

        return []

    except (ValueError, SyntaxError, TypeError):
        return []


def normalize_tmdb_id(value):
    """Convert TMDB IDs into consistent string values."""

    if pd.isna(value):
        return ""

    try:
        return str(int(float(value)))
    except (ValueError, TypeError):
        return str(value).strip()


def normalize_imdb_id(value):
    """Normalize IMDb IDs such as 114709 into tt0114709."""

    if pd.isna(value):
        return ""

    value = str(value).strip()

    if not value or value.lower() == "nan":
        return ""

    if value.startswith("tt"):
        digits = value[2:]
    else:
        digits = value

    try:
        return "tt" + str(int(float(digits))).zfill(7)
    except (ValueError, TypeError):
        return ""


def extract_names(value):
    """Extract name values from a list of dictionaries."""

    items = parse_list(value)

    names = []

    for item in items:
        if isinstance(item, dict):
            name = item.get("name")

            if name:
                names.append(str(name).strip())

    return list(dict.fromkeys(names))


def extract_cast(value, limit=10):
    """Extract the first few cast members."""

    items = parse_list(value)

    names = []

    for item in items:
        if isinstance(item, dict):
            name = item.get("name")

            if name:
                names.append(str(name).strip())

        if len(names) >= limit:
            break

    return list(dict.fromkeys(names))


def extract_directors(value):
    """Extract directors from the crew list."""

    items = parse_list(value)

    directors = []

    for item in items:
        if not isinstance(item, dict):
            continue

        if item.get("job") == "Director":
            name = item.get("name")

            if name:
                directors.append(str(name).strip())

    return list(dict.fromkeys(directors))


def make_poster_url(poster_path):
    """Build a TMDB image URL from a poster path."""

    if pd.isna(poster_path):
        return ""

    poster_path = str(poster_path).strip()

    if not poster_path or poster_path.lower() == "nan":
        return ""

    if not poster_path.startswith("/"):
        poster_path = "/" + poster_path

    return POSTER_BASE_URL + poster_path


# --------------------------------------------------
# LOAD DATASETS
# --------------------------------------------------

def main():

    print("\nMOVIEFLIX DATASET BUILDING")
    print("=" * 60)

    print("\nLoading original datasets...")

    metadata = pd.read_csv(METADATA_FILE, low_memory=False)
    credits = pd.read_csv(CREDITS_FILE, low_memory=False)
    keywords = pd.read_csv(KEYWORDS_FILE, low_memory=False)

    print("Metadata records:", len(metadata))
    print("Credits records:", len(credits))
    print("Keywords records:", len(keywords))

    # --------------------------------------------------
    # PREPARE TMDB IDs
    # --------------------------------------------------

    metadata["tmdb_key"] = metadata["id"].apply(normalize_tmdb_id)
    credits["tmdb_key"] = credits["id"].apply(normalize_tmdb_id)
    keywords["tmdb_key"] = keywords["id"].apply(normalize_tmdb_id)

    # Remove duplicate IDs before merging.
    credits = credits.drop_duplicates(subset="tmdb_key", keep="first")
    keywords = keywords.drop_duplicates(subset="tmdb_key", keep="first")

    # --------------------------------------------------
    # MERGE DATASETS
    # --------------------------------------------------

    print("\nMerging metadata, credits and keywords...")

    movies = metadata.merge(
        credits[["tmdb_key", "cast", "crew"]],
        on="tmdb_key",
        how="left"
    )

    movies = movies.merge(
        keywords[["tmdb_key", "keywords"]],
        on="tmdb_key",
        how="left"
    )

    # --------------------------------------------------
    # EXTRACT MOVIE FEATURES
    # --------------------------------------------------

    print("Extracting genres, cast, directors and keywords...")

    movies["genres"] = movies["genres"].apply(
        lambda value: ", ".join(extract_names(value))
    )

    movies["cast"] = movies["cast"].apply(
        lambda value: ", ".join(extract_cast(value))
    )

    movies["director"] = movies["crew"].apply(
        lambda value: ", ".join(extract_directors(value))
    )

    movies["keywords"] = movies["keywords"].apply(
        lambda value: ", ".join(extract_names(value))
    )

    # --------------------------------------------------
    # CLEAN BASIC MOVIE INFORMATION
    # --------------------------------------------------

    movies["imdb_id"] = movies["imdb_id"].apply(normalize_imdb_id)

    movies["title"] = movies["title"].fillna("").astype(str).str.strip()

    movies["overview"] = (
        movies["overview"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    movies["poster_path"] = (
        movies["poster_path"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    movies["poster_url"] = movies["poster_path"].apply(make_poster_url)

    movies["release_year"] = pd.to_datetime(
        movies["release_date"],
        errors="coerce"
    ).dt.year

    # Convert ratings into numeric values.
    movies["vote_average"] = pd.to_numeric(
        movies["vote_average"],
        errors="coerce"
    )

    movies["vote_count"] = pd.to_numeric(
        movies["vote_count"],
        errors="coerce"
    )

    # --------------------------------------------------
    # PRESERVE OLD IMDB SCORES
    # --------------------------------------------------

    print("\nMatching old IMDb scores...")

    if OLD_DATASET_FILE.exists():

        old_movies = pd.read_csv(
            OLD_DATASET_FILE,
            low_memory=False,
            encoding="latin-1"
        )


        old_movies["imdb_id"] = old_movies["imdbId"].apply(
            normalize_imdb_id
        )

        old_movies["IMDB Score"] = pd.to_numeric(
            old_movies["IMDB Score"],
            errors="coerce"
        )

        old_scores = (
            old_movies[["imdb_id", "IMDB Score"]]
            .drop_duplicates(subset="imdb_id", keep="first")
        )

        movies = movies.merge(
            old_scores,
            on="imdb_id",
            how="left"
        )

        print(
            "Old IMDb scores matched:",
            movies["IMDB Score"].notna().sum()
        )

    else:
        movies["IMDB Score"] = pd.NA
        print("Old MovieGenre.csv not found. Using TMDB ratings.")

    # Fill missing IMDb scores with TMDB ratings.
    movies["IMDB Score"] = (
        movies["IMDB Score"].fillna(movies["vote_average"])
    )

    # --------------------------------------------------
    # SELECT FINAL COLUMNS
    # --------------------------------------------------

    final_columns = [
        "id",
        "imdb_id",
        "title",
        "release_year",
        "release_date",
        "genres",
        "overview",
        "poster_path",
        "poster_url",
        "IMDB Score",
        "vote_average",
        "vote_count",
        "cast",
        "director",
        "keywords",
        "imdb_id"
    ]

    final_movies = movies[[
        column for column in dict.fromkeys(final_columns)
        if column in movies.columns
    ]].copy()

    final_movies = final_movies.rename(columns={"id": "tmdb_id"})

    # Remove records without a usable title.
    final_movies = final_movies[
        final_movies["title"].notna()
        & (final_movies["title"].astype(str).str.strip() != "")
    ]

    # Remove duplicate IMDb IDs, preserving records without IMDb IDs.
    has_imdb = final_movies["imdb_id"].astype(str).str.startswith("tt")

    with_imdb = final_movies[has_imdb].drop_duplicates(
        subset="imdb_id",
        keep="first"
    )

    without_imdb = final_movies[~has_imdb]

    final_movies = pd.concat(
        [with_imdb, without_imdb],
        ignore_index=True
    )

    # --------------------------------------------------
    # SAVE FINAL DATASET
    # --------------------------------------------------

    final_movies.to_csv(OUTPUT_FILE, index=False)

    # --------------------------------------------------
    # BUILD SUMMARY
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("MOVIEFLIX DATASET BUILDING COMPLETED")
    print("=" * 60)

    print("Total movies:", len(final_movies))
    print("Total columns:", len(final_movies.columns))

    print("\nFEATURE AVAILABILITY")
    print("-" * 60)

    for column in [
        "genres",
        "overview",
        "cast",
        "director",
        "keywords",
        "poster_url",
        "IMDB Score"
    ]:
        if column in final_movies.columns:
            available = (
                final_movies[column]
                .fillna("")
                .astype(str)
                .str.strip()
                .ne("")
                .sum()
            )

            print(f"{column}: {available}")

    print("\nSaved dataset:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
