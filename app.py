from flask import Flask, request, render_template, redirect, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from googleapiclient.discovery import build
import subprocess
import os
import time

app = Flask(__name__)

# Set up Spotify API credentials
SPOTIFY_CLIENT_ID = '37eb65f6dd69432cb786943c79218bc7'
SPOTIFY_CLIENT_SECRET = '491075505c96471895d5afc7de119255'
SPOTIFY_REDIRECT_URI = 'http://localhost:8888/callback'

# Set up YouTube API key
YOUTUBE_API_KEY = 'AIzaSyBqtfqlcQ-VTyWhH8M6pxxbNm6mqRcsfL4'

def fetch_spotify_tracks(playlist_id):
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope="playlist-read-private"
    ))
    results = sp.playlist_items(playlist_id)
    tracks = []
    for item in results['items']:
        track = item['track']
        tracks.append(f"{track['name']} {track['artists'][0]['name']}")
    return tracks

def search_youtube(song_name):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        q=song_name,
        part='snippet',
        type='video',
        maxResults=1
    )
    response = request.execute()
    if response['items']:
        return f"https://www.youtube.com/watch?v={response['items'][0]['id']['videoId']}"
    return None

def write_urls_to_file(tracks, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as file:
        for track in tracks:
            file.write(f"{track}\n")

def download_songs_with_ytdlp(urls_file, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    command = [
        "yt-dlp",
        "-a", urls_file,
        "-f", "bestaudio",
        "--extract-audio",
        "--audio-format", "mp3",
        "--embed-metadata",
        "--add-metadata",
        "--embed-thumbnail",
        "--convert-thumbnails", "png",
        "-P", output_folder
    ]
    subprocess.run(command, check=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    playlist_id = request.form['playlist_id']
    folder_name = request.form['folder_name']
    output_folder = os.path.join(os.path.expanduser("~"), "Downloads", folder_name)
    urls_file = os.path.join(output_folder, "urls.txt")

    try:
        tracks = fetch_spotify_tracks(playlist_id)
        total_tracks = len(tracks)
        urls = []

        # Process each track and update progress
        for i, track in enumerate(tracks):
            url = search_youtube(track)
            if url:
                urls.append(url)
            # Simulate progress for frontend
            with open("progress.txt", "w") as progress_file:
                progress_file.write(f"{int((i + 1) / total_tracks * 100)}")

        write_urls_to_file(urls, urls_file)
        download_songs_with_ytdlp(urls_file, output_folder)

        # Indicate completion
        with open("progress.txt", "w") as progress_file:
            progress_file.write("100")

        return f"Songs downloaded to {output_folder}!"
    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == '__main__':
    app.run(debug=True)


