
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pathlib import Path
import pandas as pd
import json

from recommender.content_recommender_v2 import MovieRecommender


app = Flask(__name__)
CORS(app)


# --------------------------------------------------
# INITIALIZE NEW MOVIE RECOMMENDATION SYSTEM
# --------------------------------------------------

print("\n" + "=" * 60)
print("STARTING MOVIEFLIX")
print("=" * 60)

content_recommender = MovieRecommender()

# The new recommender loads the new dataset itself.
movies = content_recommender.movies

print("\nMovieFlix backend initialized successfully.")
print(f"Dataset: {content_recommender.dataset_path}")
print(f"Total movies: {len(movies)}")


# --------------------------------------------------
# HELPER: CONVERT DATAFRAME TO JSON-SAFE RECORDS
# --------------------------------------------------

def dataframe_to_records(dataframe):

    if dataframe is None or dataframe.empty:
        return []

    # Converts NaN values to JSON null.
    return json.loads(
        dataframe.to_json(orient="records")
    )


# --------------------------------------------------
# HELPER: VALIDATE COUNT
# --------------------------------------------------

def get_valid_count(value, default=10, maximum=20):

    try:
        count = int(value)
    except (TypeError, ValueError):
        count = default

    return max(1, min(count, maximum))


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def home():

    return render_template("index.html")


# --------------------------------------------------
# API 1: GET MOVIES FROM NEW DATASET
# --------------------------------------------------

@app.route("/api/movies", methods=["GET"])
def get_movies():

    try:

        limit = get_valid_count(
            request.args.get("limit", 10),
            default=10,
            maximum=100
        )

        movie_records = dataframe_to_records(
            movies.head(limit)
        )

        return jsonify({
            "success": True,
            "total": len(movies),
            "movies": movie_records
        })

    except Exception as error:

        print("GET MOVIES ERROR:", error)

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# --------------------------------------------------
# API 2: SEARCH MOVIES FROM NEW DATASET
# --------------------------------------------------

@app.route("/api/search-movies", methods=["GET"])
def search_movies():

    try:

        query = request.args.get("q", "").strip()

        if not query:

            return jsonify({
                "success": True,
                "suggestions": [],
                "movies": []
            })

        results = content_recommender.search_movies(
            query,
            limit=10
        )

        suggestions = [
            movie["title"]
            for movie in results
        ]

        return jsonify({
            "success": True,
            "suggestions": suggestions,
            "movies": results
        })

    except Exception as error:

        print("SEARCH ERROR:", error)

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# --------------------------------------------------
# API 3: HYBRID CONTENT-BASED RECOMMENDATIONS
# --------------------------------------------------

@app.route("/api/recommend", methods=["POST"])
def recommend_movies():

    try:

        data = request.get_json(silent=True) or {}

        movie_title = str(
            data.get("title", "")
        ).strip()

        year = data.get("year")

        count = get_valid_count(
            data.get("count", 5),
            default=5,
            maximum=20
        )

        if not movie_title:

            return jsonify({
                "success": False,
                "error": "Please provide a movie title."
            }), 400

        # Use the NEW hybrid recommendation method.
        result = content_recommender.get_recommendations(
            title=movie_title,
            count=count,
            year=year
        )

        if result["status"] != "success":

            return jsonify({
                "success": False,
                "status": result["status"],
                "message": result.get("message"),
                "recommendations": []
            }), 404

        return jsonify({
            "success": True,
            "status": "success",
            "input_movie": movie_title,
            "matched_movie": result["matched_movie"],
            "matched_year": result["matched_year"],
            "recommendations": result["recommendations"]
        })

    except Exception as error:

        print("RECOMMENDATION ERROR:", error)

        return jsonify({
            "success": False,
            "error": str(error),
            "recommendations": []
        }), 500


# --------------------------------------------------
# API 4: MOOD RECOMMENDATIONS
# TEMPORARILY DISABLED
# --------------------------------------------------

@app.route("/api/mood", methods=["POST"])
def recommend_by_mood():

    return jsonify({
        "success": False,
        "error": (
            "Mood recommendations are temporarily unavailable. "
            "They will be connected to the new dataset in the next phase."
        )
    }), 501


# --------------------------------------------------
# API 5: SENTIMENT ANALYSIS
# TEMPORARILY DISABLED
# --------------------------------------------------

@app.route("/api/analyze", methods=["POST"])
def analyze_and_recommend():

    return jsonify({
        "success": False,
        "error": (
            "Sentiment-based recommendations are temporarily unavailable. "
            "They will be integrated in the next phase."
        )
    }), 501


# --------------------------------------------------
# RUN FLASK APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
