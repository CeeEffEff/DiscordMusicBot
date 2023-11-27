import discord
import os
from threading import Thread
from discord.ext import commands
from discord.message import Message

from playlist_manager import PlaylistManager

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
async def help(ctx):
    await ctx.send(
        f"""Commands:
            - !join [Joins the voice chat]

            - !leave [Leaves the voice chat]

            - !list [Lists all the available music that can be played on Jondando's computer]

            - !play "<filename>" [Plays the music file on Jon's computer]

            - !stop [Stops the music]

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
async def add(ctx, filename):
    channel = ctx.author.voice.channel
    guild = ctx.guild
    filepath = os.path.abspath(os.path.join(music_dir, filename))
    if not os.path.isfile(filepath):
        await ctx.send(f"❌ {filepath} does not exist Josh... Try again you doofus 🙂")
        return
    source = discord.FFmpegPCMAudio(os.path.join('music', filepath))
    
    PlaylistManager.add_to_playlist(filename, source, str(guild), str(channel))
    await ctx.send(f"Adding {filename} to playlist...")

@bot.command()
async def skip(ctx):
    voice_channel = get_author_voice(ctx)
    if voice_channel and voice_channel.is_playing():
        voice_channel.stop()
        await ctx.send("Skipping the current song.")
    else:
        await send_no_music_playing(ctx)

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
    await ctx.send("No music is playing dude, what on *earth* have you been smoking? 😶‍🌫️")

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
    voice_channel = get_author_voice(ctx)
    if voice_channel:
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
    bot.run('<INSERT TOKEN HERE>')
