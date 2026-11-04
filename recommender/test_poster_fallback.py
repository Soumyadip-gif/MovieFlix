
import requests
import time
import re

TEST_MOVIES = [
    ("The Shawshank Redemption", 1994),
    ("Operation Dumbo Drop", 1995),
    ("Notorious", 1946),
    ("Repulsion", 1965),
    ("Tokyo Decadence", 1992),
]

COMMONS_API = "https://commons.wikimedia.org/w/api.php"

session = requests.Session()
session.headers.update({
    "User-Agent": "MovieFlixPosterTester/1.0 (educational project)"
})


def clean_text(value):
    return re.sub(r"[^a-z0-9]", "", value.lower())


def search_commons(title, year):
    search_query = f'"{title}" {year} film poster'

    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": search_query,
        "gsrnamespace": 6,
        "gsrlimit": 10,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": 400,
        "format": "json",
    }

    try:
        response = session.get(
            COMMONS_API,
            params=params,
            timeout=20
        )
        response.raise_for_status()

        pages = response.json().get("query", {}).get("pages", {})
        candidates = []

        for page in pages.values():
            info_list = page.get("imageinfo", [])

            if not info_list:
                continue

            info = info_list[0]
            file_title = page.get("title", "")
            normalized_title = clean_text(title)
            normalized_file = clean_text(file_title)

            # Basic title matching
            if normalized_title not in normalized_file:
                continue

            metadata = info.get("extmetadata", {})

            candidates.append({
                "file": file_title,
                "url": info.get("thumburl", info.get("url", "")),
                "license": metadata.get(
                    "LicenseShortName", {}
                ).get("value", "Unknown"),
            })

        return candidates

    except requests.RequestException as error:
        print("Search error:", error)
        return []


def verify_image(url):
    try:
        response = session.get(
            url,
            timeout=20,
            stream=True
        )

        content_type = response.headers.get("Content-Type", "")

        working = (
            response.status_code == 200
            and content_type.startswith("image/")
        )

        response.close()
        return working

    except requests.RequestException:
        return False


def main():
    print("\nMOVIEFLIX TITLE + YEAR POSTER TEST")
    print("=" * 65)

    for title, year in TEST_MOVIES:
        print(f"\nMOVIE: {title} ({year})")
        print("-" * 65)

        candidates = search_commons(title, year)

        if not candidates:
            print("No matching candidates found.")
            time.sleep(2)
            continue

        for index, candidate in enumerate(candidates, start=1):
            working = verify_image(candidate["url"])

            print(f"\nCandidate {index}")
            print("File:", candidate["file"])
            print("Image working:", working)
            print("License:", candidate["license"])
            print("URL:", candidate["url"])

        time.sleep(2)

    print("\n" + "=" * 65)
    print("TEST COMPLETED")
    print("Original dataset remains unchanged.")


if __name__ == "__main__":
    main()
