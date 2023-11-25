# DiscordMusicBot
It's a Discord Music Bot


# Pre-requisites
You first must download the following:
- [git](https://git-scm.com/download/win)
- [python](https://www.python.org/downloads/windows/)
- [miniconda](https://docs.conda.io/projects/miniconda/en/latest/)
- [ffmpeg](https://www.gyan.dev/ffmpeg/builds/)

# First Time Setup
Create a virtual environment in which we can install all the necessary packages:
```
> conda create -n discordmusicbot
```

Initialize the environment:
```
> conda init
```

Close and reopen the command line terminal, then activate the environment:
```
> conda activate discordmusicbot
```

Install the necessary packages:
```
> pip install -r requirements.txt
```

# Using the bot
Invite the bot to a server using:
https://discord.com/api/oauth2/authorize?client_id=1177970716675670045&permissions=36011190242880&scope=bot

If the environment is not already activated:
```
> conda activate discordmusicbot
```

Then run the bot:
```
> python bot.py
```