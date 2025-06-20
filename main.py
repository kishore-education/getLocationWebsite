
import requests
import telegram
import os
import csv
import uuid
import asyncio

BASE_URL = "http://64.227.132.105:3000"

TELEGRAM_BOT_TOKEN = '7311171550:AAGXZ6fQWsPO30_FRZl3MCgXssvRaYFgiQM'
TELEGRAM_CHAT_ID = '5408718071'

def search_songs(query, page=0, limit=10):
    url = f"{BASE_URL}/api/search/songs"
    params = {"query": query, "page": page, "limit": limit}
    response = requests.get(url, params=params)
    return response.json()

def search_albums(query, page=0, limit=10):
    url = f"{BASE_URL}/api/search/albums"
    params = {"query": query, "page": page, "limit": limit}
    response = requests.get(url, params=params)
    return response.json()

def search_artists(query, page=0, limit=10):
    url = f"{BASE_URL}/api/search/artists"
    params = {"query": query, "page": page, "limit": limit}
    response = requests.get(url, params=params)
    return response.json()

def search_playlists(query, page=0, limit=10):
    url = f"{BASE_URL}/api/search/playlists"
    params = {"query": query, "page": page, "limit": limit}
    response = requests.get(url, params=params)
    return response.json()

def get_song_by_id(song_id):
    url = f"{BASE_URL}/api/songs/{song_id}"
    response = requests.get(url)
    return response.json()

def send_song_to_telegram(song_url, song_name, song_id=None, details=None):
    # Helper to save song details to CSV
    def save_song_to_csv(song_id, data):
        csv_file = 'songs_metadata.csv'
        file_exists = os.path.isfile(csv_file)
        with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['unique_id', 'song_id', 'title', 'artist', 'album', 'year', 'label', 'language', 'duration', 'image_url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                'unique_id': data.get('unique_id', ''),
                'song_id': song_id,
                'title': data.get('title', ''),
                'artist': data.get('artist', ''),
                'album': data.get('album', ''),
                'year': data.get('year', ''),
                'label': data.get('label', ''),
                'language': data.get('language', ''),
                'duration': data.get('duration', ''),
                'image_url': data.get('image_url', '')
            })

    async def send():
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        # Download the song file
        file_response = requests.get(song_url, stream=True)
        temp_filename = f"temp_{song_name}.mp3"
        with open(temp_filename, 'wb') as f:
            for chunk in file_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # --- Download song details for metadata and save to CSV ---
        song_details = details
        unique_id = str(uuid.uuid4())
        if song_details is None and song_id is not None:
            try:
                song_details = get_song_by_id(song_id)
            except Exception:
                song_details = {}
        if song_details is None:
            song_details = {}
        song_details['unique_id'] = unique_id
        save_song_to_csv(song_id or '', song_details)

        # Send the song to Telegram
        with open(temp_filename, 'rb') as audio_file:
            await bot.send_audio(
                chat_id=TELEGRAM_CHAT_ID,
                audio=audio_file,
                title=song_details.get('title', song_name),
                performer=song_details.get('artist', ''),
                caption=f"{song_details.get('title', song_name)} by {song_details.get('artist', '')}"
            )
        os.remove(temp_filename)

    asyncio.run(send())


if __name__ == "__main__":
    query = input("Enter the song name to search: ")
    results = search_songs(query)
    if results and 'results' in results and results['results']:
        song = results['results'][0]
        song_url = song['downloadUrl'][0]['link']
        song_name = song['title']
        song_id = song['id']
        print(f"Sending '{song_name}' to Telegram...")
        send_song_to_telegram(song_url, song_name, song_id, song)
        print("Done!")
    else:
        print("No songs found for your query.")
