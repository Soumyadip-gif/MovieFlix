
// ==========================================
// MOVIEFLIX FRONTEND CONFIGURATION
// ==========================================

const API_URL = "http://127.0.0.1:5000";

const FALLBACK_POSTER =
    "https://placehold.co/300x450/191920/ffffff?text=Poster+Unavailable";


// ==========================================
// 1. DISPLAY MOVIE CARDS
// ==========================================

function displayMovies(movies, containerId) {

    const container = document.getElementById(containerId);

    if (!container) {
        console.error(`Container not found: ${containerId}`);
        return;
    }

    container.innerHTML = "";

    if (!Array.isArray(movies) || movies.length === 0) {

        container.innerHTML = `
            <p class="empty-message">
                No movies found. Try another search.
            </p>
        `;

        return;
    }

    movies.forEach(movie => {

        const card = document.createElement("div");
        card.className = "movie-card";


        // New dataset fields

        const title = movie.title || "Unknown Movie";

        const genre = movie.genres || "Genre unavailable";

        const year = movie.release_year || "Year unavailable";

        const rating = movie["IMDB Score"] ?? "N/A";

        const poster = movie.poster_url || "";


        // ==================================
        // POSTER IMAGE
        // ==================================

        const image = document.createElement("img");

        image.className = "movie-poster";

        image.alt = `${title} poster`;

        image.loading = "lazy";

        image.onerror = function () {

            this.onerror = null;

            this.src = FALLBACK_POSTER;

        };

        image.src =
            typeof poster === "string" &&
            /^https?:\/\//i.test(poster.trim())
                ? poster.trim()
                : FALLBACK_POSTER;


        // ==================================
        // MOVIE INFORMATION
        // ==================================

        const info = document.createElement("div");

        info.className = "movie-info";


        const heading = document.createElement("h4");

        heading.textContent = title;


        const yearText = document.createElement("p");

        yearText.textContent = `Year: ${year}`;


        const genreText = document.createElement("p");

        genreText.textContent = genre;


        const ratingText = document.createElement("p");

        ratingText.className = "rating";

        ratingText.textContent = `⭐ IMDb: ${rating}`;


        info.append(
            heading,
            yearText,
            genreText,
            ratingText
        );


        // ==================================
        // RECOMMENDATION SCORE
        // ==================================

        if (movie.final_score !== undefined) {

            const scoreText = document.createElement("p");

            scoreText.className = "recommendation-score";

            scoreText.textContent =
                `Match score: ${Number(movie.final_score).toFixed(1)}`;

            info.appendChild(scoreText);

        }


        // ==================================
        // RECOMMENDATION EXPLANATION
        // ==================================

        if (movie.explanation) {

            const explanation = document.createElement("p");

            explanation.className = "movie-explanation";

            explanation.textContent = movie.explanation;

            info.appendChild(explanation);

        }


        // ==================================
        // IMDb LINK
        // ==================================

        if (movie.imdb_id) {

            const link = document.createElement("a");

            link.href =
                `https://www.imdb.com/title/${encodeURIComponent(movie.imdb_id)}/`;

            link.target = "_blank";

            link.rel = "noopener noreferrer";

            link.className = "movie-link";

            link.textContent = "View on IMDb";

            info.appendChild(link);

        }


        card.append(image, info);

        container.appendChild(card);

    });

}


// ==========================================
// 2. MOVIE TITLE RECOMMENDATIONS
// ==========================================

async function searchMovies() {

    const movieInput = document.getElementById("movieSearch");

    const message = document.getElementById("searchMessage");

    const button = document.getElementById("searchButton");

    const title = movieInput.value.trim();


    if (!title) {

        message.textContent = "Please enter a movie name.";

        return;

    }


    button.disabled = true;

    message.textContent = "Finding similar movies...";


    try {

        const response = await fetch(`${API_URL}/api/recommend`, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                title: title,

                count: 10

            })

        });


        const data = await response.json();


        if (!response.ok || !data.success) {

            throw new Error(
                data.message ||
                data.error ||
                "Could not find recommendations."
            );

        }


        const matchedTitle =
            data.matched_movie || data.input_movie || title;


        message.textContent =
            `Movies similar to ${matchedTitle}` +
            (data.matched_year ? ` (${data.matched_year})` : "");


        displayMovies(
            data.recommendations,
            "similarMovies"
        );


    } catch (error) {

        console.error("Movie recommendation error:", error);

        message.textContent = error.message;

        displayMovies([], "similarMovies");


    } finally {

        button.disabled = false;

    }

}


// Search button event

document
    .getElementById("searchButton")
    .addEventListener("click", searchMovies);


// ==========================================
// 3. MOOD RECOMMENDATIONS
// ==========================================

document.querySelectorAll(".mood-card").forEach(button => {

    button.addEventListener("click", async () => {

        const mood = button.dataset.mood;

        const message = document.getElementById("moodMessage");


        // Highlight selected mood

        document.querySelectorAll(".mood-card").forEach(card => {

            card.classList.remove("selected");

        });

        button.classList.add("selected");


        message.textContent = "Finding movies for your mood...";


        try {

            const response = await fetch(`${API_URL}/api/mood`, {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    mood: mood,

                    count: 10

                })

            });


            const data = await response.json();


            if (!response.ok || !data.success) {

                throw new Error(
                    data.error || "Mood recommendations are unavailable."
                );

            }


            message.textContent =
                `Recommended movies for: ${mood}`;


            displayMovies(
                data.recommendations,
                "moodMovies"
            );


        } catch (error) {

            console.error("Mood recommendation error:", error);

            message.textContent = error.message;

        }

    });

});


// ==========================================
// 4. AI NATURAL LANGUAGE RECOMMENDATIONS
// ==========================================

document
    .getElementById("analyzeButton")
    .addEventListener("click", async () => {

        const text =
            document.getElementById("moodInput").value.trim();

        const message =
            document.getElementById("aiMessage");

        const button =
            document.getElementById("analyzeButton");


        if (!text) {

            message.textContent =
                "Please describe what you want to watch.";

            return;

        }


        button.disabled = true;

        message.textContent =
            "Analyzing your preferences...";


        try {

            const response = await fetch(`${API_URL}/api/analyze`, {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    text: text,

                    count: 10

                })

            });


            const data = await response.json();


            if (!response.ok || !data.success) {

                throw new Error(
                    data.error || "AI analysis is unavailable."
                );

            }


            if (data.analysis) {

                message.textContent =
                    `Detected mood: ${data.analysis.mood || "Unknown"} | ` +
                    `Sentiment: ${data.analysis.sentiment || "Unknown"}`;

            } else {

                message.textContent =
                    "Your recommendations are ready.";

            }


            displayMovies(
                data.recommendations,
                "aiMovies"
            );


        } catch (error) {

            console.error("AI recommendation error:", error);

            message.textContent = error.message;


        } finally {

            button.disabled = false;

        }

});


// ==========================================
// 5. MOVIE SEARCH AUTOCOMPLETE
// ==========================================

const movieSearch =
    document.getElementById("movieSearch");

const suggestionsBox =
    document.getElementById("movieSuggestions");


let searchTimeout;

let autocompleteController;


movieSearch.addEventListener("input", () => {

    clearTimeout(searchTimeout);


    // Cancel previous request

    if (autocompleteController) {

        autocompleteController.abort();

    }


    const query = movieSearch.value.trim();


    if (query.length < 2) {

        suggestionsBox.innerHTML = "";

        suggestionsBox.style.display = "none";

        return;

    }


    searchTimeout = setTimeout(async () => {

        autocompleteController = new AbortController();


        try {

            const response = await fetch(

                `${API_URL}/api/search-movies?q=${encodeURIComponent(query)}`,

                {
                    signal: autocompleteController.signal
                }

            );


            const data = await response.json();


            suggestionsBox.innerHTML = "";


            if (
                !response.ok ||
                !data.success ||
                !Array.isArray(data.suggestions) ||
                data.suggestions.length === 0
            ) {

                suggestionsBox.style.display = "none";

                return;

            }


            data.suggestions.forEach(title => {

                const item = document.createElement("div");

                item.className = "suggestion-item";

                item.textContent = title;


                item.addEventListener("click", () => {

                    movieSearch.value = title;

                    suggestionsBox.innerHTML = "";

                    suggestionsBox.style.display = "none";

                });


                suggestionsBox.appendChild(item);

            });


            suggestionsBox.style.display = "block";


        } catch (error) {

            if (error.name !== "AbortError") {

                console.error("Autocomplete error:", error);

            }

            suggestionsBox.style.display = "none";

        }

    }, 250);

});


// ==========================================
// 6. HIDE AUTOCOMPLETE WHEN CLICKING OUTSIDE
// ==========================================

document.addEventListener("click", event => {

    if (!event.target.closest(".movie-search-wrapper")) {

        suggestionsBox.style.display = "none";

    }

});


// ==========================================
// 7. SEARCH USING ENTER KEY
// ==========================================

movieSearch.addEventListener("keydown", event => {

    if (event.key === "Enter") {

        event.preventDefault();

        suggestionsBox.style.display = "none";

        searchMovies();

    }


    if (event.key === "Escape") {

        suggestionsBox.style.display = "none";

    }

});
