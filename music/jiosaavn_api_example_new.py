def is_song_uploaded(song_id):
    csv_file = 'songs_metadata.csv'
    if not os.path.isfile(csv_file):
        return False
    with open(csv_file, 'r', encoding='utf-8') as csvfile:
        for line in csvfile:
            if line.strip().startswith('song_id'):
                continue
            if f',{song_id},' in line or line.strip().endswith(f',{song_id}'):
                return True
    return False
import csv
import uuid
import os
import requests
import telegram
import asyncio

import mimetypes

def send_test_message():
    try:
        async def send():
            bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="Test message: Upload is working!")
            print("Test message sent to Telegram chat.")
        asyncio.run(send())
    except Exception as e:
        print(f"Failed to send test message: {e}")

# API configuration
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

def send_song_to_telegram(song_url, song_name, quality_label=None, image_url=None):
    # Modified: Accepts quality_label and image_url, returns file_ids
    async def send(quality_label=None, image_url=None):
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        image_file_id = image_file_unique_id = None
        temp_image_filename = None
        if image_url:
            try:
                img_resp = requests.get(image_url, stream=True)
                if img_resp.status_code == 200:
                    temp_image_filename = f"temp_{song_name}.jpg"
                    with open(temp_image_filename, 'wb') as img_file:
                        for chunk in img_resp.iter_content(chunk_size=8192):
                            if chunk:
                                img_file.write(chunk)
                    with open(temp_image_filename, 'rb') as img_file:
                        msg = await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=img_file, caption=f"{song_name} cover art")
                        if msg and msg.photo:
                            photo_info = msg.photo[-1]
                            image_file_id = photo_info.file_id
                            image_file_unique_id = photo_info.file_unique_id
                            print(f"Image for '{song_name}' sent to Telegram chat.")
            except Exception as e:
                print(f"Failed to send image for '{song_name}': {e}")
            finally:
                if temp_image_filename and os.path.exists(temp_image_filename):
                    os.remove(temp_image_filename)

        # Download the song file
        temp_filename = f"temp_{song_name}_{quality_label or 'audio'}.mp3"
        file_response = requests.get(song_url, stream=True)
        with open(temp_filename, 'wb') as f:
            for chunk in file_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Send the file to Telegram
        audio_file_id = audio_file_unique_id = None
        with open(temp_filename, 'rb') as audio_file:
            msg = await bot.send_audio(chat_id=TELEGRAM_CHAT_ID, audio=audio_file, title=song_name)
            if msg and msg.audio:
                audio_file_id = msg.audio.file_id
                audio_file_unique_id = msg.audio.file_unique_id
                print(f"Audio '{song_name}' ({quality_label}) sent to Telegram chat.")
        os.remove(temp_filename)
        return audio_file_id, audio_file_unique_id, image_file_id, image_file_unique_id
    try:
        return asyncio.run(send(quality_label=quality_label, image_url=image_url))
    except Exception as e:
        print(f"Failed to send audio or image for '{song_name}': {e}")
        return None, None, None, None

def get_album_by_id(album_id):
    url = f"{BASE_URL}/api/albums?id={album_id}"
    response = requests.get(url)
    return response.json()

def get_artist_by_id(artist_id):
    url = f"{BASE_URL}/api/artists/{artist_id}"
    response = requests.get(url)
    return response.json()

def get_playlist_by_id(playlist_id):
    url = f"{BASE_URL}/api/playlists?id={playlist_id}"
    response = requests.get(url)
    return response.json()


# New function to upload songs from search.csv by name
def upload_songs_from_csv(csv_path='search.csv'):
    print(f"Uploading songs from {csv_path}...")
    fieldnames = [
        'song_id', 'song_name', 'quality', 'audio_file_id', 'audio_file_unique_id',
        'image_file_id', 'image_file_unique_id', 'album', 'artist', 'release_date', 'duration', 'download_url', 'image_url'
    ]
    csv_file = 'songs_metadata.csv'
    csv_exists = os.path.isfile(csv_file)
    temp_dir = 'temp'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            song_name = row['Song Title'].strip()
            if not song_name:
                continue
            print(f"\nSearching and uploading: {song_name}")
            songs = search_songs(song_name, limit=1)
            if not (songs and songs.get('data') and songs['data'].get('results')):
                print(f"No results found for '{song_name}'. Skipping.")
                continue
            song = songs['data']['results'][0]
            song_id = song.get('id')
            if not song_id:
                print(f"No song ID found for '{song_name}'. Skipping.")
                continue
            if is_song_uploaded(song_id):
                print(f"Song '{song_name}' already uploaded. Skipping.")
                continue
            details = get_song_by_id(song_id)
            if not (details and details.get('data') and len(details['data']) > 0):
                print(f"Could not fetch details for song '{song_name}'. Skipping.")
                continue
            data = details['data'][0]
            download_url = data.get('downloadUrl')
            # Get image url (prefer 500x500)
            img_field = data.get('image') or data.get('imageUrl')
            image_url = None
            if isinstance(img_field, list):
                best_img = None
                for img in img_field:
                    if isinstance(img, dict) and img.get('quality') == '500x500':
                        best_img = img.get('url')
                        break
                if not best_img and img_field:
                    best_img = img_field[-1].get('url') if isinstance(img_field[-1], dict) else None
                image_url = best_img
            elif isinstance(img_field, str):
                image_url = img_field

            # Process both 160kbps and 320kbps qualities
            for quality in ['160kbps', '320kbps']:
                quality_url = None
                if isinstance(download_url, dict):
                    quality_url = download_url.get(quality)
                elif isinstance(download_url, list):
                    for item in download_url:
                        if isinstance(item, dict) and (item.get('quality') == quality):
                            quality_url = item.get('url')
                            break
                elif isinstance(download_url, str):
                    quality_url = None
                if not quality_url:
                    print(f"No {quality} download URL found for the song '{song_name}'. Skipping {quality}.")
                    continue
                # Send image and get file_id/unique_id (only once, for first quality)
                image_file_id = image_file_unique_id = None
                if image_url and quality == '160kbps':
                    async def send_image():
                        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
                        temp_image_filename = os.path.join(temp_dir, f"{song_name}_cover.jpg")
                        try:
                            img_resp = requests.get(image_url, stream=True)
                            if img_resp.status_code == 200:
                                with open(temp_image_filename, 'wb') as img_file:
                                    for chunk in img_resp.iter_content(chunk_size=8192):
                                        if chunk:
                                            img_file.write(chunk)
                                with open(temp_image_filename, 'rb') as img_file:
                                    msg = await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=img_file, caption=f"{song_name} cover art")
                                    if msg and msg.photo:
                                        photo_info = msg.photo[-1]
                                        return photo_info.file_id, photo_info.file_unique_id
                        except Exception as e:
                            print(f"Failed to send image for '{song_name}': {e}")
                        finally:
                            if os.path.exists(temp_image_filename):
                                os.remove(temp_image_filename)
                        return None, None
                    try:
                        image_file_id, image_file_unique_id = asyncio.run(send_image())
                    except Exception as e:
                        print(f"Image send error: {e}")
                # Send audio for this quality
                def send_audio_from_temp():
                    temp_audio_filename = os.path.join(temp_dir, f"{song_name}_{quality}.mp3")
                    try:
                        file_response = requests.get(quality_url, stream=True)
                        with open(temp_audio_filename, 'wb') as f_audio:
                            for chunk in file_response.iter_content(chunk_size=8192):
                                if chunk:
                                    f_audio.write(chunk)
                        # Send the file to Telegram
                        async def send_audio():
                            bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
                            with open(temp_audio_filename, 'rb') as audio_file:
                                msg = await bot.send_audio(chat_id=TELEGRAM_CHAT_ID, audio=audio_file, title=song_name)
                                if msg and msg.audio:
                                    audio_file_id = msg.audio.file_id
                                    audio_file_unique_id = msg.audio.file_unique_id
                                    print(f"Audio '{song_name}' ({quality}) sent to Telegram chat.")
                                    return audio_file_id, audio_file_unique_id
                                return None, None
                        audio_file_id, audio_file_unique_id = asyncio.run(send_audio())
                    except Exception as e:
                        print(f"Failed to send audio for '{song_name}' ({quality}): {e}")
                        audio_file_id = audio_file_unique_id = None
                    finally:
                        if os.path.exists(temp_audio_filename):
                            os.remove(temp_audio_filename)
                    return audio_file_id, audio_file_unique_id
                # Retry upload up to 3 times if it fails
                max_retries = 3
                for attempt in range(1, max_retries + 1):
                    audio_file_id, audio_file_unique_id = send_audio_from_temp()
                    if audio_file_id:
                        break
                    else:
                        print(f"Upload to Telegram failed for '{song_name}' ({quality}), attempt {attempt}/{max_retries}.")
                # Only write to CSV and verify if upload was successful after retries
                if audio_file_id:
                    row_data = {
                        'song_id': song_id,
                        'song_name': song_name,
                        'quality': quality,
                        'audio_file_id': audio_file_id,
                        'audio_file_unique_id': audio_file_unique_id,
                        'image_file_id': image_file_id if quality == '160kbps' else '',
                        'image_file_unique_id': image_file_unique_id if quality == '160kbps' else '',
                        'album': data.get('album', ''),
                        'artist': data.get('primaryArtists', ''),
                        'release_date': data.get('releaseDate', ''),
                        'duration': int(data.get('duration')) if data.get('duration') else None,
                        'download_url': quality_url,
                        'image_url': image_url if quality == '160kbps' else ''
                    }
                    with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        if not csv_exists:
                            writer.writeheader()
                            csv_exists = True
                        safe_row_data = {k: ('' if row_data[k] is None else str(row_data[k])) for k in fieldnames}
                        writer.writerow(safe_row_data)

                    # Verification: read back the last row using csv.DictReader (file is now closed)
                    verified = False
                    try:
                        with open(csv_file, 'r', encoding='utf-8', newline='') as verifyfile:
                            reader = list(csv.DictReader(verifyfile))
                            if reader:
                                last_row = reader[-1]
                                expected_row = {k: ('' if row_data[k] is None else str(row_data[k])) for k in fieldnames}
                                last_row_clean = {k: ('' if last_row[k] is None else str(last_row[k])) for k in fieldnames}
                                if last_row_clean == expected_row:
                                    verified = True
                    except Exception as e:
                        print(f"Verification error for '{song_name}' ({quality}): {e}")
                    if verified:
                        print(f"Upload and verification complete for '{song_name}' ({quality})!")
                    else:
                        print(f"Verification failed for '{song_name}' ({quality})! Removing last CSV row.")
                        # Remove the last row from the CSV file
                        try:
                            with open(csv_file, 'r', encoding='utf-8', newline='') as f:
                                rows = list(csv.reader(f))
                            if len(rows) > 1:
                                rows = rows[:-1]  # Remove last row
                                with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                                    writer = csv.writer(f)
                                    writer.writerows(rows)
                        except Exception as e:
                            print(f"Error removing last row from CSV: {e}")
                        break
                else:
                    print(f"Upload to Telegram failed for '{song_name}' ({quality}) after {max_retries} attempts. Skipping CSV write and verification.")
    print("All songs from CSV processed.")

if __name__ == "__main__":
    print("JioSaavn API Python Example")
    send_test_message()
    upload_songs_from_csv('search.csv')
