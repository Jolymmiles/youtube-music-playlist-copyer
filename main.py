import asyncio
import json
import time
from time import sleep

from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.command import Command
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from yandex_music import ClientAsync
from ytmusicapi import YTMusic
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By



def is_active(driver):
    try:
        driver.execute(Command.GET_ALL_COOKIES)
        return True
    except Exception:
        return False


def get_token():
    # make chrome log requests
    capabilities = DesiredCapabilities.CHROME
    capabilities["loggingPrefs"] = {"performance": "ALL"}
    capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}
    # Create a Service object using ChromeDriverManager
    service = Service(ChromeDriverManager().install())

    with webdriver.Chrome(service=service, desired_capabilities=capabilities) as driver:
        driver.get("https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d")

        token = None
        while token is None and is_active(driver):
            try:
                logs_raw = driver.get_log("performance")
            except Exception:
                continue

            for lr in logs_raw:
                log = json.loads(lr["message"])["message"]
                url_fragment = log.get('params', {}).get('frame', {}).get('urlFragment')

                if url_fragment:
                    token = url_fragment.split('&')[0].split('=')[1]
                    break

    return token


def get_playlist(ytmusic, name):
    playlists = ytmusic.get_library_playlists()
    for playlist in playlists:
        if playlist['title'] == name:
            return playlist['playlistId']
    return None


def add_track_to_playlist(ytmusic, new_playlist, track, progress):
    try:
        existing_tracks = ytmusic.get_playlist(new_playlist)['tracks']
        if not any(t['videoId'] == track['videoId'] for t in existing_tracks):
            ytmusic.add_playlist_items(new_playlist, [track['videoId']])
            progress['count'] += 1
            print(f"\rProgress: {progress['count'] / progress['total'] * 100:.2f}%", end="")
    except Exception as e:
        print(f"\nError adding track {track['title']} to playlist: {e}")
        raise


def copy_youtube_music_track_from_to_youtube_music_playlist():
    new_playlist_name = input("New playlist name:")
    track_quantity = int(input("Quantity of tracks in playlist:"))
    playlist_link_from = input("Link to playlist from which should be copied tracks:").split("=")[1]

    ytmusic = YTMusic("browser.json")
    tracks = ytmusic.get_playlist(playlist_link_from, track_quantity)['tracks']
    new_playlist = get_playlist(ytmusic, new_playlist_name)

    if not new_playlist:
        new_playlist = ytmusic.create_playlist(new_playlist_name, "Public playlist created from Likes", "PUBLIC")

    existing_tracks = ytmusic.get_playlist(new_playlist, track_quantity)['tracks']
    tracks = [t for t in tracks if not any(et['videoId'] == t['videoId'] for et in existing_tracks)]
    progress = {'count': 0, 'total': len(tracks)}

    i = 0
    while i < len(tracks):
        try:
            add_track_to_playlist(ytmusic, new_playlist, tracks[i], progress)
            i += 1
        except Exception:
            time.sleep(5)

    print("\nDone!")


async def add_track(client, playlist_kind, track_name, progress):
    search_results = await client.search(track_name, type_='track')
    if search_results.tracks is not None:
        playlist = await client.users_playlists(kind=playlist_kind)
        best_track = search_results.tracks.results[0]
        if best_track.available & best_track.albums[0]['id'] is not None:
            await client.users_playlists_insert_track(playlist.kind, best_track.id, best_track.albums[0]['id'],
                                                      revision=playlist.revision)
        progress['count'] += 1
        print(f"\rProgress: {progress['count'] / progress['total'] * 100:.2f}%", end="")


async def yandex_music(titles: []):
    token = get_token()
    print(f"Got Yandex token {token}")
    client = await ClientAsync(token).init()
    print("Connected to Yandex")
    created_playlist = await client.users_playlists_create(title="Copied from YTM2")
    print("Created new playlist")
    progress = {'count': 0, 'total': len(titles)}
    print(f"Quantity of tracks from youtube {len(titles)}")
    for track_name in titles:
        await add_track(client, created_playlist.kind, track_name, progress)


def get_track_names_from_youtube_music_playlist():
    ytmusic = YTMusic("browser.json")
    print("Connected to YouTube Music")
    playlists = ytmusic.get_library_playlists()
    for i, playlist in enumerate(playlists):
        print(f"{i + 1}: {playlist['title']}")
    playlist_index = int(input("Enter the index of the playlist you want to select:")) - 1
    selected_playlist = playlists[playlist_index]
    tracks = ytmusic.get_playlist(selected_playlist['playlistId'], 1000)['tracks']
    titles = [tt['artists'][0]['name'] + " " + tt['title'] for tt in tracks]
    print(f"Got all track names from playlist {selected_playlist['playlistId']}")
    return titles


what_to_do = input("You chose:")
if what_to_do == '1':
    copy_youtube_music_track_from_to_youtube_music_playlist()
elif what_to_do == '2':
    loop = asyncio.get_event_loop()
    temp = get_track_names_from_youtube_music_playlist()
    loop.run_until_complete(yandex_music(temp))

