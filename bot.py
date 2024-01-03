import discord
import os
from functools import partial
from threading import Thread
from pytube import YouTube
from discord.ext import commands
from discord.message import Message

from playlist_manager import PlaylistManager
from bot_token import TOKEN

music_dir = 'music'

# Setup music dir
if not os.path.isdir(music_dir):
    os.mkdir(music_dir)

# Define the intents
intents = discord.Intents.default()
intents.all()
intents.message_content = True

# Create the bot
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help') # We write our own help command

def get_author_voice(ctx):
    voice_channel = discord.utils.get(
            bot.voice_clients, 
            guild=ctx.guild,
            channel=ctx.author.voice.channel
        )
    return voice_channel

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message: Message):
    if message.author == bot.user:  # Ignore messages from the bot itself
        return
    print(f'Message content: {message.content}')
    if not message.content:  # Check if the message content is empty
        return

    # Process the message content here
    await bot.process_commands(message)

@bot.command()
async def square(ctx):
    await ctx.send('Josh rn: 🟨👉👈')

@bot.command()
async def help(ctx):
    await ctx.send(
        f"""Commands:
            - !join [Joins the voice chat]

            - !leave [Leaves the voice chat, stopping and clearing any playlist]

            - !list [Lists all the downloaded available music that can be played on the computer]

            - !playlist [Lists all songs in the current playlist]

            - !add "<filename>" [Add the music file on local computer to the playlist]
            
            - !add "<youtube url>" [Download and add the youtube song to the playlist]

            - !play [Sets the playlist to play mode]

            - !stop [Stops the playlist]

            - !skip [Skips the current song]

            - !clear [Clears the playlist]

            - !louder [Increases the music volume for everyone]

            - !quieter [Decreases the music volume for everyone]
        """
    )

@bot.command()
async def play(ctx):
    channel = ctx.author.voice.channel
    guild = ctx.guild
    try:
        voice_channel = await channel.connect()
    except discord.errors.ClientException as e:
        if 'Already connected to a voice channel' not in str(e):
            raise e
        voice_channel = get_author_voice(ctx)
    PlaylistManager.start_playlist(voice_channel, str(guild), str(channel))
    await ctx.send("Playlist set to play 💦")

@bot.command()
async def stop(ctx):
    channel = ctx.author.voice.channel
    guild = ctx.guild
    voice_channel = get_author_voice(ctx)
    if voice_channel:
        PlaylistManager.stop_playlist(str(guild), str(channel))

    if voice_channel and voice_channel.is_playing():
        voice_channel.stop()
        await ctx.send("Stopped the music... Pfft. Buzzkill. 😒")
    else:
        await send_no_music_playing(ctx)

@bot.command()
async def add(ctx, filename: str):
    channel = ctx.author.voice.channel
    guild = ctx.guild
    filepath = os.path.abspath(os.path.join(music_dir, filename))
    if filename.startswith('https://www.youtube.com') or filename.startswith('https://youtu.be'):
        await add_yt_song(ctx, filename, channel, guild)
        return
    if os.path.isfile(filepath):
        await add_file(ctx, filename, channel, guild, filepath)
        return
    if os.path.isdir(filepath):
        await add_dir(ctx, filename, channel, guild, filepath)
        return
    await ctx.send(f"❌ {filepath} does not exist... Try again you doofus 🙂")

async def add_yt_song(ctx, url, channel, guild):
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        if not stream:
            await ctx.send(f"Stream for {url} not available.")
            return
        await ctx.send(f"Attempting to download {url}... Will add to the playlist if successful 🤞")
        add_func = partial(add_downloaded, yt.title, channel, guild)
        yt.register_on_complete_callback(add_func)
        dl_thread = Thread(target=stream.download, args=(music_dir,))
        dl_thread.daemon = True
        dl_thread.start()
    except Exception as e:
        await ctx.send(f"Error: {e}")
    

def add_downloaded(filename, channel, guild, obj, filepath):
    source = discord.FFmpegPCMAudio(filepath)
    PlaylistManager.add_to_playlist(filename, source, str(guild), str(channel))
    print(f"Added {filename} to playlist")

async def add_file(ctx, filename, channel, guild, filepath):
    source = discord.FFmpegPCMAudio(filepath)
    PlaylistManager.add_to_playlist(filename, source, str(guild), str(channel))
    await ctx.send(f"Added {filename} to playlist 🤝🏼")

async def add_dir(ctx, dirname, channel, guild, dirpath):
    added = 0
    for filename in os.listdir(dirpath):
        filepath = os.path.abspath(os.path.join(dirpath, filename))
        if not os.path.isfile(filepath):
            continue
        try:
            source = discord.FFmpegPCMAudio(filepath)
        except Exception as e:
            print(e)
            continue
        PlaylistManager.add_to_playlist(filename, source, str(guild), str(channel))
        added += 1
    await ctx.send(f"Added {added} files from {dirname} to playlist 🤝🏼")

@bot.command()
async def skip(ctx):
    voice_channel = get_author_voice(ctx)
    if voice_channel and voice_channel.is_playing():
        voice_channel.stop()
        await ctx.send("Skipping the current song ⏭️")
    else:
        await send_no_music_playing(ctx)

@bot.command()
async def clear(ctx):
    channel = ctx.author.voice.channel
    guild = ctx.guild
    PlaylistManager.clear_playlist(str(guild), str(channel))
    await ctx.send(f"Cleared the playlist 💣")

@bot.command()
async def playlist(ctx):
    channel = ctx.author.voice.channel
    guild = ctx.guild
    await PlaylistManager.list_playlist(ctx, str(guild), str(channel))

@bot.command()
async def list(ctx):
    filepath = os.path.abspath(music_dir)
    message = f'{filepath} contains:'
    for file in os.listdir(filepath):
        message += f'\n\t- {file}\n'
    await ctx.send(message)

@bot.command()
async def louder(ctx):
    voice_channel = get_author_voice(ctx)
    if voice_channel and voice_channel.is_playing():
        voice_channel.source.volume += 0.1
        await ctx.send("LOUDER 🤬")
    else:
        await send_no_music_playing(ctx)

async def send_no_music_playing(ctx):
    await ctx.send("No music is playing dude 😶")

@bot.command()
async def quieter(ctx):
    voice_channel = get_author_voice(ctx)
    if voice_channel and voice_channel.is_playing():
        vol = max(voice_channel.source.volume - 0.1, 0.47)
        voice_channel.source.volume = vol
        await ctx.send("Shhhh 🤫")
    else:
        await send_no_music_playing(ctx)

@bot.command()
async def leave(ctx):
    channel = ctx.author.voice.channel
    guild = ctx.guild
    voice_channel = get_author_voice(ctx)
    if voice_channel:
        PlaylistManager.terminate_playlist(
            server=str(guild),
            channel=str(channel)
        )
        await voice_channel.disconnect()
        await ctx.send("👋 Left the voice channel. Gone but never gonna let you down.")
    else:
        await ctx.send("I'm not in a voice channel 😭 If you don't like me just say it.")
    
@bot.command()
async def join(ctx):
    # Check if the user is in a voice channel
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        # Join the voice channel
        voice = await channel.connect()
        await ctx.send(f'👋 Joined {channel}, and I\'m never gonna give you up 🧑🏿‍🎤')
        
        return voice
    else:
        await ctx.send("You are not in a voice channel... ❔❔❔")

if __name__ == "__main__":
    bot.run(TOKEN)
