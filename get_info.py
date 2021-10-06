async def queue_add(ctx, song):
    queue_name = "m"+str(ctx.guild.id)
    SQL = f"INSERT INTO {queue_name} VALUES ('{song}');"
    cur.execute(SQL)
    conn.commit()
    return

async def playlist(ctx, song):
    voice = ctx.guild.voice_client

    if voice:
        if voice.is_playing():
            await queue_add(ctx, song)
            return
        else:
            await queue_add(ctx, song)
            await play_music(ctx, song)
            return
    else:
        await ctx.author.voice.channel.connect()
        await queue_add(ctx, song)
        await play_music(ctx, song)
        return

async def get_info(ctx, song):

    if song.startswith("https://open.spotify.com/playlist"): #this is for spotify playlists
        track_names = [spottrack for spottrack in sp.user_playlist_tracks('spotify', song.split('playlist/')[1].split('?')[0])['items']]

        for track in track_names:
            song_name = track['track']['name'] + track['track']['artists'][0]['name']
        
            ytresults = YoutubeSearch(song_name, max_results=1).to_dict()

            if len(ytresults) == 0:
                await ctx.send(f"No results for {track['track']['name']} by {track['track']['artists'][0]['name']}.")
                continue
            else:
                song = "".join(("https://www.youtube.com", ytresults[0]["url_suffix"]))
                title = ytresults[0]["title"]
                channel = ytresults[0]["channel"]
                runtime = ytresults[0]["duration"]
                author = ctx.author
                live = False

            runtime_sec = col_to_sec(runtime)

            if runtime_sec > 7200:
                await ctx.send("Cannot queue a song longer than 2 hours.")
                continue

            await playlist(ctx, (song, title, channel, runtime, author, live))
        
        await ctx.send(f"Queued `{len(track_names)}` songs.")

    elif song.startswith("https://open.spotify.com/album/"): #this is for spotify albums
        tracks = [spottrack for spottrack in sp.album_tracks(song.split('album/')[1].split('?')[0])['items']]

        for item in tracks:
            song_name = item['name'] + item['artists'][0]['name']
        
            ytresults = YoutubeSearch(song_name, max_results=1).to_dict()

            if len(ytresults) == 0:
                await ctx.send(f"No results for {item['name']} by {item['artists'][0]['name']}.")
                continue
            else:
                song = "".join(("https://www.youtube.com", ytresults[0]["url_suffix"]))
                title = ytresults[0]["title"]
                channel = ytresults[0]["channel"]
                runtime = ytresults[0]["duration"]
                author = ctx.author
                live = False

            runtime_sec = col_to_sec(runtime)

            if runtime_sec > 7200:
                await ctx.send("Cannot queue a song longer than 2 hours.")
                continue

            await playlist(ctx, (song, title, channel, runtime, author, live))
        
        await ctx.send(f"Queued `{len(tracks)}` songs.")

    elif song.startswith("https://open.spotify.com/track/"): #this is for standalone spotify tracks
        track_name = sp.track(song.split("track/")[1].split("?")[0])['name']+" "+sp.track(song.split("track/")[1].split("?")[0])['artists'][0]['name']
        song = track_name
        
    elif song.startswith("https://soundcloud.com"): #this is for anything souncloud
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url = song)
            if bool(info.get('_type')): #this is for soundcloud playlists
                for entry in info['entries']:
                    title = entry['title']
                    channel = entry['uploader']
                    runtime = str(datetime.timedelta(seconds=int(entry['duration'])))
                    author = ctx.author
                    live = False if int(entry['duration']) == 0 else True
                    if int(entry['duration']) > 7200:
                        await ctx.send("Cannot queue a song longer than 2 hours.")
                        return
                    await playlist(ctx, (song, title, channel, runtime, author, live))
                await ctx.send(f"Queued `{len(info['entries'])}` songs.")
            else: #this is for soundcloud tracks
                title = info['title']
                channel = info['uploader']
                runtime = str(datetime.timedelta(seconds=int(info['duration'])))
                author = ctx.author
                live = False
                if int(info['duration']) > 7200:
                    await ctx.send("Cannot queue a song longer than 2 hours.")
                    return
                else:
                    return (title, channel, runtime, author, live)
                
    elif song.startswith("https://www.youtube.com"): #this is for direct youtube links
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url = song)
            if bool(info.get('_type')): #this is for youtube playlists or albums
                for entry in info['entries']:
                    song = entry['webpage_url']
                    title = entry['title']
                    channel = entry['uploader']
                    runtime = str(datetime.timedelta(seconds=int(entry['duration'])))
                    author = ctx.author
                    live = True if int(entry['duration']) == 0 else False

                    if int(entry['duration']) > 7200:
                        await ctx.send("Cannot queue a song longer than 2 hours.")
                        continue
                    
                    await playlist(ctx, (song, title, channel, runtime, author, live))
            else: #this is for plain youtube links
                print("playing youtube link...")
                title = info['title']
                channel = info['uploader']
                runtime = str(datetime.timedelta(seconds=int(info['duration'])))
                author = ctx.author
                live = True if int(info['duration']) == 0 else False

                if int(info['duration']) > 7200:
                    await ctx.send("Cannot queue a song longer than 2 hours.")
                    return
                else:
                    return (title, channel, runtime, author, live)
    else:
        ytresults = YoutubeSearch(song, max_results=1).to_dict()

        if len(ytresults) == 0:
            await ctx.send("No results.")
            return False
        elif ytresults[0]['duration'] == 0:
            song = "".join(("https://www.youtube.com", ytresults[0]['url_suffix']))
            title = ytresults[0]['title']
            channel = ytresults[0]["channel"]
            runtime = 0
            live = True
        else:
            song = "".join(("https://www.youtube.com", ytresults[0]["url_suffix"]))
            title = ytresults[0]["title"]
            channel = ytresults[0]["channel"]
            runtime = ytresults[0]["duration"]
            live = False

        runtime_sec = col_to_sec(str(runtime))

        if runtime_sec > 7200:
            await ctx.send("Cannot queue a song longer than 2 hours.")
            return

    voice = ctx.guild.voice_client

    queue_name = "m"+str(ctx.guild.id)

    cur.execute(f"INSERT INTO {queue_name} VALUES ('{song}');")
    conn.commit()

    if voice:
        if voice.is_playing():
            music_queue.append((song, title, channel, runtime, ctx.author, live))
            total_runtime = 0
            for song in music_queue[1:]:
                total_runtime += col_to_sec(song[3])
            
            total_runtime += col_to_sec(str(now_playing[3]))-(int(datetime.datetime.now().timestamp())-now_playing[5])

            queueadd_embed = discord.Embed(title="**Added to Queue**", description=f"Added `{title}` to the queue.\nEstimated Time until Playing: `{str(datetime.timedelta(seconds=total_runtime))}`", color=bot_color)
            await ctx.send(embed=queueadd_embed)
            return
        else:
            await play_music(ctx, (song,title,channel, runtime, ctx.author, live))
    else:
        await uservoice.channel.connect()
        await play_music(ctx,(song,title,channel, runtime, ctx.author, live))