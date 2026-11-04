
import requests
import re
import time
from urllib.parse import unquote


class PosterService:

    def __init__(self):

        self.commons_api_url = "https://commons.wikimedia.org/w/api.php"

        self.cache = {}
        self.last_request_time = 0
        self.request_delay = 8

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "MovieFlix/1.0 "
                "(educational movie recommendation project)"
            )
        })

    def wait_before_request(self):

        elapsed = time.time() - self.last_request_time

        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)

        self.last_request_time = time.time()

    def request_api(self, params, max_retries=4):

        for attempt in range(max_retries):

            self.wait_before_request()

            try:

                response = self.session.get(
                    self.commons_api_url,
                    params=params,
                    timeout=30
                )

                if response.status_code == 429:

                    retry_after = response.headers.get(
                        "Retry-After", "30"
                    )

                    try:
                        wait_time = int(retry_after)
                    except (ValueError, TypeError):
                        wait_time = 30

                    wait_time = max(wait_time, 15)

                    print(
                        f"Rate limited. Waiting {wait_time} seconds..."
                    )

                    time.sleep(wait_time)
                    continue

                if response.status_code in (500, 502, 503, 504):

                    wait_time = 10 * (attempt + 1)

                    print(
                        f"Server error. Retrying in {wait_time} seconds..."
                    )

                    time.sleep(wait_time)
                    continue

                response.raise_for_status()

                data = response.json()

                error_code = data.get(
                    "error", {}
                ).get("code")

                if error_code in ("ratelimited", "maxlag"):

                    wait_time = 20 * (attempt + 1)

                    print(
                        f"API limit reached. Waiting {wait_time} seconds..."
                    )

                    time.sleep(wait_time)
                    continue

                return data

            except requests.RequestException as error:

                print("Request failed:", error)

                if attempt == max_retries - 1:
                    raise

                time.sleep(10 * (attempt + 1))

        raise RuntimeError("Maximum API retries reached.")

    @staticmethod
    def normalize_title(title):

        title = unquote(str(title)).lower()

        title = re.sub(
            r"\.(jpg|jpeg|png|webp|gif|tif|svg)$",
            "",
            title
        )

        title = re.sub(
            r"\s*\((18|19|20)\d{2}\)",
            "",
            title
        )

        title = re.sub(
            r"[^a-z0-9]",
            "",
            title
        )

        return title

    @staticmethod
    def extract_year(title):

        match = re.search(
            r"\((18|19|20)\d{2}\)",
            str(title)
        )

        if match:
            return match.group(0)[1:-1]

        return None

    @staticmethod
    def clean_movie_title(title):

        return re.sub(
            r"\s*\((18|19|20)\d{2}\)",
            "",
            str(title)
        ).strip()

    @staticmethod
    def title_words(title):

        ignored_words = {
            "the", "a", "an", "of", "and",
            "in", "on", "at", "to"
        }

        words = re.findall(
            r"[a-z0-9]+",
            title.lower()
        )

        return {
            word for word in words
            if word not in ignored_words
        }

    def search_commons(self, query):

        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": 30,
            "prop": "imageinfo",
            "iiprop": "url|size|mime",
            "iiurlwidth": 500
        }

        data = self.request_api(params)

        return data.get(
            "query", {}
        ).get("pages", {})

    @staticmethod
    
    def is_valid_image_url(self, url):

        if not url:
            return False

        try:
            response = self.session.get(
                url,
                headers={"Range": "bytes=0-1023"},
                stream=True,
                timeout=20
            )

            try:
                if response.status_code not in (200, 206):
                    return False

                content_type = response.headers.get(
                    "Content-Type", ""
                ).lower()

                if content_type.startswith("image/"):
                    return True

                # Check image file signatures if the server
                # does not provide a useful content type.
                image_bytes = response.raw.read(12)

                signatures = (
                    image_bytes.startswith(b"\xff\xd8\xff"),  # JPEG
                    image_bytes.startswith(b"\x89PNG\r\n\x1a\n"),  # PNG
                    image_bytes.startswith(b"GIF8"),  # GIF
                    image_bytes.startswith(b"RIFF")
                    and image_bytes[8:12] == b"WEBP"  # WEBP
                )

                return any(signatures)

            finally:
                response.close()

        except requests.RequestException as error:

            print("Image validation error:", error)
            return False


    def find_poster(self, title):

        if not title:
            return None

        title = str(title).strip()

        if title in self.cache:
            return self.cache[title]

        clean_title = self.clean_movie_title(title)

        year = self.extract_year(title)

        normalized_movie = self.normalize_title(
            clean_title
        )

        movie_words = self.title_words(clean_title)

        if not normalized_movie or not movie_words:
            return None

        print(
            f"\nSearching Wikimedia Commons for: {title}"
        )

        search_queries = []

        if year:

            search_queries.append(
                f'"{clean_title}" {year} poster'
            )

        search_queries.extend([
            f'"{clean_title}" movie poster',
            f'"{clean_title}" film poster',
            f'{clean_title} theatrical poster',
            f'{clean_title} poster'
        ])

        candidates = {}

        try:

            for query in search_queries:

                print("Search query:", query)

                pages = self.search_commons(query)

                for page in pages.values():

                    candidates[page["title"]] = page

                print(
                    "Candidates collected:",
                    len(candidates)
                )

            if not candidates:

                print("No Wikimedia Commons results.")

                self.cache[title] = None

                return None

            print("\nCandidate filenames:")

            for filename in list(candidates.keys())[:20]:
                print(" -", filename)

            best_poster = None
            best_score = 0

            rejected_words = {
                "logo", "icon", "screenshot",
                "scene", "still", "photograph",
                "photo", "collage", "soundtrack",
                "album", "banner", "wallpaper",
                "character", "portrait"
            }

            for page in candidates.values():

                file_title = page.get("title", "")

                filename_lower = file_title.lower()

                image_info = page.get("imageinfo", [])

                if not image_info:
                    continue

                info = image_info[0]

                # Only accept common poster image formats.
                if info.get("mime") not in (
                    "image/jpeg",
                    "image/png",
                    "image/webp"
                ):
                    continue

                width = info.get("width", 0)
                height = info.get("height", 0)

                if width < 250 or height < 350:
                    continue

                ratio = width / height if height else 0

                # Reject landscape images.
                if not (0.50 <= ratio <= 0.85):
                    continue

                # Reject clearly unrelated file types.
                filename_words = set(
                    re.findall(
                        r"[a-z0-9]+",
                        filename_lower
                    )
                )

                if filename_words.intersection(rejected_words):

                    print("Rejected image:", file_title)
                    continue

                
                normalized_file = self.normalize_title(file_title)

                file_words = self.title_words(file_title)

                # Reject logos, photographs and unrelated artwork.
                rejected_words = {
                    "logo", "icon", "screenshot",
                    "scene", "still", "photograph",
                    "photo", "collage", "soundtrack",
                    "album", "banner", "wallpaper",
                    "character", "portrait"
                }

                filename_words = set(
                    re.findall(r"[a-z0-9]+", filename_lower)
                )

                if filename_words.intersection(rejected_words):
                    print("Rejected image:", file_title)
                    continue

                # Require all meaningful movie title words.
                if not movie_words.issubset(file_words):
                    print("Title mismatch:", file_title)
                    continue

                if normalized_movie not in normalized_file:
                    print("Normalized title mismatch:", file_title)
                    continue

                # Reject candidates explicitly associated with
                # a different release year.
                file_years = re.findall(
                    r"(?<!\d)(?:18|19|20)\d{2}(?!\d)",
                    file_title
                )

                if year and file_years and year not in file_years:
                    print("Release year mismatch:", file_title)
                    continue

                # Reject known misleading Titanic artwork.
                if (
                    normalized_movie == "titanic"
                    and normalized_file.startswith("savedfrom")
                ):
                    print("Rejected unrelated Titanic artwork:", file_title)
                    continue

                # Prefer clearly identified movie posters.
                if "poster" not in filename_lower:
                    print("Not identified as a poster:", file_title)
                    continue

                score = 10

                if "theatrical" in filename_lower:
                    score += 5

                if year and year in file_years:
                    score += 10

                ratio = width / height if height else 0

                if 0.55 <= ratio <= 0.85:
                    score += 3

                image_url = (
                    info.get("thumburl")
                    or info.get("url")
                )

                if image_url and score > best_score:
                    best_score = score
                    best_poster = image_url


            if best_poster:

                print("\nPoster candidate found!")

                print("Score:", best_score)

                print("Checking image URL...")

                if self.is_valid_image_url(best_poster):

                    print("Valid image URL.")

                    self.cache[title] = best_poster

                    return best_poster

                print("Image URL validation failed.")

            print("No verified poster candidate found.")

            self.cache[title] = None

            return None

        except Exception as error:

            print(
                f"Poster lookup error for {title}: {error}"
            )

            # Temporary failures are not permanently cached.
            return None

    def close(self):

        self.session.close()


if __name__ == "__main__":

    service = PosterService()

    try:

        test_movies = [
            "Scream 3 (2000)",
            "The Tigger Movie (2000)",
            "Mission to Mars (2000)",
            "American Psycho (2000)",
            "Titanic (1997)"
        ]

        for movie in test_movies:

            print("\n" + "=" * 60)

            print("MOVIE:", movie)

            print("=" * 60)

            poster = service.find_poster(movie)

            if poster:

                print("\nRESULT: Poster found")

            else:

                print("\nRESULT: Poster not found")

    finally:

        service.close()
