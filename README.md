# GenFinder V1.0
*GenFinder is a Python command-line tool that allows you to easily fetch song information (metadata) and/or lyrics from Genius, using a Spotify or SoundCloud link.*


## Installation

- Clone this repo or copy the ```genfinder.py``` script.

- Install dependencies:

```bash
pip install requests beautifulsoup4
```

- **IMPORTANT :** Edit the script to insert your Genius API token in the GENIUS_ACCESS_TOKEN variable (line 32).
## Features

- Extract metadata (title, artist, album, release date, Genius URL) from a Spotify or SoundCloud track.

- Retrieve song lyrics from the corresponding Genius page.

- Option to get only lyrics, only metadata, or both.

- Output available in text or JSON format.

- Option to save the output to a file (text or JSON) in a specified folder.



## Usage

### Running the script : 

Spotify links :

```bash
python3 genfinder.py -sp <Spotify_URL> [-l|-d] [-o json|text] [-f [folder]]
```

Soundcloud links :

```bash
python3 genfinder.py -sc <SoundCloud_URL> [-l|-d] [-o json|text] [-f [folder]]
```

### Main options:

- ```-sp, --spotify``` : Spotify track URL

- ```-sc, --soundcloud``` : SoundCloud track URL

- ```-l, --lyrics``` : return only the lyrics

- ```-d, --data``` : return only the song metadata

- ```-o, --output``` : output format, text (default) or json

- ```-f, --file``` : save output to a file in the specified folder *(optional; current folder if not specified)*

### Examples:

Display lyrics and metadata as text for a Spotify link:

```bash
python3 genfinder.py -sp https://open.spotify.com/intl-fr/track/5Z13nj0hnn0ynBtN8PYaR8?si=cc0d118162a64a87
```

Display only lyrics in JSON and save to a folder:

```bash
python3 genfinder.py -sp https://open.spotify.com/intl-fr/track/2n5pHN9TUgsZg7vv5CCkq8?si=3d90ecf7bc5d4dbf -l -o json -f ./lyrics
```

Display only metadata for a SoundCloud track:

```bash
python3 genfinder.py -sc https://soundcloud.com/kronomuzik/baise-un-raciste-master -d
```
## Authors

- [@ElouannLN](https://github.com/ElouannLN)

