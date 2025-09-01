import os
import csv
import requests
from bs4 import BeautifulSoup

CSV_FILENAME = "modules_catalog.csv"
DOWNLOAD_URL_TEMPLATE = "https://api.modarchive.org/downloads.php?moduleid={mod_id}"
MODULE_PAGE_TEMPLATE = "https://modarchive.org/index.php?request=view_by_moduleid&query={mod_id}"

def fetch_html(mod_id: int) -> BeautifulSoup:
    url = MODULE_PAGE_TEMPLATE.format(mod_id=mod_id)
    resp = requests.get(url)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def scrape_metadata(soup: BeautifulSoup) -> dict:
    info_div = soup.find("##", text="Info")
    # Instead use find the section by heading
    info_section = None
    for header in soup.find_all(['h6', 'h3', 'h2', 'h4']):
        if header.text.strip() == "Info":
            info_section = header.find_next_sibling("ul") or header.find_next("p")
            break
    data = {k: "Unknown" for k in ["mod_id","md5","format","channels","genre","artist"]}

    if info_section:
        text = info_section.get_text(separator="\n")
        for line in text.splitlines():
            if "Mod Archive ID:" in line:
                data["mod_id"] = line.split(":",1)[1].strip()
            elif "MD5:" in line:
                data["md5"] = line.split(":",1)[1].strip()
            elif "Format:" in line:
                data["format"] = line.split(":",1)[1].strip()
            elif "Channels:" in line:
                data["channels"] = line.split(":",1)[1].strip()
            elif "Genre:" in line:
                data["genre"] = line.split(":",1)[1].strip()

    for header in soup.find_all(['h2']):
        if header.find(text=True, recursive=False).strip() == "Registered Artist(s):":
            artists_ul = header.find_next_sibling("ul")
            if artists_ul is not None:
                artists = [artist_li.text.strip() for artist_li in artists_ul.findAll('li')]
                data["artist"] = ', '.join(artists)

    return data

def download_module(mod_id: int, dest_path: str):
    url = DOWNLOAD_URL_TEMPLATE.format(mod_id=mod_id)
    resp = requests.get(url)
    resp.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(resp.content)

def ensure_csv_exists(csv_path: str):
    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ModArchiveID", "Name", "MD5", "Format", "Channels", "Genre", "Artist", "RelativePath"])

def sanitize_filename(s: str) -> str:
    return "".join(c for c in s if c.isalnum() or c in " _-").strip()

def update_metadata_csv(csv_path: str, new_row: dict):
    """Update or insert a row into the CSV file based on ModArchiveID."""
    fieldnames = ["ModArchiveID", "Name", "MD5", "Format", "Channels", "Genre", "Artist", "RelativePath"]
    rows = []

    # Load existing rows if the file exists
    ensure_csv_exists(CSV_FILENAME)
    if os.path.exists(csv_path):
        with open(csv_path, "r", newline="", encoding="utf -8") as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                if row["ModArchiveID"] != str(new_row["ModArchiveID"]):
                    rows.append(row)

    # Append the new/updated row
    rows.append(new_row)

    # Rewrite the CSV with all rows
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)


def main(args):
    soup = fetch_html(args.mod_id)
    meta = scrape_metadata(soup)

    # Fallback naming
    title_header = soup.find("h1") or soup.find("h2")
    title = (title_header.find(text=True, recursive=False).strip() if title_header else f"module_{mod_id}") if args.name is None else args.name

    artist = meta["artist"] if args.artist is None else args.artist
    genre = meta["genre"] or "Unknown" if args.genre is None else args.genre
    fmt = meta["format"].lower() or "mod"
    ext = fmt
    genre_dir = sanitize_filename(genre) 
    base = sanitize_filename(title)
    artist_s = sanitize_filename(artist)
    filename = f"{base}-{artist_s}.{ext}"
    dest_dir = os.path.join(".", genre_dir)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, filename)

    print(f"Downloading module #{args.mod_id} → {dest_path}")
    download_module(args.mod_id, dest_path)

    update_metadata_csv(CSV_FILENAME, {
        "ModArchiveID": meta["mod_id"],
        "Name": title,
        "MD5": meta["md5"],
        "Format": meta["format"],
        "Channels": meta["channels"],
        "Genre": genre,
        "Artist": artist, 
		"RelativePath": dest_path,
    })


    print(f"Metadata appended to {CSV_FILENAME}:\n"
          f"  ID: {meta['mod_id']}\n"
          f"  Title: {title}\n"
          f"  MD5: {meta['md5']}\n"
          f"  Format: {meta['format']}\n"
          f"  Channels: {meta['channels']}\n"
          f"  Genre: {genre}\n"
          f"  Artist: {artist}\n"
          f"  File location: {dest_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("mod_id", type=int, help="ModArchive module ID")
    parser.add_argument("--artist", default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--genre", default=None)
    args = parser.parse_args()
    main(args)