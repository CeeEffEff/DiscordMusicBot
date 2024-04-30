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
    def get_playlist(cls, server, channel) -> Tuple[str, Queue]:
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
        _, playlist = cls.get_playlist(server, channel)
        playlist.put((name, source))

    @classmethod
    def clear_playlist(cls, server, channel) -> None:
       with cls.playlists_lock:
            key = (server, channel)
            value = cls.playlists.get(key)
            if not value:
                return
            playlist = Queue()
            curr_playing = ''
            cls.playlists[key] = (curr_playing, playlist)

    @classmethod
    def get_next_song(cls, server, channel, terminate_event: Event) -> Tuple:
        _, playlist = cls.get_playlist(server, channel)
        while True:
            if terminate_event.is_set():
                return
            print(f'Waiting on item to be available in playlist {(server, channel)}...')
            try:
                name, source = playlist.get(block=True, timeout=2)
                cls.__set_playlist_current(name, server, channel)
                return name, source
            except Empty:
                pass

    @classmethod
    async def list_playlist(cls, ctx, server, channel) -> None:
        curr_playing, playlist = cls.get_playlist(server, channel)
        playlist_info = f"```yaml\nCurrent/Up Next:\n[{curr_playing}]\n\nFollowed By:\n"
        for num, (name, _) in enumerate(playlist.queue, start=1):
            playlist_info += f"{num}. {name}\n"
        playlist_info += "```"
        await ctx.send(playlist_info)

    @classmethod
    def start_playlist(cls, voice_channel, server, channel) -> None:
        with cls.threads_lock:
            key = (server, channel)
            value = cls.threads.get(key)
            if value and (thread := value[0]) and thread.is_alive():
                _, play_event, _ = value
                print(f'Setting play event for {(server, channel)}')
                play_event.set()
                return
            play_event = Event()
            play_event.set()
            terminate_event = Event()
            thread = Thread(
                target=playlist_loop,
                args=(voice_channel, server, channel, play_event, terminate_event),
                name=str(key),
                daemon=True
            )
            cls.threads[key] = thread, play_event, terminate_event
            print(f'Starting playlist for {(server, channel)}')
            thread.start()
    
    
    @classmethod
    def stop_playlist(cls, server, channel) -> None:
        with cls.threads_lock:
            key = (server, channel)
            value = cls.threads.get(key)
            if not value:
                return
            _, play_event, _ = value
            print(f'Clearing play event for {(server, channel)}')
            play_event.clear()
        cls.__set_playlist_current('', server, channel)
    
    @classmethod
    def terminate_playlist(cls, server: str, channel: str) -> None:
        with cls.threads_lock:
            key = (server, channel)
            value = cls.threads.get(key)
            if value:
                thread, play_event, stop_event = value
                stop_event.set()
                play_event.set() # Prevents blocking, but we will not actually play
                print(f'Waiting for {thread.name} to terminate...')
                thread.join()
                print(f'{thread.name} terminated.')
        cls.clear_playlist(server, channel)

def playlist_loop(voice_channel, server, channel, play_event: Event, terminate_event: Event):
    while True:
        name, source = PlaylistManager.get_next_song(server, channel, terminate_event)
        if terminate_event.is_set():
            return
        play_event.wait()
        if terminate_event.is_set():
            return
        voice_channel.play(
            source,
            after=lambda e: print(f'Done playing {name}', e)
        )
        voice_channel.source = discord.PCMVolumeTransformer(voice_channel.source)
        voice_channel.source.volume = 0.47

        while voice_channel.is_playing():
            if terminate_event.is_set():
                return
            sleep(5)
