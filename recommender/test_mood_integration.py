from sentiment_analyzer import SentimentAnalyzer
from mood_recommender import MoodRecommender


class MovieFlixAI:
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.mood_recommender = MoodRecommender()

    def recommend_from_text(self, user_text, number_of_movies=5):

        # Step 1: Detect mood from user input
        analysis = self.sentiment_analyzer.analyze_mood(user_text)

        detected_mood = analysis["mood"]

        if detected_mood is None:
            return {
                "analysis": analysis,
                "movies": []
            }

        # Step 2: Recommend movies based on detected mood
        movies = self.mood_recommender.recommend_by_mood(
            detected_mood,
            number_of_movies
        )

        return {
            "analysis": analysis,
            "movies": movies
        }


if __name__ == "__main__":

    movieflix = MovieFlixAI()

    user_input = input(
        "\nTell MovieFlix how you are feeling: "
    )

    result = movieflix.recommend_from_text(user_input)

    print("\n" + "=" * 55)
    print("MOVIEFLIX AI RECOMMENDATIONS")
    print("=" * 55)

    print("\nDetected Mood:", result["analysis"]["mood"])
    print("Sentiment:", result["analysis"]["sentiment"])

    print("\nRecommended Movies:\n")

    if result["movies"] is not None and len(result["movies"]) > 0:

        for index, movie in result["movies"].iterrows():

            print(f"{index + 1}. {movie['Title']}")
            print("   Genre:", movie["Genre"])
            print("   IMDb Rating:", movie["IMDB Score"])
            print("-" * 45)

    else:
        print("No recommendations found.")