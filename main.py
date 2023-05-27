import time

from ytmusicapi import YTMusic
from yandex_music import Client


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




def yandex_music():
    client = Client('token').init()
    #test = client.users_playlists(3)
    playlist_link_from = input("Link to playlist from which should be copied tracks:").split("=")[1]
    ytmusic = YTMusic("browser.json")
    tracks = ytmusic.get_playlist(playlist_link_from, 1000)['tracks']
    titles = [t['title'] for t in tracks]

    created_playlist = client.users_playlists_create(title="Copied from YTM")

    for track_name in titles:
        # Поиск трека
        search_result = client.search(track_name, type_='track')
        # Получение информации о плейлисте
        if search_result.tracks is not None:
            playlist = client.users_playlists(kind=created_playlist.kind)
            # Берем лучший результат
            best_track = search_result.tracks.results[0]
            # Добавляем трек в плейлист
            client.users_playlists_insert_track(playlist.kind, best_track.id, best_track.albums[0]['id'], revision=playlist.revision)


what_to_do = input("You chose:")
if (what_to_do == '1'):
    copy_youtube_music_track_from_to_youtube_music_playlist()
elif (what_to_do == '2'):
    yandex_music()

