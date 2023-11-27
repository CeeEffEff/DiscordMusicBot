from threading import Lock
from queue import Empty, Queue
from threading import Thread, Event
from time import sleep
from typing import Tuple

import discord

class PlaylistManager:
    playlists = dict()
    playlists_lock = Lock()
    threads = dict()
    threads_lock = Lock()

    @classmethod
    def __get_playlist(cls, server, channel) -> Tuple[str, Queue]:
        with cls.playlists_lock:
            key = (server, channel)
            value = cls.playlists.get(key)
            if value:
                return value
            playlist = Queue()
            curr_playing = ''
            cls.playlists[key] = (curr_playing, playlist)
            return curr_playing, playlist

    @classmethod
    def __set_playlist_current(cls, curr_playing, server, channel) -> Tuple[str, Queue]:
        with cls.playlists_lock:
            key = (server, channel)
            value = cls.playlists.get(key)
            if value:
                cls.playlists[key] = curr_playing, value[1]
                return
            playlist = Queue()
            curr_playing = ''
            cls.playlists[key] = (curr_playing, playlist)

    @classmethod
    def add_to_playlist(cls, name: str, source: discord.FFmpegPCMAudio, server, channel) -> None:
        _, playlist = cls.__get_playlist(server, channel)
        playlist.put((name, source))

    @classmethod
    def get_next_song(cls, server, channel) -> Tuple:
        _, playlist = cls.__get_playlist(server, channel)
        while True:
            print(f'Waiting on item to be available in playlist {(server, channel)}...')
            try:
                name, source = playlist.get(block=True, timeout=2)
                cls.__set_playlist_current(name, server, channel)
                return name, source
            except Empty:
                pass

    @classmethod
    async def list_playlist(cls, ctx, server, channel) -> None:
        curr_playing, playlist = cls.__get_playlist(server, channel)
        message = f'Current/Up Next:\n\t[{curr_playing}]\n'
        message += '\nFollowed By:'
        for num, (name, _) in enumerate(playlist.queue, start=1):
            message += f'\n\t{num}. [{name}]\n'
        await ctx.send(message)

    @classmethod
    def start_playlist(cls, voice_channel, server, channel) -> None:
        with cls.threads_lock:
            key = (server, channel)
            value = cls.threads.get(key)
            if value and (thread := value[0]) and thread.is_alive():
                _, play_event = value
                print(f'Setting play event for {(server, channel)}')
                play_event.set()
                return
            play_event = Event()
            play_event.set()
            thread = Thread(
                target=playlist_loop,
                args=(voice_channel, server, channel, play_event),
                name=str(key),
                daemon=True
            )
            cls.threads[key] = thread, play_event
            print(f'Starting playlist for {(server, channel)}')
            thread.start()
    
    
    @classmethod
    def stop_playlist(cls, server, channel) -> None:
        with cls.threads_lock:
            key = (server, channel)
            value = cls.threads.get(key)
            if not value:
                return
            _, play_event = value
            print(f'Clearing play event for {(server, channel)}')
            play_event.clear()

def playlist_loop(voice_channel, server, channel, play_event: Event):
    while True:
        name, source = PlaylistManager.get_next_song(server, channel)
        play_event.wait()
        voice_channel.play(
            source,
            after=lambda e: print(f'Done playing {name}', e)
        )
        voice_channel.source = discord.PCMVolumeTransformer(voice_channel.source)
        voice_channel.source.volume = 0.47

        while voice_channel.is_playing():
            sleep(5)
