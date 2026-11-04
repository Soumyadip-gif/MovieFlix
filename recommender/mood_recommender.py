
import pandas as pd
from pathlib import Path


class MoodRecommender:

    def __init__(self):

        self.base_dir = Path(__file__).resolve().parent.parent
        self.data_path = self.base_dir / "data" / "cleaned_movies.csv"

        self.movies = None

        # Mood-to-genre mapping
        self.mood_genres = {

            "happy": [
                "Comedy",
                "Animation",
                "Family"
            ],

            "sad": [
                "Drama",
                "Romance"
            ],

            "romantic": [
                "Romance",
                "Comedy",
                "Drama"
            ],

            "adventurous": [
                "Adventure",
                "Action",
                "Fantasy"
            ],

            "excited": [
                "Action",
                "Thriller",
                "Adventure"
            ],

            "relaxed": [
                "Comedy",
                "Family",
                "Romance"
            ],

            "scared": [
                "Horror",
                "Thriller",
                "Mystery"
            ],

            "thoughtful": [
                "Drama",
                "Mystery",
                "Documentary"
            ]
        }

    # -----------------------------------
    # 1. LOAD MOVIE DATA
    # -----------------------------------

    def load_data(self):

        if not self.data_path.exists():
            raise FileNotFoundError(
                "cleaned_movies.csv not found."
            )

        self.movies = pd.read_csv(self.data_path)

        self.movies["Genre"] = (
            self.movies["Genre"]
            .fillna("")
            .astype(str)
        )

        self.movies["IMDB Score"] = pd.to_numeric(
            self.movies["IMDB Score"],
            errors="coerce"
        )

        print(f"Loaded {len(self.movies)} movies.")

    # -----------------------------------
    # 2. RECOMMEND MOVIES BY MOOD
    # -----------------------------------

    def recommend_by_mood(self, mood, top_n=10):

        if self.movies is None:
            self.load_data()

        mood = str(mood).strip().lower()

        if mood not in self.mood_genres:

            print("Mood not supported:", mood)

            print(
                "Available moods:",
                ", ".join(self.mood_genres.keys())
            )

            return pd.DataFrame()

        selected_genres = self.mood_genres[mood]

        print("\nSelected mood:", mood)
        print("Target genres:", selected_genres)

        # Find movies matching at least one selected genre
        pattern = "|".join(
            pd.Series(selected_genres)
            .str.replace(r"([.*+?^${}()|[\]\\])", r"\\\1", regex=True)
        )

        recommendations = self.movies[
            self.movies["Genre"].str.contains(
                pattern,
                case=False,
                regex=True,
                na=False
            )
        ].copy()

        # Count matching genres
        recommendations["Genre Match"] = (
            recommendations["Genre"].apply(
                lambda genre: sum(
                    selected_genre.casefold() in [
                        item.strip().casefold()
                        for item in genre.split("|")
                    ]
                    for selected_genre in selected_genres
                )
            )
        )

        # Rank by matching genres and IMDb rating
        recommendations = recommendations.sort_values(
            by=["Genre Match", "IMDB Score"],
            ascending=[False, False],
            na_position="last"
        )

        return recommendations[
    [
        "Title",
        "Genre",
        "IMDB Score",
        "Genre Match",
        "Poster",
        "Imdb Link"
    ]
].head(top_n).reset_index(drop=True)


# -----------------------------------
# 3. TEST MOOD RECOMMENDATIONS
# -----------------------------------


if __name__ == "__main__":

    recommender = MoodRecommender()
    recommender.load_data()

    moods = [
        "happy",
        "sad",
        "romantic",
        "adventurous",
        "excited",
        "relaxed",
        "scared",
        "thoughtful"
    ]

    for mood in moods:

        results = recommender.recommend_by_mood(
            mood,
            top_n=5
        )

        print(f"\n{'=' * 60}")
        print(f"MOOD: {mood.upper()}")
        print("=" * 60)

        if not results.empty:
            print(
                results[
                    ["Title", "Genre", "IMDB Score"]
                ].to_string(index=False)
            )
        else:
            print("No recommendations found.")

