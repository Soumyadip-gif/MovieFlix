
from textblob import TextBlob


class SentimentAnalyzer:

    def __init__(self):

        # Mood keywords and related expressions
        self.mood_keywords = {

            "happy": [
                "happy", "happiness", "funny", "cheerful",
                "joyful", "laugh", "laughing", "positive",
                "great", "wonderful", "excited"
            ],

            "sad": [
                "sad", "lonely", "heartbroken", "depressed",
                "cry", "crying", "upset", "unhappy",
                "disappointed", "grief"
            ],

            "romantic": [
                "romantic", "love", "loving", "relationship",
                "valentine", "affection", "date"
            ],

            "adventurous": [
                "adventure", "adventurous", "explore",
                "exploring", "journey", "fantasy", "travel"
            ],

            "excited": [
                "thrilling", "thrill", "action", "energetic",
                "adrenaline", "intense", "exciting"
            ],

            "relaxed": [
                "relax", "relaxing", "calm", "peaceful",
                "stressful", "stress", "unwind", "tired",
                "exhausted", "rest"
            ],

            "scared": [
                "scared", "frightened", "horror", "fear",
                "terrifying", "spooky", "creepy", "haunted"
            ],

            "thoughtful": [
                "thoughtful", "thinking", "curious",
                "mysterious", "deep", "meaningful",
                "philosophical", "mind"
            ]
        }

    # ---------------------------------------
    # 1. DETECT MOOD USING KEYWORDS
    # ---------------------------------------

    def detect_keyword_mood(self, text):

        text = text.lower()

        mood_scores = {}

        for mood, keywords in self.mood_keywords.items():

            score = 0

            for keyword in keywords:

                if keyword in text:
                    score += 1

            mood_scores[mood] = score

        best_mood = max(
            mood_scores,
            key=mood_scores.get
        )

        if mood_scores[best_mood] > 0:
            return best_mood, mood_scores[best_mood]

        return None, 0

    # ---------------------------------------
    # 2. ANALYZE SENTIMENT
    # ---------------------------------------

    def analyze_mood(self, user_text):

        user_text = str(user_text).strip()

        if not user_text:
            return {
                "mood": None,
                "sentiment": "neutral",
                "polarity": 0.0,
                "subjectivity": 0.0,
                "matched_keywords": []
            }

        # Analyze sentiment using TextBlob
        analysis = TextBlob(user_text)

        polarity = analysis.sentiment.polarity
        subjectivity = analysis.sentiment.subjectivity

        # Detect mood using keywords
        detected_mood, keyword_score = (
            self.detect_keyword_mood(user_text)
        )

        # Use sentiment if no mood keywords are found
        if detected_mood is None:

            if polarity > 0.2:
                detected_mood = "happy"

            elif polarity < -0.2:
                detected_mood = "sad"

            else:
                detected_mood = "thoughtful"

        # Determine general sentiment
        if polarity > 0.2:
            sentiment = "positive"

        elif polarity < -0.2:
            sentiment = "negative"

        else:
            sentiment = "neutral"

        # Find matched keywords for explanation
        matched_keywords = []

        text_lower = user_text.lower()

        for keyword in self.mood_keywords[detected_mood]:

            if keyword in text_lower:
                matched_keywords.append(keyword)

        return {
            "mood": detected_mood,
            "sentiment": sentiment,
            "polarity": round(polarity, 3),
            "subjectivity": round(subjectivity, 3),
            "matched_keywords": matched_keywords
        }


# ---------------------------------------
# 3. TEST SENTIMENT ANALYZER
# ---------------------------------------

if __name__ == "__main__":

    analyzer = SentimentAnalyzer()

    test_sentences = [

        "I am feeling very happy today.",

        "I had a terrible day and feel lonely.",

        "I want to watch a romantic love story.",

        "I want an adventurous movie with exploration.",

        "I need an exciting action movie.",

        "I had a stressful day and want something relaxing.",

        "I feel scared and want a horror movie.",

        "I want something deep and meaningful to think about.",

        "I feel wonderful today.",

        "I feel terrible today."
    ]

    print("\nMOVIEFLIX SENTIMENT ANALYSIS")
    print("=" * 65)

    for sentence in test_sentences:

        result = analyzer.analyze_mood(sentence)

        print("\nUser input:", sentence)
        print("Detected mood:", result["mood"])
        print("Sentiment:", result["sentiment"])
        print("Polarity:", result["polarity"])
        print("Matched keywords:", result["matched_keywords"])

        print("-" * 65)
