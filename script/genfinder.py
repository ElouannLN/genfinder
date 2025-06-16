#!/usr/bin/env python3
"""
GenFinder – Fetch song information and/or lyrics from Genius
using a Spotify or SoundCloud link.

Usage examples:
    python3 genfinder.py -sp <URL> -l
    python3 genfinder.py -sc <URL> -d -o json -f /chemin/vers/dossier

Options:
    -sp, --spotify    Spotify track URL (mutually exclusive with -sc)
    -sc, --soundcloud SoundCloud track URL (mutually exclusive with -sp)
    -l, --lyrics      Return only the lyrics
    -d, --data        Return only the song metadata
    -o, --output      Output format: "text" (default) or "json"
    -f, --file        Save output to file in specified folder (optional argument).
                      If no folder is given, save to current directory.
"""

import argparse
import json
import os
import re
import sys
from typing import Tuple, Optional

import requests
from bs4 import BeautifulSoup

GENIUS_API_BASE = "https://api.genius.com"
GENIUS_ACCESS_TOKEN = (
    "[/!\ YOUR GENIUS ACCESS TOKEN HERE /!\]" #MAKE SURE TO PUT YOUR GENIUS ACCESS API TOKEN HERE !!!
)


def _get_spotify_metadata(url: str) -> Tuple[str, str]:
    """
    Retrieve track and artist information from a Spotify track URL
    using Spotify's public oEmbed endpoint.

    Raises:
        ValueError: If metadata cannot be extracted or the URL is invalid.
    """
    try:
        response = requests.get(f"https://open.spotify.com/oembed?url={url}", timeout=10)
        response.raise_for_status()
        data = response.json()
        title = data.get("title")
        if not title:
            raise ValueError("Invalid Spotify metadata: title not found.")

        parts = [p.strip() for p in title.split(" - ")]
        if len(parts) >= 2:
            return parts[0], parts[-1]
        return title, ""
    except requests.RequestException as e:
        raise ValueError(f"Invalid or unreachable Spotify URL: {e}")
    except (KeyError, json.JSONDecodeError) as e:
        raise ValueError(f"Malformed Spotify response: {e}")

def _get_soundcloud_metadata(url: str) -> Tuple[str, str]:
    """
    Retrieve track and artist information from a SoundCloud track URL
    using SoundCloud's public oEmbed endpoint.

    Raises:
        ValueError: If metadata cannot be extracted or the URL is invalid.
    """
    try:
        response = requests.get(f"https://soundcloud.com/oembed?format=json&url={url}", timeout=10)
        response.raise_for_status()
        data = response.json()
        title = data.get("title")
        if not title:
            raise ValueError("Invalid SoundCloud metadata: title not found.")

        parts = [p.strip() for p in title.split(" - ")]
        if len(parts) >= 2:
            return " - ".join(parts[1:]), parts[0]
        return title, ""
    except requests.RequestException as e:
        raise ValueError(f"Invalid or unreachable SoundCloud URL: {e}")
    except (KeyError, json.JSONDecodeError) as e:
        raise ValueError(f"Malformed SoundCloud response: {e}")

def _search_genius(track: str, artist: str, token: str) -> Optional[int]:
    headers = {"Authorization": f"Bearer {token}"}
    query = f"{track} {artist}".strip()
    response = requests.get(f"{GENIUS_API_BASE}/search", headers=headers, params={"q": query}, timeout=10)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            sys.stderr.write(f"[ERROR] Invalid Genius API access token: {e}")
            sys.exit(1)
        else:
            raise e
    hits = response.json()["response"]["hits"]
    artist_lower = artist.lower()

    for hit in hits:
        primary_artist = hit["result"]["primary_artist"]["name"].lower()
        if artist_lower and artist_lower in primary_artist:
            return hit["result"]["id"]

    if hits:
        return hits[0]["result"]["id"]
    return None


def _get_genius_song(song_id: int, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{GENIUS_API_BASE}/songs/{song_id}", headers=headers, timeout=10)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            sys.stderr.write("[ERROR] Invalid Genius API access token (HTTP 401 Unauthorized).\n")
            sys.exit(1)
        else:
            raise e
    return response.json()["response"]["song"]


def _scrape_genius_lyrics(url: str) -> str:
    """
    Scrape the lyrics from the Genius song webpage.
    Excludes elements marked with 'data-exclude-from-selection' to avoid
    unwanted content like ads or annotations.

    Args:
        url (str): URL of the Genius song page.

    Returns:
        str: Cleaned lyrics text.
    """
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    lyrics_containers = soup.find_all("div", {"data-lyrics-container": "true"})
    lyrics_lines = []

    for container in lyrics_containers:
        for excluded in container.find_all(attrs={"data-exclude-from-selection": True}):
            excluded.extract()

        text = container.get_text(separator="\n").strip()
        if text:
            lyrics_lines.append(text)

    return "\n".join(lyrics_lines)


def _print_metadata(song: dict) -> str:
    """
    Format the song metadata into a readable multiline string.

    Args:
        song (dict): Song metadata dictionary.

    Returns:
        str: Formatted string containing key song information.
    """
    parts = [
        f"Title : {song.get('title')}",
        f"Artist: {song['primary_artist']['name']}",
    ]
    if song.get("album"):
        parts.append(f"Album : {song['album']['name']}")
    if song.get("release_date"):
        parts.append(f"Date  : {song['release_date']}")
    parts.append(f"URL   : {song.get('url')}")
    return "\n".join(parts)


def _sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be safe for use as a filename by removing
    unsafe characters and replacing spaces with underscores.

    Args:
        name (str): Original filename string.

    Returns:
        str: Sanitized filename string.
    """
    return re.sub(r'[^\w\s\-_().]', '', name).strip().replace(" ", "_")


def _write_to_file(content: str, title: str, folder_path: str, extension: str = "txt"):
    """
    Write the given content to a file named after the song title
    inside the specified folder. Creates the folder if it does not exist.

    Args:
        content (str): Content to write into the file.
        title (str): Title of the song used to create the filename.
        folder_path (str): Destination folder path.
        extension (str): File extension (default is 'txt').
    """
    os.makedirs(folder_path, exist_ok=True)
    filename = _sanitize_filename(title)
    filepath = os.path.join(folder_path, f"{filename}.{extension}")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n[FICHIER SAUVÉ] {filepath}")


def main() -> None:
    """
    Main entry point: parses command-line arguments, processes input URLs,
    retrieves song metadata and/or lyrics from Genius, formats output
    according to user options, and optionally writes output to a file.
    """
    parser = argparse.ArgumentParser(description="Fetch song info and/or lyrics from Genius.")
    src_group = parser.add_mutually_exclusive_group(required=True)
    src_group.add_argument("-sp", "--spotify", metavar="URL", help="Spotify track URL")
    src_group.add_argument("-sc", "--soundcloud", metavar="URL", help="SoundCloud track URL")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("-l", "--lyrics", action="store_true", help="Return only lyrics")
    mode_group.add_argument("-d", "--data", action="store_true", help="Return only song metadata")

    parser.add_argument("-o", "--output", choices=["text", "json"], default="text",
                        help="Output format (default: text)")

    parser.add_argument("-f", "--file", nargs="?", const=".", metavar="FOLDER",
                        help="Save output to specified folder, or current folder if no folder given")

    args = parser.parse_args()
    token = GENIUS_ACCESS_TOKEN

    if not token or token == "[/!\ YOUR GENIUS ACCESS TOKEN HERE /!\]":
        sys.stderr.write("[ERROR] Please set GENIUS_ACCESS_TOKEN in the script (line 32).\n")
        sys.exit(1)

    try:
        if args.spotify:
            track, artist = _get_spotify_metadata(args.spotify)
        elif args.soundcloud:
            track, artist = _get_soundcloud_metadata(args.soundcloud)
        else:
            raise ValueError("Aucune source musicale valide n'a été fournie.")
    except ValueError as e:
        sys.stderr.write(f"[ERROR] {e}\n")
        sys.exit(1)

    if not track:
        sys.stderr.write("[ERROR] Could not parse metadata from provided link.\n")
        sys.exit(1)

    song_id = _search_genius(track, artist, token)
    if not song_id:
        sys.stderr.write("[ERROR] No matching song found on Genius.\n")
        sys.exit(1)

    song = _get_genius_song(song_id, token)
    title = song.get("title", "unknown_title")

    need_lyrics = args.lyrics or (not args.data)
    lyrics = ""
    if need_lyrics:
        try:
            lyrics = _scrape_genius_lyrics(song["url"])
        except Exception as e:
            sys.stderr.write(f"[WARNING] Lyrics scraping failed: {e}\n")

    if args.output == "json":
        if args.lyrics:
            output = json.dumps({"lyrics": lyrics}, ensure_ascii=False, indent=2)
        elif args.data:
            output = json.dumps(song, ensure_ascii=False, indent=2)
        else:
            song_with_lyrics = dict(song)
            song_with_lyrics["lyrics"] = lyrics
            output = json.dumps(song_with_lyrics, ensure_ascii=False, indent=2)
    else:
        if args.lyrics:
            output = lyrics
        elif args.data:
            output = _print_metadata(song)
        else:
            output = _print_metadata(song) + "\n\n" + lyrics

    if args.file is not None:
        folder_path = args.file
        _write_to_file(output, title, folder_path, extension="json" if args.output == "json" else "txt")
    else:
        print(output)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled by user.")
