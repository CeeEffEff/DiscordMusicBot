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
    def __get_playlist(cls, server, channel) -> Queue:
        with cls.playlists_lock:
            key = (server, channel)
            playlist = cls.playlists.get(key)
            if playlist:
                return playlist
            playlist = Queue()
            cls.playlists[key] = playlist
            return playlist

    @classmethod
    def add_to_playlist(cls, name: str, source: discord.FFmpegPCMAudio, server, channel) -> None:
        playlist = cls.__get_playlist(server, channel)
        playlist.put((name, source))

    @classmethod
    def get_next_song(cls, server, channel) -> Tuple:
        playlist = cls.__get_playlist(server, channel)
        while True:
            print(f'Waiting on item to be available in playlist {(server, channel)}...')
            try:
                return playlist.get(block=True, timeout=2)
            except Empty:
                pass

    @classmethod
    def start_playlist(cls, ctx, voice_channel, server, channel) -> None:
        with cls.threads_lock:
            key = (server, channel)
            thread, play_event = cls.threads.get(key)
            if thread:
                print(f'Setting play event for {(server, channel)}')
                play_event.set()
                return
            play_event = Event()
            play_event.set()
            thread = Thread(
                target=playlist_loop,
                args=(ctx, voice_channel, server, channel, play_event),
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
            thread, play_event = cls.threads.get(key)
            if not thread:
                return
            print(f'Clearing play event for {(server, channel)}')
            play_event.clear()

def playlist_loop(ctx, voice_channel, server, channel, play_event: Event):
    while True:
        play_event.wait()
        name, source = PlaylistManager.get_next_song(server, channel)
        ctx.send(f"(Rick) Rolling: {name}. 🎤")
        voice_channel.play(
            source,
            after=lambda e: print(f'Done playing {name}', e)
        )
        voice_channel.source = discord.PCMVolumeTransformer(voice_channel.source)
        voice_channel.source.volume = 0.07

        while voice_channel.is_playing():
            sleep(5)
            # if not play_event.is_set():
            #     print(f'Stopping playlist {(server, channel)}')
            #     voice_channel.stop()
            #     break
