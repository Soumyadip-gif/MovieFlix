# 🎬 MovieFlix – AI-Powered Movie Recommendation System

MovieFlix is an AI-powered movie recommendation web application that helps users discover movies based on their interests and movie preferences.

It uses content-based filtering, TF-IDF feature extraction, and semantic understanding to recommend movies with similar characteristics.

## ✨ Features

- **AI Movie Recommendations:** Discover similar movies based on a selected movie.
- **Semantic Similarity:** Uses Sentence Transformers to understand movie descriptions.
- **Content-Based Filtering:** Analyzes genres, overviews, cast, directors, and keywords.
- **Movie Search:** Search for movies by title.
- **Movie Dataset:** Contains more than 45,000 movie records.
- **Movie Posters:** Displays movie posters using available poster image URLs.
- **Web Interface:** Interactive frontend built with HTML, CSS, and JavaScript.
- **REST API:** Flask-powered backend for movie search and recommendations.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend development |
| Flask | Web application and API |
| Pandas | Dataset processing |
| NumPy | Numerical operations |
| Scikit-learn | TF-IDF and similarity calculations |
| Sentence Transformers | Semantic embeddings |
| HTML | Webpage structure |
| CSS | Styling and layout |
| JavaScript | Frontend functionality |

## 📁 Project Structure

```text
MovieFlix/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   └── movieflix_movies.csv
│
├── recommender/
│   ├── content_recommender_v2.py
│   ├── poster_service.py
│   ├── sentiment_analyzer.py
│   └── ...
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
└── templates/
    └── index.html
```

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Soumyadip-gif/MovieFlix.git
```

### 2. Navigate to the Project

```bash
cd MovieFlix
```

### 3. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\Activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
python app.py
```

Open the local URL displayed in your terminal in a web browser.

**Note:** The application requires `data/movieflix_movies.csv`. The Sentence Transformers model may download automatically the first time the recommender initializes. An internet connection is required for model downloads and externally hosted movie posters.

## 🧠 Recommendation System

MovieFlix uses a hybrid feature-based and semantic approach to movie recommendations.

The recommendation engine analyzes:

- Genres
- Movie overviews
- Cast
- Directors
- Keywords
- Semantic overview embeddings

It combines TF-IDF feature representations with semantic embeddings to calculate movie similarity and identify relevant recommendations.

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Homepage |
| GET | `/api/movies` | Retrieve movie data |
| GET | `/api/search-movies` | Search movies |
| POST | `/api/recommend` | Generate movie recommendations |

## 🚀 Future Improvements

- Improve movie poster availability.
- Enhance recommendation accuracy.
- Integrate mood-based recommendations.
- Add user accounts and personalized watchlists.
- Add movie ratings and reviews.
- Improve the user interface and experience.

## 👨‍💻 Developer

**Soumyadip**

GitHub: [@Soumyadip-gif](https://github.com/Soumyadip-gif)

## 📌 Repository

[MovieFlix – GitHub Repository](https://github.com/Soumyadip-gif/MovieFlix)

---

⭐ If you find this project interesting, consider starring the repository!