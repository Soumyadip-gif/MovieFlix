
import re
import json
import hashlib
from pathlib import Path
from difflib import get_close_matches

import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer


class MovieRecommender:

    DATASET_PATH = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "movieflix_movies.csv"
    )

    MODEL_NAME = "all-MiniLM-L6-v2"

    # Embedding cache
    EMBEDDING_PATH = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "movie_overview_embeddings.npy"
    )

    EMBEDDING_METADATA_PATH = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "movie_overview_embeddings.json"
    )

    # Total weight = 1.0
    FEATURE_WEIGHTS = {
        "genres": 0.10,
        "overview": 0.10,
        "semantic_overview": 0.40,
        "cast": 0.08,
        "director": 0.04,
        "keywords": 0.28,
    }

    FEATURE_THRESHOLDS = {
        "genres": 0.10,
        "overview": 0.05,
        "semantic_overview": 0.25,
        "cast": 0.08,
        "keywords": 0.05,
    }

    MIN_MEANINGFUL_MATCHES = 2
    MIN_RELEVANCE_SCORE = 0.05

    MIN_OVERVIEW_MATCH = 0.07
    MIN_SEMANTIC_MATCH = 0.35
    MIN_KEYWORD_MATCH = 0.20
    MIN_CAST_MATCH = 0.35

    YEAR_TOLERANCE = 2

    def __init__(self, dataset_path=None):

        self.dataset_path = Path(
            dataset_path or self.DATASET_PATH
        )

        self.movies = None
        self.feature_matrices = {}
        self.vectorizers = {}

        self.semantic_model = None
        self.semantic_embeddings = None

        self.rating_normalized = None

        self.load_dataset()
        self.build_model()

    # --------------------------------------------------
    # 1. TITLE NORMALIZATION
    # --------------------------------------------------

    @staticmethod
    def normalize_title(title):

        if title is None:
            return ""

        title = str(title).casefold()

        return re.sub(
            r"[^a-z0-9]+",
            " ",
            title
        ).strip()

    # --------------------------------------------------
    # 2. LOAD DATASET
    # --------------------------------------------------

    def load_dataset(self):

        print("\nLoading MovieFlix dataset...")

        if not self.dataset_path.exists():

            raise FileNotFoundError(
                f"Dataset not found: {self.dataset_path}"
            )

        self.movies = pd.read_csv(
            self.dataset_path
        ).reset_index(drop=True)

        required_columns = [
            "title",
            "genres",
            "overview",
            "cast",
            "director",
            "keywords",
            "IMDB Score"
        ]

        missing = [
            column
            for column in required_columns
            if column not in self.movies.columns
        ]

        if missing:

            raise ValueError(
                f"Missing dataset columns: {missing}"
            )

        optional_columns = [
            "release_year",
            "release_date",
            "poster_url",
            "imdb_id"
        ]

        for column in optional_columns:

            if column not in self.movies.columns:
                self.movies[column] = ""

        text_columns = [
            "title",
            "genres",
            "overview",
            "cast",
            "director",
            "keywords"
        ]

        for column in text_columns:

            self.movies[column] = (
                self.movies[column]
                .fillna("")
                .astype(str)
                .str.strip()
            )

        self.movies = self.movies[
            self.movies["title"].ne("")
        ].reset_index(drop=True)

        self.movies["IMDB Score"] = pd.to_numeric(
            self.movies["IMDB Score"],
            errors="coerce"
        ).fillna(0)

        self.movies["release_year"] = pd.to_numeric(
            self.movies["release_year"],
            errors="coerce"
        )

        self.movies["normalized_title"] = (
            self.movies["title"].apply(
                self.normalize_title
            )
        )

        ratings = self.movies[
            "IMDB Score"
        ].to_numpy(dtype=np.float32)

        min_rating = ratings.min()
        max_rating = ratings.max()

        if max_rating > min_rating:

            self.rating_normalized = (
                (ratings - min_rating)
                / (max_rating - min_rating)
            )

        else:

            self.rating_normalized = np.zeros(
                len(ratings),
                dtype=np.float32
            )

        print(f"Movies loaded: {len(self.movies)}")

        print(
            f"Unique titles: "
            f"{self.movies['normalized_title'].nunique()}"
        )

    # --------------------------------------------------
    # 3. BUILD TF-IDF MATRICES
    # --------------------------------------------------

    def build_model(self):

        print("\nBuilding MovieFlix hybrid recommendation model...")

        tfidf_features = [
            "genres",
            "overview",
            "cast",
            "director",
            "keywords"
        ]

        for feature in tfidf_features:

            print(f"\nProcessing TF-IDF: {feature}")

            vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                min_df=1,
                max_features=50000,
                sublinear_tf=True,
                dtype=np.float32
            )

            try:

                matrix = vectorizer.fit_transform(
                    self.movies[feature].tolist()
                )

                self.vectorizers[feature] = vectorizer

            except ValueError:

                matrix = None
                self.vectorizers[feature] = None

            self.feature_matrices[feature] = matrix

            if matrix is None:

                print(f"{feature}: no usable vocabulary")

            else:

                print(
                    f"{feature}: "
                    f"{matrix.shape[1]} features, "
                    f"{matrix.nnz} non-zero values"
                )

        # Build semantic overview embeddings.
        self.build_semantic_embeddings()

        print("\nHybrid recommendation model completed.")

    # --------------------------------------------------
    # 4. SEMANTIC OVERVIEW EMBEDDINGS
    # --------------------------------------------------

    def get_overview_fingerprint(self):

        hasher = hashlib.sha256()

        hasher.update(
            self.MODEL_NAME.encode("utf-8")
        )

        for overview in self.movies["overview"]:

            hasher.update(
                overview.encode("utf-8")
            )

            hasher.update(b"\0")

        return hasher.hexdigest()

    def build_semantic_embeddings(self):

        print("\nBuilding semantic overview embeddings...")

        fingerprint = self.get_overview_fingerprint()

        # Try loading existing cached embeddings.
        if (
            self.EMBEDDING_PATH.exists()
            and self.EMBEDDING_METADATA_PATH.exists()
        ):

            try:

                with open(
                    self.EMBEDDING_METADATA_PATH,
                    "r",
                    encoding="utf-8"
                ) as file:

                    metadata = json.load(file)

                cached_embeddings = np.load(
                    self.EMBEDDING_PATH,
                    allow_pickle=False
                )

                cache_is_valid = (
                    metadata.get("model_name") == self.MODEL_NAME
                    and metadata.get("fingerprint") == fingerprint
                    and cached_embeddings.shape[0] == len(self.movies)
                    and cached_embeddings.shape[1] == 384
                )

                if cache_is_valid:

                    self.semantic_embeddings = (
                        cached_embeddings.astype(
                            np.float32,
                            copy=False
                        )
                    )

                    print(
                        "Loaded semantic embeddings from cache."
                    )

                    return

            except (
                OSError,
                ValueError,
                KeyError,
                json.JSONDecodeError
            ):

                print(
                    "Existing embedding cache is invalid. Rebuilding..."
                )

        # Load the sentence-transformer model.
        print(
            f"Loading semantic model: {self.MODEL_NAME}"
        )

        self.semantic_model = SentenceTransformer(
            self.MODEL_NAME
        )

        overviews = self.movies[
            "overview"
        ].tolist()

        # Encode all movie descriptions.
        print(
            f"Generating embeddings for {len(overviews)} movies..."
        )

        embeddings = self.semantic_model.encode(
            overviews,
            batch_size=64,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        embeddings = np.asarray(
            embeddings,
            dtype=np.float32
        )

        # Empty descriptions should not receive similarity scores.
        empty_overviews = (
            self.movies["overview"]
            .eq("")
            .to_numpy()
        )

        embeddings[empty_overviews] = 0.0

        self.semantic_embeddings = embeddings

        # Save embeddings for future runs.
        self.EMBEDDING_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        np.save(
            self.EMBEDDING_PATH,
            embeddings
        )

        metadata = {
            "model_name": self.MODEL_NAME,
            "fingerprint": fingerprint,
            "movie_count": len(self.movies),
            "embedding_dimension": embeddings.shape[1]
        }

        with open(
            self.EMBEDDING_METADATA_PATH,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                metadata,
                file,
                indent=4
            )

        print(
            f"Semantic embeddings saved: {self.EMBEDDING_PATH}"
        )

        print(
            f"Embedding shape: {embeddings.shape}"
        )

    # --------------------------------------------------
    # 5. YEAR FILTERING
    # --------------------------------------------------

    def filter_by_year(self, candidates, year):

        if year is None or candidates.empty:
            return candidates

        years = pd.to_numeric(
            candidates["release_year"],
            errors="coerce"
        )

        valid = years.notna()

        if not valid.any():
            return candidates.iloc[0:0]

        differences = (
            years[valid] - int(year)
        ).abs()

        minimum_difference = differences.min()

        if minimum_difference > self.YEAR_TOLERANCE:
            return candidates.iloc[0:0]

        return candidates.loc[
            differences[
                differences <= self.YEAR_TOLERANCE
            ].index
        ]

    # --------------------------------------------------
    # 6. FIND MOVIE
    # --------------------------------------------------

    def find_movie(self, title, year=None):

        normalized = self.normalize_title(title)

        if not normalized:
            return None

        if year is not None:

            try:
                year = int(year)
            except (TypeError, ValueError):
                year = None

        exact_matches = self.movies[
            self.movies["normalized_title"] == normalized
        ]

        if not exact_matches.empty:

            if year is not None:

                candidates = self.filter_by_year(
                    exact_matches,
                    year
                )

                if candidates.empty:
                    return None

                differences = (
                    candidates["release_year"] - year
                ).abs()

                return int(differences.idxmin())

            return int(
                exact_matches["IMDB Score"].idxmax()
            )

        partial_matches = self.movies[
            self.movies["normalized_title"].str.contains(
                re.escape(normalized),
                na=False
            )
        ]

        if not partial_matches.empty:

            if year is not None:

                partial_matches = self.filter_by_year(
                    partial_matches,
                    year
                )

            if not partial_matches.empty:

                if year is not None:

                    differences = (
                        partial_matches["release_year"] - year
                    ).abs()

                    partial_matches = partial_matches[
                        differences == differences.min()
                    ]

                return int(
                    partial_matches["IMDB Score"].idxmax()
                )

        available_titles = (
            self.movies["normalized_title"]
            .dropna()
            .unique()
        )

        close_matches = get_close_matches(
            normalized,
            available_titles,
            n=1,
            cutoff=0.65
        )

        if close_matches:

            candidates = self.movies[
                self.movies["normalized_title"]
                == close_matches[0]
            ]

            if year is not None:

                candidates = self.filter_by_year(
                    candidates,
                    year
                )

            if not candidates.empty:

                return int(
                    candidates["IMDB Score"].idxmax()
                )

        return None

    # --------------------------------------------------
    # 7. CALCULATE FEATURE SIMILARITIES
    # --------------------------------------------------

    def calculate_feature_similarities(
        self,
        movie_index
    ):

        feature_similarities = {}

        # Existing TF-IDF features.
        for feature in [
            "genres",
            "overview",
            "cast",
            "director",
            "keywords"
        ]:

            matrix = self.feature_matrices.get(
                feature
            )

            if matrix is None:

                scores = np.zeros(
                    len(self.movies),
                    dtype=np.float32
                )

            else:

                scores = (
                    matrix.getrow(movie_index)
                    @ matrix.T
                ).toarray().ravel()

                scores = scores.astype(
                    np.float32
                )

            feature_similarities[feature] = scores

        # Semantic similarity between movie overviews.
        query_embedding = (
            self.semantic_embeddings[movie_index]
        )

        semantic_scores = (
            self.semantic_embeddings
            @ query_embedding
        )

        semantic_scores = np.clip(
            semantic_scores,
            0.0,
            1.0
        ).astype(np.float32)

        # If the selected movie has no overview,
        # do not use semantic similarity.
        if np.linalg.norm(query_embedding) == 0:

            semantic_scores[:] = 0.0

        feature_similarities[
            "semantic_overview"
        ] = semantic_scores

        return feature_similarities

    # --------------------------------------------------
    # 8. COUNT MEANINGFUL MATCHES
    # --------------------------------------------------

    def count_meaningful_matches(
        self,
        feature_scores
    ):

        meaningful_features = []

        for feature, threshold in (
            self.FEATURE_THRESHOLDS.items()
        ):

            if feature_scores.get(
                feature,
                0
            ) >= threshold:

                meaningful_features.append(feature)

        return meaningful_features

    # --------------------------------------------------
    # 9. CHECK CONTENT RELEVANCE
    # --------------------------------------------------

    def has_content_match(self, feature_scores):

        semantic_score = feature_scores[
            "semantic_overview"
        ]

        overview_score = feature_scores[
            "overview"
        ]

        keyword_score = feature_scores[
            "keywords"
        ]

        cast_score = feature_scores[
            "cast"
        ]

        genre_score = feature_scores[
            "genres"
        ]

        # Strong semantic story similarity.
        if semantic_score >= self.MIN_SEMANTIC_MATCH:
            return True

        # Moderate semantic similarity supported
        # by keywords or genres.
        if (
            semantic_score >= 0.28
            and (
                keyword_score >= 0.15
                or genre_score >= 0.20
            )
        ):
            return True

        # Strong lexical overview similarity.
        if overview_score >= self.MIN_OVERVIEW_MATCH:
            return True

        # Strong cast match supported by keywords.
        if (
            cast_score >= self.MIN_CAST_MATCH
            and keyword_score >= 0.15
        ):
            return True

        return False

    # --------------------------------------------------
    # 10. BUILD EXPLANATION
    # --------------------------------------------------

    def build_explanation(
        self,
        feature_scores,
        contributions
    ):

        explanations = []

        meaningful_features = (
            self.count_meaningful_matches(
                feature_scores
            )
        )

        ranked_features = sorted(
            contributions.items(),
            key=lambda item: item[1],
            reverse=True
        )

        explanation_labels = {
            "genres": "Similar genres",
            "overview": "Similar story keywords",
            "semantic_overview": "Similar story and meaning",
            "cast": "Shared cast members",
            "keywords": "Similar themes and keywords"
        }

        for feature, contribution in ranked_features:

            if feature == "director":

                if feature_scores[feature] >= 0.10:

                    explanations.append(
                        "Shared director"
                    )

            elif feature in meaningful_features:

                explanations.append(
                    explanation_labels[feature]
                )

        return explanations[:3]

    # --------------------------------------------------
    # 11. GET RECOMMENDATIONS
    # --------------------------------------------------

    def get_recommendations(
        self,
        title,
        count=10,
        year=None
    ):

        print(
            f"\nFinding movies similar to: {title}"
        )

        try:
            count = int(count)
        except (TypeError, ValueError):
            count = 10

        count = max(1, min(count, 50))

        movie_index = self.find_movie(
            title,
            year
        )

        if movie_index is None:

            return {
                "status": "not_found",
                "message": (
                    f"Movie '{title}' was not found. "
                    "Check the title or release year."
                ),
                "recommendations": []
            }

        selected_movie = self.movies.iloc[
            movie_index
        ]

        selected_normalized_title = (
            selected_movie["normalized_title"]
        )

        print(
            f"MATCHED TITLE: {selected_movie['title']}"
        )

        print(
            f"MATCHED YEAR: {selected_movie['release_year']}"
        )

        feature_similarities = (
            self.calculate_feature_similarities(
                movie_index
            )
        )

        combined_similarity = np.zeros(
            len(self.movies),
            dtype=np.float32
        )

        for feature, weight in self.FEATURE_WEIGHTS.items():

            combined_similarity += (
                feature_similarities[feature] * weight
            )

        final_scores = combined_similarity * (
            0.98 + 0.02 * self.rating_normalized
        )

        results = self.movies.copy()

        results["similarity"] = combined_similarity
        results["final_score"] = final_scores

        # Exclude selected movie and duplicate title versions.
        results = results[
            (results.index != movie_index)
            &
            (
                results["normalized_title"]
                != selected_normalized_title
            )
        ].copy()

        meaningful_match_counts = []
        content_match_flags = []

        for result_index in results.index:

            feature_scores = {
                feature: float(
                    feature_similarities[feature][result_index]
                )
                for feature in self.FEATURE_WEIGHTS
            }

            meaningful_matches = (
                self.count_meaningful_matches(
                    feature_scores
                )
            )

            has_content = self.has_content_match(
                feature_scores
            )

            meaningful_match_counts.append(
                len(meaningful_matches)
            )

            content_match_flags.append(
                has_content
            )

        results["meaningful_matches"] = (
            meaningful_match_counts
        )

        results["has_content_match"] = (
            content_match_flags
        )

        # Filter weak recommendations.
        results = results[
            (results["meaningful_matches"] >= self.MIN_MEANINGFUL_MATCHES)
            &
            (results["similarity"] >= self.MIN_RELEVANCE_SCORE)
            &
            (results["has_content_match"])
        ].copy()

        results = results.sort_values(
            by="final_score",
            ascending=False
        ).head(count)

        recommendations = []

        for result_index, movie in results.iterrows():

            feature_scores = {}

            for feature in self.FEATURE_WEIGHTS:

                feature_scores[feature] = round(
                    float(
                        feature_similarities[feature][result_index]
                    ),
                    4
                )

            contributions = {
                feature: round(
                    feature_scores[feature] * weight,
                    4
                )
                for feature, weight
                in self.FEATURE_WEIGHTS.items()
            }

            explanation = self.build_explanation(
                feature_scores,
                contributions
            )

            recommendations.append({

                "title": movie["title"],

                "release_year": (
                    None
                    if pd.isna(movie["release_year"])
                    else int(movie["release_year"])
                ),

                "genres": movie["genres"],

                "overview": movie["overview"],

                "cast": movie["cast"],

                "director": movie["director"],

                "keywords": movie["keywords"],

                "poster_url": movie["poster_url"],

                "imdb_id": movie["imdb_id"],

                "IMDB Score": float(
                    movie["IMDB Score"]
                ),

                "similarity": round(
                    float(movie["similarity"]),
                    4
                ),

                "final_score": round(
                    float(movie["final_score"]),
                    4
                ),

                "meaningful_matches": int(
                    movie["meaningful_matches"]
                ),

                "feature_scores": feature_scores,

                "feature_contributions": contributions,

                "explanation": explanation
            })

        return {

            "status": "success",

            "matched_movie": selected_movie["title"],

            "matched_year": (
                None
                if pd.isna(selected_movie["release_year"])
                else int(selected_movie["release_year"])
            ),

            "recommendations": recommendations
        }

    # --------------------------------------------------
    # 12. SEARCH MOVIES
    # --------------------------------------------------

    def search_movies(
        self,
        query,
        limit=10
    ):

        query = self.normalize_title(query)

        if not query:
            return []

        try:
            limit = max(1, min(int(limit), 50))
        except (TypeError, ValueError):
            limit = 10

        matches = self.movies[
            self.movies["normalized_title"].str.contains(
                re.escape(query),
                na=False
            )
        ].copy()

        matches = matches.sort_values(
            by="IMDB Score",
            ascending=False
        ).head(limit)

        return matches[
            [
                "title",
                "release_year",
                "genres",
                "poster_url",
                "IMDB Score"
            ]
        ].to_dict("records")


# --------------------------------------------------
# 13. STANDALONE TEST
# --------------------------------------------------

if __name__ == "__main__":

    recommender = MovieRecommender()

    test_movies = [
        ("Toy Story", 1995),
        ("Jumanji", 1995),
        ("The Dark Knight", 2008),
        ("Titanic", 1997),
        ("Avatar", 2009),
    ]

    for movie_title, movie_year in test_movies:

        result = recommender.get_recommendations(
            movie_title,
            count=10,
            year=movie_year
        )

        print("\n" + "=" * 75)

        print(
            f"RECOMMENDATIONS FOR "
            f"{movie_title} ({movie_year})"
        )

        print("=" * 75)

        if result["status"] != "success":

            print(result["message"])
            continue

        print(
            f"Matched: {result['matched_movie']} "
            f"({result['matched_year']})"
        )

        recommendations = result["recommendations"]

        if not recommendations:

            print(
                "\nNo sufficiently relevant recommendations found."
            )
            continue

        for index, movie in enumerate(
            recommendations,
            start=1
        ):

            print(
                f"\n{index}. {movie['title']} "
                f"({movie['release_year']})"
            )

            print(
                f"Similarity: {movie['similarity']:.4f}"
            )

            print(
                f"Final Score: {movie['final_score']:.4f}"
            )

            print(
                f"Meaningful Matches: "
                f"{movie['meaningful_matches']}"
            )

            print(
                "Feature Scores:",
                movie["feature_scores"]
            )

            print(
                "Why Recommended:",
                ", ".join(movie["explanation"])
            )

    # Fuzzy matching test
    print("\n" + "=" * 75)
    print("FUZZY MATCH TEST")
    print("=" * 75)

    typo_result = recommender.get_recommendations(
        "Tytanic",
        count=5
    )

    print(typo_result["status"])
    print(typo_result.get("matched_movie"))

    # Unknown movie test
    print("\n" + "=" * 75)
    print("UNKNOWN MOVIE TEST")
    print("=" * 75)

    unknown_result = recommender.get_recommendations(
        "This Movie Does Not Exist",
        count=5
    )

    print(unknown_result["status"])
    print(unknown_result["message"])
