import os
import discord
import asyncio
import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from discord.ext.commands.core import after_invoke
from discord.ext.commands import bot
from discord.ext import commands
from youtube_dl import YoutubeDL
from database_manager import DB_Manager
from tqdm import tqdm
# assddddsdsadsadd
class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_playing = False
        self.q = []
        self.YDL_OPTIONS = { "format": "bestaudio",
                             "postprocessors" : [{
                                    "key" : "FFmpegExtractAudio",
                                    "preferredcodec" : "mp3",
                                    "preferredquality" : "192",
                                }],
                             "noplaylists":"True" }

        self.FFMEPG_OPTIONS = { "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 10",
                                "options": "-vn" }
        

        self.voice_channel = None
        self.current_song = None
        self.tmp = False
        self.db = DB_Manager(os.environ["FIRESTORE_SECRET_JSON"])
        self.logged_users = {}
        self.ctx = None
        self.dcc = False
        self.rand = False
        self.looping = False
        self.looping_song = False
        self.playlist = 0
        self.q2 = []
        
        self.SPOTIFY_CLIENT_ID = "d6e98a42c52c4dff9cb2b09822b46423"
        self.SPOTIFY_CLIENT_SECRET = "59125220c60d4006aa9edf67d2b66d44"
        self.spotify_client = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id = self.SPOTIFY_CLIENT_ID, client_secret = self.SPOTIFY_CLIENT_SECRET))

        
    def search_youtube(self, item):

        ydl = YoutubeDL(self.YDL_OPTIONS)

        try:
            info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]

        except Exception:
            return {}
        
        return { 'source': info['formats'][0]['url'], 
                 'title': info['title'] }
        
    
    def search_youtube_multiple(self, item):
        
        ydl = YoutubeDL(self.YDL_OPTIONS)

        try:
            infos = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][:5]

        except Exception:
            return {}
        
        return [{'source': info['formats'][0]['url'], 
                 'title': info['title'] } for info in infos]
        


    def next(self,ctx):
        #asyncio.sleep(0.2)
        self.dcc = False

        if self.q:
            self.is_playing = True
            
            if self.rand:
                sel = np.random.choice(range(len(self.q)))
                url = self.q[sel][0]['source']
                self.current_song = self.q.pop(sel)
            else:
                url = self.q[0][0]['source']
                self.current_song = self.q.pop(0)
                
            asyncio.run_coroutine_threadsafe(ctx.send("REPRODUCIENDO LA SIGUIENTE CANCION QUE FLIPAS: **{}** \n".format(self.current_song[0]['title'])),self.bot.loop)
            self.voice_channel.play(discord.FFmpegPCMAudio(url, **self.FFMEPG_OPTIONS), after=lambda e: self.next(ctx))

        else:
            if self.looping:
                self.q = self.q2
                url = self.q[0][0]['source']
                self.current_song = self.q.pop(0)
                asyncio.run_coroutine_threadsafe(ctx.send("REPRODUCIENDO LA SIGUIENTE CANCION QUE FLIPAS: **{}** \n".format(self.current_song[0]['title'])),self.bot.loop)
                self.voice_channel.play(discord.FFmpegPCMAudio(url, **self.FFMEPG_OPTIONS), after=lambda e: self.next(ctx))
            else:
                self.is_playing = False
                
    

    async def play(self,ctx):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        
        self.dcc = False

        if self.q:
            self.is_playing = True
            url = self.q[0][0]['source']

            if not self.voice_channel or not self.voice_channel.is_connected():
                self.voice_channel = await self.q[0][1].connect()
                await ctx.send("LA BOMBA BATISTA YA ESTA AQUI!")
            
            self.current_song = self.q.pop(0)
            self.voice_channel.play(discord.FFmpegPCMAudio(url, **self.FFMEPG_OPTIONS), after=lambda e: self.next(ctx))
        
        else:
            self.is_playing = False
    
    @commands.command()
    async def whereami(self, ctx):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        message = f'You are in {ctx.message.guild.name} in the {ctx.message.channel.mention} channel'
        await ctx.message.author.send(message)
        
    
    @commands.command()
    async def p(self, ctx, *args):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        
        self.ctx = ctx
        multiple = False
        query = " ".join(args)
        if "--check" in query:
            multiple = True
            query = query.split("--check")[1]
        vc = ctx.author.voice.channel

        if vc is None:
            await ctx.send("LA BOMBA BATISTA YA ESTA AQUI!")

        else:
            
            if "Umbra" in ctx.message.author.name:
                message = 'Estas Baneado del bot en todos los servidores oficiales.'
                await ctx.message.author.send(message)
                return
            
            if 'spotify' in query:
                if 'playlist' not in query:
                    data = self.spotify_client.track(query)
                    query = data["name"] + " "+ data["artists"][0]['name']
                else:
                    result = self.spotify_client.playlist_items(query,limit=100)
                    data = result['items']
                    
                    while result['next']:
                        result = self.spotify_client.next(result)
                        data.extend(result['items'])
                    
                    data = [track['track']['name'] + " "+ track['track']['artists'][0]['name'] for track in data]
                    np.random.shuffle(data)
                    data = data[:30]
                    self.playlist = len(data)
                    if "Paz" in ctx.message.author.name:
                        await ctx.send("GRACIAS POR USAR NUESTRO SERVICIO PAZ USTED ES CLIENTE PREMIUM DELUXE\n CARGANDO: **"+str(len(data))+" CANCIONES"+"** A LA COLA\n")
                    else:
                        await ctx.send("HERMANO TE REGALAS HEMOS ENCONTRADO LA LISTA\n CARGANDO: **"+str(len(data))+" CANCIONES"+"** A LA COLA\n")
                    
                    for song in tqdm(data):
                        title = song.split()
                        await self.p(ctx, *title)
                        #await asyncio.sleep(0.2)
                        self.playlist -= 1
                    
                    try:
                        await ctx.send("TODAS CARGADAS\n")
                    except:
                        pass
                    
                    return


            if not multiple:
                song = self.search_youtube(query)
            else:
                song = self.search_youtube_multiple(query)
                await ctx.send("GERMAN SELECCIONA LA QUE TE MOLA\n")
                for e,s in enumerate(song):
                    await ctx.send("HERMANO TE REGALAS HEMOS ENCONTRADO LA CANCIÓN : **"+str(e)+" - "+s['title'].upper()+"** A LA LISTA\n")
                
                def check(msgg):
                    return msgg.content.isdigit()
                
                m = await self.bot.wait_for("message", check = check)
                if m:
                    print(m)
                    song = song[int(m)]
                    #

            if not song:
                await ctx.send("TE HAS EQUIVOCADO EN ALGO O LOS SERVIDORES VAN MAL NOSE YO SOY SOLO BATISTA XD\n")
            
            else:
                if self.playlist == 0:
                    await ctx.send("HERMANO TE REGALAS HEMOS ENCONTRADO LA CANCIÓN Y LA HEMOS METIDO EN LA COLA\n SE HA AÑADIDO: **"+song['title'].upper()+"** A LA LISTA\n")
                    
                self.q.append([song, vc])
                if not self.is_playing:
                    self.is_playing = True
                    await self.play(ctx)
                    #await asyncio.sleep(0.2)
    


    @commands.command()
    async def P(self, ctx, *args):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        self.ctx = ctx
        query = " ".join(args)
        vc = ctx.author.voice.channel

        if vc is None:
            await ctx.send("LA BOMBA BATISTA YA ESTA AQUI!")

        else:
            
            if 'spotify' in query:
                if 'playlist' not in query:
                    data = self.spotify_client.track(query)
                    query = data["name"] + " "+ data["artists"][0]['name']
                else:
                    result = self.spotify_client.playlist_items(query,limit=100)
                    data = result['items']
                    
                    while result['next']:
                        results = self.spotify_client.next(results)
                        data.extend(results['items'])
                    
                    data = [track['track']['name'] + " "+ track['track']['artists'][0]['name'] for track in data]
                    np.random.shuffle(data)
                    data = data[:30]
                    self.playlist = len(data)
                    
                    await ctx.send("HERMANO TE REGALAS HEMOS ENCONTRADO LA LISTA\n CARGANDO: **"+len(data)+" CANCIONES"+"** A LA COLA\n")

                    for song in data:
                        title = song.split()
                        await self.p(ctx, *title)
                        self.playlist -= 1
                    
                    await ctx.send("TODAS CARGADAS\n")

                    
                    return
            
            song = self.search_youtube(query)

            if not song:
                await ctx.send("TE HAS EQUIVOCADO EN ALGO O LOS SERVIDORES VAN MAL NOSE YO SOY SOLO BATISTA XD\n")
            
            else:
                if self.playlist == 0:
                    await ctx.send("HERMANO TE REGALAS HEMOS ENCONTRADO LA CANCIÓN Y LA HEMOS METIDO EN LA COLA\n SE HA AÑADIDO: **"+song['title'].upper()+"** A LA LISTA\n")
                self.q.append([song, vc])
                if not self.is_playing:
                    self.is_playing = True
                    await self.play(ctx)
    
    @commands.command()
    async def pause(self, ctx):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        server = ctx.message.guild
        voice_channel = server.voice_client
        voice_channel.pause()

    
    @commands.command()
    async def resume(self, ctx):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        server = ctx.message.guild
        voice_channel = server.voice_client
        voice_channel.resume()

    
    @commands.command()
    async def q(self, ctx):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        if not self.q and not self.is_playing:
            await ctx.send("NO HAY CANCIONES MANIN AÑADELAS")

        else:
            string = [("{} - ".format(i+1)+"**"+str(song[0]['title'])).upper()+"**" for i,song in enumerate([self.current_song]+self.q)]
            string[0]+="(current)"
            string = "\n".join(string)
            await ctx.send("LISTA ACTUAL: \n ------------------------------------------------------------- \n"+string)
    
    @commands.command()
    async def queue(self, ctx):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        if not self.q and not self.is_playing:
            await ctx.send("NO HAY CANCIONES MANIN AÑADELAS")

        else:
            string = [("{} - ".format(i+1)+"**"+str(song[0]['title'])).upper()+"**" for i,song in enumerate([self.current_song]+self.q)]
            string[0]+="(current)"
            string = "\n".join(string)
            await ctx.send("LISTA ACTUAL: \n ------------------------------------------------------------- \n"+string)
    

    @commands.command()
    async def s(self, ctx):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        if self.q:
            if self.playlist > 0:
                self.playlist -= 1
                
            self.voice_channel.stop()
            await self.next(ctx)
    
    @commands.command()
    async def skip(self, ctx):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        if self.q:
            if self.playlist > 0:
                self.playlist -= 1
            self.voice_channel.stop()
            await self.next(ctx)

        else:
            self.voice_channel.stop()
            self.is_playing = False
            self.ctx = ctx

    @commands.command()
    async def stop(self, ctx):
        self.playlist = 0
        self.voice_channel.stop()
        self.is_playing = False
        self.q = []

    @commands.command()
    async def rm(self, ctx, i):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        try:
            i = int(i)
            song = [self.current_song]+self.q
            song = song[i-1]
            await ctx.send("SE HA ELIMINADO: **"+song[0]['title'].upper()+"** DE LA LISTA\n")
            self.q.pop(i-2)
            if self.playlist > 0:
                self.playlist -= 1
        except Exception as e:
            await ctx.send("ESO NO ES UNA POSICIÓN DE LA LISTA CHULO\n")
    

    @commands.command()
    async def remove(self, ctx, i):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        try:
            i = int(i)
            song = [self.current_song]+self.q
            song = song[i-1]
            await ctx.send("SE HA ELIMINADO: **"+song[0]['title'].upper()+"** DE LA LISTA\n")
            self.q.pop(i-2)
            if self.playlist > 0:
                self.playlist -= 1
        except Exception as e:
            await ctx.send("ESO NO ES UNA POSICIÓN DE LA LISTA CHULO\n")

        
    
    @commands.command()
    async def dc(self,ctx):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        await self.voice_channel.disconnect()
        self.is_playing = False
        self.q = []
        self.playlist = 0
    
    @commands.command()
    async def disconnect(self,ctx):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        await self.voice_channel.disconnect()
        self.is_playing = False
        self.q = []
        self.playlist = 0
    
    
    @commands.command()
    async def login(self, ctx, *args):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        
        user  = args[0]
        status, data =self.db.verify_credentials(user)
        
        if status:
            await ctx.send("EY MIRAD QUIEN HA VENIDO. BIENVENIDO "+user+" TE HAS LOGEADO DE PUTA MADRE.")
            self.logged_users[ctx.author.display_name+"#"+ctx.author.discriminator] = user

        else:
            await ctx.send("TAS EQUIVOCAO NO TE ACUERDAS O QUE.")
    

    @commands.command()
    async def register(self, ctx, *args):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        
        user  = args[0]
        status, data =self.db.verify_credentials(user)
        
        if not status:
            self.db.add_user(user)
            await ctx.send("FELICIDADES HERMANO TU USUARIO "+user+" SE HA REGISTRADO AL MEJOR BOT DE EUROPA.")

        else:
            await ctx.send("EEEEEEE EL USUARIO YA EXISTE FUYERO NO INTENTES ROBAR.")
    

    @commands.command()
    async def mylists(self, ctx, *args):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        
        current = ctx.author.display_name+"#"+ctx.author.discriminator
        if current in self.logged_users:
            my_playlists = self.db.get_playlists(self.logged_users[current])
            if len(args) == 0:
                my_playlists = ["- **"+playlist+"**" for playlist in my_playlists.keys()]
                my_playlists = "\n".join(my_playlists)
                my_playlists = "TUS PLAYLISTS GUARDADAS \n ------------------------------------------------------------ \n" + my_playlists
                await ctx.send(my_playlists)
            else:
                name = args[0]
                try:
                    my_playlists = my_playlists[name]
                    string = [("{} - ".format(i+1)+"**"+song+"**") for i,song in enumerate(my_playlists)]
                    string = "\n".join(string)
                    await ctx.send("**{} SONGS**: \n ------------------------------------------------------------- \n".format(name)+string)

                except:
                    await ctx.send("O TE HAS INVENTADO LA PLAYLIST O ALGO FALLA LOCO.")


        else:
            await ctx.send("NECESITAS HACER LOGIN JAJAJAJJAJAJAJAJA.")
    

    @commands.command()
    async def save(self, ctx, *args):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        
        name  = args[0]
        current = ctx.author.display_name+"#"+ctx.author.discriminator
        if current in self.logged_users:
            songs = [(str(song[0]['title'])).upper() for song in [self.current_song]+self.q]
            status = self.db.update_playlist(self.logged_users[current],name,songs)
            if status:
                await ctx.send("SE HA GUARDADO LA PLAYLIST CORRECTAMENTE")
            else:
                await ctx.send("ALGO HA FALLADO HERMANO VUELVE A PROBAR.")

        else:
            await ctx.send("NECESITAS HACER LOGIN JAJAJAJJAJAJAJAJA.")
    

    @commands.command()
    async def load(self, ctx, *args):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        
        name  = args[0]
        current = ctx.author.display_name+"#"+ctx.author.discriminator
        if current in self.logged_users:
            my_playlist = self.db.get_playlists(self.logged_users[current])[name]
            if len(my_playlist) > 0:
                self.q = []
                for l in my_playlist:
                    title = l.split()
                    await self.p(ctx, *title)
                await ctx.send("SE HA CARGADO LA PLAYLIST CORRECTAMENTE.")
            else:
                await ctx.send("ALGO HA FALLADO HERMANO VUELVE A PROBAR.")

        else:
            await ctx.send("NECESITAS HACER LOGIN JAJAJAJJAJAJAJAJA.")
    

    @commands.command()
    async def delete(self, ctx, *args):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        
        name  = args[0]
        current = ctx.author.display_name+"#"+ctx.author.discriminator
        if current in self.logged_users:
            status = self.db.remove_playlist(self.logged_users[current],name)
            if status:
                await ctx.send("SE HA ELIMINADO LA PLAYLIST CORRECTAMENTE.")
            else:
                await ctx.send("ALGO HA FALLADO HERMANO VUELVE A PROBAR.")
        else:
            await ctx.send("NECESITAS HACER LOGIN JAJAJAJJAJAJAJAJA.")
    
    
    @commands.command()
    async def loop(self, ctx, *args):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        
        state  = args[0]
        if "on" in state:
            self.looping = True
            self.q2 = self.q + [self.current_song]
            await ctx.send("Loop ON")
        elif "song" in state:
            self.looping_song = True
            await ctx.send("Loop SONG")
        else:
            self.looping_song = False
            self.looping = False
            await ctx.send("Loop OFF")
    
    
    @commands.command()
    async def random(self, ctx, *args):
        if ctx.message.guild.name != "Hi Fi" and ctx.message.guild.name != "Los chavales":
            message = 'Este Bot no funciona en servidores de hijos de la gran puta.'
            await ctx.message.author.send(message)
            return
        
        state  = args[0]
        if "on" in state:
            self.rand = True
        else:
            self.rand = False
            await ctx.send("RAND OFF")
            
    
        
        
        
    




    @commands.command()
    async def h(self, ctx):
        commands = ["-h -help", "-p <name or url>", "-q -queue", "-s -skip", "-stop", "-rm -remove <index>", "-dc -disconnect", "-pause", "-resume", "-save <playlistname> (requires login)",
                    "-load <playlistname> (requires login)","-register <username>", "-login <username>", "-mylists (requires login)", "-mylists <playlistname> (requires login)", "-delete <playlistname> (requires login)"]

        info = ["AQUI TIENES TODA LA INFO DE LOS COMANDOS FIERA", "AÑADE CANCIONES PARA REPRODUCIR MAQUINA", "MUESTRA LAS CANCIONES EN LA COLA DE REPRODUCCIÓ DIPLODOCUS",
                "CUANDO TE DA PALO Y QUIERES LA SIGUIENTE WEON", "PARAR DE REPRODUCIR MUSICA JEFE", "ELIMINAR UNA DE LA LISTA PORQUE TE HAS EQUIVOCADO MERLUZO", "ME DESPIDES DEL TRABAJO TE MATO",
                 "PAUSAR LA CANCIÓN QUE ESTÁ EN MARCHA PANITA", "DESPAUSAR LA CANCION PAUSADA QUE EL PAUSADOR PAUSÓ O ALGO ASÍ", "GUARDAR LA COLA DE CANCIONES ACTUAL EN UNA PLAYLIST VINCULADA A TU CUENTA (A QUE MOLO???)",
                 "CARGAR TODAS LAS CANCIONES DE LA PLAYLIST GUARDADA A LA COLA PARA GOZARLO", "CREAR TU CUENTA DE USUARIO PARA PODER CREAR PLAYLISTS Y FLIPAR", "INICIAR SESION PARA OBTENER LAS MEJORES FUNCIONES DE TU VIDA",
                 "MIRAR TODAS TUS PLAYLISTS ASI PIM PAM", "MIRAR LAS CANCIONES QUE ESTAN EN LA PLAYLIST (POR SI ACASO NO TE ACUERDAS LOCO)", "ELIMINA LA PLAYLIST QUE ELIJAS PORQUE TE DA TODO EL ASCO CABRON."]
        
        string = ["{} : **{}.**".format(commands[i],info[i]) for i in range(len(commands))]
        string[0] = "LISTA DE COMANDOS \n ------------------------------------------------------------ \n" + string[0] 
        string = "\n".join(string)

        await ctx.send(string)
    
    
    async def autodc(self):
        while True:
            await asyncio.sleep(10*60) # 5 min
            if not self.is_playing and not self.dcc:
                self.dcc = True
                await self.voice_channel.disconnect()
                await self.ctx.send("ESTOY INTOXICADO FUUCKKKKK")

        


        

def run():
    bot = commands.Bot(command_prefix="-")
    music = MusicBot(bot)
    bot.add_cog(music)
    #bot.loop.create_task(music.autodc())
    bot.run(os.environ["DISCORD_KEY"])

run()