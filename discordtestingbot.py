import ctypes
import asyncio
import ctypes.util
import datetime
import math
import os
import random
import functools
import itertools
from async_timeout import timeout

import discord
from discord import colour
from discord import permissions
from discord.errors import ClientException
from discord.ext import commands
from discord.ext.commands.errors import CommandOnCooldown
from discord.player import FFmpegPCMAudio

import spotipy
import spotipy.oauth2 as oauth2
import psycopg2
import requests
import youtube_dl
from youtube_search import YoutubeSearch

DEFAULT_PREFIX = "!"

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()
conn.autocommit = True

async def get_prefix(bot, message):
    cur.execute(f"SELECT prefix FROM prefixes WHERE server_id={message.guild.id};")
    return cur.fetchone()[0]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix = get_prefix, description = "General purpose music bot", intents=intents, case_insensitive = True)
bot.remove_command('help')
bot_color = discord.Color.from_rgb(81,193,177)

find = ctypes.util.find_library('opus')
discord.opus.load_opus(find)

auth_manager = oauth2.SpotifyClientCredentials(client_id=os.environ['spot_id'], client_secret=os.environ['spot_secret'])
sp = spotipy.Spotify(auth_manager=auth_manager)

music_queue = []

ydl_opts = {
    'quiet': True,
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': './song.mp3',
    'cookiefile': '.ydl_cookies.txt'
}

now_playing = ""

song_repeating = False
queue_repeating = False

@bot.group(name='help', invoke_without_command = True)
async def help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    cur.execute(f"SELECT prefix FROM prefixes WHERE server_id={ctx.guild.id};")
    cur_prefix = cur.fetchone()[0]
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = f"The prefix of the bot is `{cur_prefix}`", color = bot_color)
    helpEmbed.add_field(name = ":musical_note: **Music - 8**", value = "`play`, `skip`, `clear`, `queue`, `leave`, `shuffle`, `repeat`, `ignore`")
    helpEmbed.add_field(name = ":gear: **Settings**", value = "`settings`", inline = False)
    helpEmbed.set_footer(text = "For more information try .help (command) or .help (category), ex: .help play or .help settings")
    await ctx.send(embed=helpEmbed)

# MUSIC HELP COMMANDS

@help.command(name = "music")
async def music_help(ctx):
    cur.execute(f"SELECT prefix FROM prefixes WHERE server_id={ctx.guild.id};")
    cur_prefix = cur.fetchone()[0]
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the Music category", color = bot_color)
    helpEmbed.add_field(name = ":musical_note: Music Commands :musical_note:", value = "**play**\nPlays a song\n**skip**\nSkips the song\n**clear**\nClears the queue\n**queue**\nShows the queue\n**leave**\nForces the bot to leave\n**shuffle**\nShuffles the queue\n**repeat**\nRepeats the song\n**ignore**\nIgnores a user's commands", inline=False)
    helpEmbed.set_footer(text=f"For more help, type {cur_prefix}help `command` (ex. {cur_prefix}help play)")
    await ctx.send(embeds=helpEmbed)
@help.command(name = "play")
async def play_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the play command", color = bot_color)
    helpEmbed.add_field(name = "play `<youtube url, search term, or spotify playlist link>`", value = "play lets you queue a song from youtube or a playlist from spotify")
    await ctx.send(embed=helpEmbed)
@help.command(name = "skip")
async def skip_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the skip command", color = bot_color)
    helpEmbed.add_field(name = "skip", value = "skip lets you skip the currently playing song")
    await ctx.send(embed=helpEmbed)
@help.command(name = "clear")
async def clear_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the clear command", color = bot_color)
    helpEmbed.add_field(name = "clear", value = "clear lets you clear the song queue")
    await ctx.send(embed=helpEmbed)
@help.command(name = "leave")
async def leave_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the leave command", color = bot_color)
    helpEmbed.add_field(name = "leave", value = "leave forces the bot to leave the voice channel")
    await ctx.send(embed=helpEmbed)
@help.command(name = "shuffle")
async def shuffle_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the shuffle command", color = bot_color)
    helpEmbed.add_field(name = "shuffle", value = "shuffle lets you shuffle the music queue")
    await ctx.send(embed=helpEmbed)
@help.command(name = "repeat")
async def repeat_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the repeat command", color = bot_color)
    helpEmbed.add_field(name = "repeat", value = "repeat lets you repeat a song indefinitely")
    await ctx.send(embed=helpEmbed)
@help.command(name = "ignore")
async def ignore_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the ignore command", color = bot_color)
    helpEmbed.add_field(name = "ignore `<mention member>`", value = "ignore lets a moderator take away someone's music bot privileges")
    await ctx.send(embed=helpEmbed)
@help.command(name = "queue")
async def queue_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the queue command", color = bot_color)
    helpEmbed.add_field(name = "queue", value = "queue lets you view the song queue")
    await ctx.send(embed=helpEmbed)
@help.command(name = "settings")
async def settings_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the settings command", color = bot_color)
    helpEmbed.add_field(name = "settings", value = "settings shows the channel and mod settings for the bot")
    await ctx.send(embed=helpEmbed)




@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    await bot.change_presence(status = discord.Status.online, activity=discord.Game("!help"))


class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))

        return ', '.join(duration)


class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title='Now playing',
                               description='```css\n{0.source.title}\n```'.format(self),
                               color=discord.Color.blurple())
                 .add_field(name='Duration', value=self.source.duration)
                 .add_field(name='Requested by', value=self.requester.mention)
                 .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                 .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
                 .set_thumbnail(url=self.source.thumbnail))

        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()

            if not self.loop:
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with timeout(180):  # 3 minutes
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    return

            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(embed=self.current.create_embed())

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('This command can\'t be used in DM channels.')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('An error occurred: {}'.format(str(error)))

    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel."""

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='summon')
    @commands.has_permissions(manage_guild=True)
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Summons the bot to a voice channel.
        If no channel was specified, it joins your channel.
        """

        if not channel and not ctx.author.voice:
            raise VoiceError('You are neither connected to a voice channel nor specified a channel to join.')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='leave', aliases=['disconnect'])
    @commands.has_permissions(manage_guild=True)
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""

        if not ctx.voice_state.voice:
            return await ctx.send('Not connected to any voice channel.')

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name='volume')
    async def _volume(self, ctx: commands.Context, *, volume: int):
        """Sets the volume of the player."""

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        if 0 > volume > 100:
            return await ctx.send('Volume must be between 0 and 100')

        ctx.voice_state.volume = volume / 100
        await ctx.send('Volume of the player set to {}%'.format(volume))

    @commands.command(name='now', aliases=['current', 'playing'])
    async def _now(self, ctx: commands.Context):
        """Displays the currently playing song."""

        await ctx.send(embed=ctx.voice_state.current.create_embed())

    @commands.command(name='pause')
    @commands.has_permissions(manage_guild=True)
    async def _pause(self, ctx: commands.Context):
        """Pauses the currently playing song."""

        if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='resume')
    @commands.has_permissions(manage_guild=True)
    async def _resume(self, ctx: commands.Context):
        """Resumes a currently paused song."""

        if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='stop')
    @commands.has_permissions(manage_guild=True)
    async def _stop(self, ctx: commands.Context):
        """Stops playing song and clears the queue."""

        ctx.voice_state.songs.clear()

        if not ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction('⏹')

    @commands.command(name='skip')
    async def _skip(self, ctx: commands.Context):
        """Vote to skip a song. The requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing any music right now...')

        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester:
            await ctx.message.add_reaction('⏭')
            ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= 3:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()
            else:
                await ctx.send('Skip vote added, currently at **{}/3**'.format(total_votes))

        else:
            await ctx.send('You have already voted to skip this song.')

    @commands.command(name='queue')
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """Shows the player's queue.
        You can optionally specify the page to show. Each page contains 10 elements.
        """

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                 .set_footer(text='Viewing page {}/{}'.format(page, pages)))
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction('✅')

    @commands.command(name='remove')
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a song from the queue at a given index."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction('✅')

    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing song.
        Invoke this command again to unloop the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction('✅')

    @commands.command(name='play')
    async def _play(self, ctx: commands.Context, *, search: str):
        """Plays a song.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """

        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                song = Song(source)

                await ctx.voice_state.songs.put(song)
                await ctx.send('Enqueued {}'.format(str(source)))

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Bot is already in a voice channel.')

@bot.group(name="settings", description="Allows an admin to change the settings of the bot", invoke_without_command=True)
async def settings(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that command.")
        await asyncio.sleep(5)
        return
    elif len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    else:
        settings_embed = discord.Embed(title = "Settings", description = "", color=bot_color)
        settings_embed.add_field(name="Channels", value = f"This setting allows you to add or remove channels that the bot will listen to \n `channels` - lets you view the currently whitelisted channels \n `addchannel` - adds a channel to the bots whitelist \n `removechannel` - removes a channel from the bots whitelist", inline=False)
        settings_embed.add_field(name="Mods", value = f"This setting allows you to add or remove mods that can change bot settings \n `mods` - lets you view the current list of mods \n `addmod` - lets you add a mod \n `removemod` - lets you remove a mod")
        settings_embed.add_field(name="Prefix", value = f"This setting allows you to change the prefix the bot uses for commands \n `prefix` - lets you change the bot's prefix", inline=False)
        settings_embed.set_footer(text = "ex. `!settings addchannel #general`, `!settings prefix ?`, etc...")
        await ctx.send(embed=settings_embed)

@settings.command(name="channels", description="Lets you view the currently whitelisted channels", aliases=["c"])
async def channels(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that command.")
        await asyncio.sleep(5)
        return
    elif len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    elif len(channelWhitelist) == 0:
        await ctx.send(":x: No channels are whitelisted. Commands can be accepted from any channel.")
        return
    else:
        channelEmbed = discord.Embed(title="Channel Whitelist", description = "", color=bot_color)
        for channelID in channelWhitelist:
            channel = bot.get_channel(channelID)
            channelEmbed.add_field(name=channel.name, value=":white_circle: This channel is whitelisted", inline=False)

        await ctx.send(embed=channelEmbed)
        return
        
@settings.command(name="addchannel", description="Lets you add a channel to the whitelist", aliases=["ac"])
async def add_channel(ctx, channel: discord.TextChannel):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that command.")
        await asyncio.sleep(5)
        return
    elif len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    elif channel not in ctx.guild.text_channels:
        await ctx.send(":x: That is not a valid text channel.")
        return
    elif channel.id in channelWhitelist:
        await ctx.send(":x: That channel is already in the bot's whitelist.")
        return
    else:
        SQL = f"INSERT INTO {server_name}(channels) VALUES ({int(channel.id)});"
        cur.execute(SQL)
        conn.commit()
        await ctx.send(f"`{channel.name}` has been added to the bot's whitelist.")
        return

@settings.command(name="removechannel", description="Lets you remove a channel from the whitelist", aliases=["rc"])
async def remove_channel(ctx, channel: discord.TextChannel):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that command.")
        await asyncio.sleep(5)
        return
    elif len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    elif channel not in ctx.guild.text_channels:
        await ctx.send(":x: That is not a valid text channel.")
        return
    elif (channel.id,) not in channelWhitelist:
        await ctx.send(":x: That channel is not currently on the bot's whitelist.")
        return
    else:
        SQL = f"UPDATE {server_name} SET channel = NULL WHERE channel = {int(channel.id)};"
        cur.execute(SQL)
        conn.commit()
        await ctx.send(f"`{channel.name}` has been removed from the bot's whitelist.")
        return

@settings.command(name="mods", description = "Lets you view the current mods", aliases=["m"])
async def mods(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [int(id[0]) for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [int(channel[0]) for channel in cur.fetchall() if type(channel[0]) is str]

    if int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that command.")
        await asyncio.sleep(5)
        return
    elif len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    elif len(modIDS) == 0:
        await ctx.send("There are no moderators in this server")
        return
    else:
        mod_embed = discord.Embed(title="Mod List", description = "List of added mods that have control over the bot", color=bot_color)
        for modID in modIDS:
            mod = bot.get_user(modID)
            mod_embed.add_field(name=mod.display_name, value = f":crossed_swords: This user is a moderator", inline=False)
        await ctx.send(embed=mod_embed)
        return

@settings.command(name="addmod", description="Lets you add a moderator to the bot", aliases=["am"])
async def add_mod(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is str]

    if int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that command.")
        await asyncio.sleep(5)
        return
    elif len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return

    for i in range(len(ctx.message.mentions)):
        modUser = ctx.message.mentions[i-1]
        if modUser.id in modIDS:
            await ctx.send(":x: This user is already a moderator.")
            return
        elif modUser.bot:
            await ctx.send(":x: You cannot add other bots as moderators.")
            return
        else:
            SQL = f"INSERT INTO {server_name}(mods) VALUES ({modUser.id});"
            cur.execute(SQL)
            conn.commit()
            await ctx.send(f"{modUser.name} has been added to the bot's mod list.")
            return

@settings.command(name="removemod", description="Lets you remove a moderator from the bot", aliases=["rm"])
async def remove_mod(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is str]

    if int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that command.")
        await asyncio.sleep(5)
        return
    elif len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return

    for i in range(len(ctx.message.mentions)):
        modUser = ctx.message.mentions[i-1]
        if modUser.id not in modIDS:
            await ctx.send(":x: This user is not a moderator.")
            return
        else:
            SQL = f"UPDATE {server_name} SET mods = NULL WHERE mods = {int(modUser.id)};"
            cur.execute(SQL)
            conn.commit()
            await ctx.send(f"{modUser.name} has been removed from the bot's mod list.")
            return

@settings.command(name="prefix", description="Lets you change the prefix the bot uses in commands")
async def change_prefix(ctx, prefix):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is str]

    if int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that command.")
        await asyncio.sleep(5)
        return
    elif len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return

    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is str]

    cur.execute(f"SELECT prefix FROM prefixes WHERE server_id={ctx.guild.id};")
    current_prefix = str(cur.fetchone()[0])

    if int(ctx.author.id) not in modIDS:
        await ctx.send(":x: You must have a moderator role to use that command.")
        return
    elif len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        return
        await mess.delete()
    elif not isinstance(prefix, str):
        await ctx.send(":x: The prefix must be a string (like a letter or punctuation).")
        return
    elif prefix == current_prefix:
        await ctx.send(":x: That is the current prefix.")
        return
    else:
        SQL = f"UPDATE prefixes SET prefix = '{str(prefix)}' WHERE server_id={ctx.guild.id};"
        cur.execute(SQL)
        conn.commit()
        await ctx.send(f"Prefix successfully changed to `{prefix}`.")
        return

@bot.event
async def on_member_join(member):
    #insert into musicbot
    SQL = f"INSERT INTO musicbot(ignore, id) VALUES (False, {member.id});"
    cur.execute(SQL)
    conn.commit()


@bot.event
async def on_member_leave(member):
    #delete from music bot
    SQL = f"DELETE FROM musicbot WHERE id={member.id};"
    cur.execute(SQL)
    conn.commit()

@bot.event
async def on_guild_join(guild):
    main_channel = guild.text_channels[0]
    await main_channel.send(f":cd: Thanks for welcoming me to `{guild.name}`! My default prefix is `!`. You can change this and the channel I listen to with `!settings`.")

    server_name = "t"+str(guild.id)
    queue_name = "m"+str(guild.id)

    SQL = f"CREATE TABLE {server_name} (channels bigint, mods bigint, prefix varchar(255));"
    cur.execute(SQL)
    conn.commit()

    SQL = f"CREATE TABLE {queue_name} (song varchar(255), title varchar(255), channel varchar(255), runtime varchar(255), author varchar(255), live bool);"
    cur.execute(SQL)
    conn.commit()

    SQL = f"INSERT INTO prefixes(server_id,prefix) VALUES ({guild.id}, '{DEFAULT_PREFIX}');"
    cur.execute(SQL)
    conn.commit()

    SQL = f"INSERT INTO {server_name}(mods) VALUES (288710564367171595);"
    cur.execute(SQL)
    conn.commit()

    for member in guild.members:
        if member.bot:
            continue
        SQL = f"INSERT INTO musicbot(ignore, id) VALUES (False, {int(member.id)});"
        cur.execute(SQL)
        conn.commit()

        if member.top_role.permissions.administrator:
            SQL = f"INSERT INTO {server_name}(mods) VALUES ({int(member.id)});"
            cur.execute(SQL)
            conn.commit()

@bot.event
async def on_guild_remove(guild):
    server_name = "t"+str(guild.id)
    queue_name = "m"+str(guild.id)

    for member in guild.members:
        SQL = f"DELETE FROM musicbot WHERE id={member.id};"
        cur.execute(SQL)
        conn.commit()
    
    SQL = f"DELETE FROM prefixes WHERE server_id={guild.id};"
    cur.execute(SQL)
    conn.commit()
    
    SQL = f"DROP TABLE {server_name};"
    cur.execute(SQL)
    conn.commit()

    SQL = f"DROP TABLE {queue_name};"
    cur.execute(SQL)
    conn.commit()
    


bot.add_cog(Music(bot))
#--------------------------------------------------------------------------------------------------------------------------------------#
#runs the bot using the discord bot token provided within Heroku
bot.run(os.environ['token'])

