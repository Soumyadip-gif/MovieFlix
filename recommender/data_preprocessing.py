
import pandas as pd
from pathlib import Path


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "MovieGenre.csv"
OUTPUT_FILE = BASE_DIR / "data" / "cleaned_movies.csv"


def load_dataset():
    """Load the original movie dataset."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}\n"
            "Place MovieGenre.csv inside the data folder."
        )

    # latin1 handles special characters in this dataset
    df = pd.read_csv(INPUT_FILE, encoding="latin1")

    print("Original dataset loaded successfully.")
    print("Original shape:", df.shape)

    return df


def clean_dataset(df):
    """Clean movie records and prepare them for recommendations."""

    df = df.copy()

    # Remove duplicate movie IDs
    df = df.drop_duplicates(subset=["imdbId"], keep="first")

    # Clean movie titles
    df["Title"] = df["Title"].astype("string").str.strip()

    # Clean genres while preserving their original order
    def clean_genres(value):
        if pd.isna(value):
            return pd.NA

        genres = [
            genre.strip().title()
            for genre in str(value).split("|")
            if genre.strip()
        ]

        # Remove repeated genres without changing their order
        genres = list(dict.fromkeys(genres))

        return "|".join(genres) if genres else pd.NA

    df["Genre"] = df["Genre"].apply(clean_genres)

    # Convert IMDb ratings into numeric values
    df["IMDB Score"] = pd.to_numeric(
        df["IMDB Score"], errors="coerce"
    )

    # Ratings must be between 0 and 10
    df.loc[
        ~df["IMDB Score"].between(0, 10),
        "IMDB Score"
    ] = pd.NA

    # Clean poster URLs
    df["Poster"] = df["Poster"].astype("string").str.strip()

    valid_posters = df["Poster"].str.match(
        r"^https?://", case=False, na=False
    )

    df.loc[~valid_posters, "Poster"] = pd.NA

    # Remove records without essential recommendation information
    df = df.dropna(subset=["Title", "Genre"])

    # Remove empty titles
    df = df[df["Title"] != ""]

    return df.reset_index(drop=True)


def save_dataset(df):
    """Save the cleaned dataset."""

    df.to_csv(OUTPUT_FILE, index=False)

    print("\nCleaned dataset saved successfully.")
    print("Saved at:", OUTPUT_FILE)


def main():
    df = load_dataset()

    print("\nMissing values before cleaning:")
    print(df.isna().sum())

    cleaned_df = clean_dataset(df)

    print("\nCleaning completed!")
    print("Original records:", len(df))
    print("Cleaned records:", len(cleaned_df))
    print("Removed records:", len(df) - len(cleaned_df))

    print("\nMissing values after cleaning:")
    print(cleaned_df.isna().sum())

    save_dataset(cleaned_df)


if __name__ == "__main__":
    main()
