import os
import discord
import asyncio
from discord.ext.commands.core import after_invoke
from discord.ext.commands import bot
from discord.ext import commands
from youtube_dl import YoutubeDL
from database_manager import DB_Manager

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_playing = False
        self.q = []
        self.YDL_OPTIONS = { "format": "bestaudio",
                             "noplaylists":"True" }

        self.FFMEPG_OPTIONS = { "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                "options": "-vn" }

        self.voice_channel = None
        self.current_song = None
        self.tmp = False
        self.db = DB_Manager(os.environ["FIRESTORE_SECRET_JSON"])
        self.logged_users = {}

    def search_youtube(self, item):

        ydl = YoutubeDL(self.YDL_OPTIONS)

        try:
            info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]

        except Exception:
            return {}
        
        return { 'source': info['formats'][0]['url'], 
                 'title': info['title'] }


    def next(self,ctx):

        if self.q:
            self.is_playing = True
            url = self.q[0][0]['source']
            self.current_song = self.q.pop(0)
            asyncio.run_coroutine_threadsafe(ctx.send("REPRODUCIENDO LA SIGUIENTE CANCION QUE FLIPAS: **{}** \n".format(self.current_song[0]['title'])),self.bot.loop)
            self.voice_channel.play(discord.FFmpegPCMAudio(url, **self.FFMEPG_OPTIONS), after=lambda e: self.next(ctx))

        else:
            self.is_playing = False
    

    async def play(self,ctx):

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
    async def p(self, ctx, *args):
        query = " ".join(args)
        vc = ctx.author.voice.channel

        if vc is None:
            await ctx.send("LA BOMBA BATISTA YA ESTA AQUI!")

        else:
            song = self.search_youtube(query)

            if not song:
                await ctx.send("TE HAS EQUIVOCADO EN ALGO O LOS SERVIDORES VAN MAL NOSE YO SOY SOLO BATISTA XD\n")
            
            else:
                await ctx.send("HERMANO TE REGALAS HEMOS ENCONTRADO LA CANCIÓN Y LA HEMOS METIDO EN LA COLA\n SE HA AÑADIDO: **"+song['title'].upper()+"** A LA LISTA\n")
                self.q.append([song, vc])
                if not self.is_playing:
                    self.is_playing = True
                    await self.play(ctx)
    
    @commands.command()
    async def pause(self, ctx):
        server = ctx.message.guild
        voice_channel = server.voice_client
        voice_channel.pause()

    
    @commands.command()
    async def resume(self, ctx):
        server = ctx.message.guild
        voice_channel = server.voice_client
        voice_channel.resume()

    
    @commands.command()
    async def q(self, ctx):
        if not self.q and not self.is_playing:
            await ctx.send("NO HAY CANCIONES MANIN AÑADELAS")

        else:
            string = [("{} - ".format(i+1)+"**"+str(song[0]['title'])).upper()+"**" for i,song in enumerate([self.current_song]+self.q)]
            string[0]+="(current)"
            string = "\n".join(string)
            await ctx.send("LISTA ACTUAL: \n ------------------------------------------------------------- \n"+string)
    
    @commands.command()
    async def queue(self, ctx):
        if not self.q and not self.is_playing:
            await ctx.send("NO HAY CANCIONES MANIN AÑADELAS")

        else:
            string = [("{} - ".format(i+1)+"**"+str(song[0]['title'])).upper()+"**" for i,song in enumerate([self.current_song]+self.q)]
            string[0]+="(current)"
            string = "\n".join(string)
            await ctx.send("LISTA ACTUAL: \n ------------------------------------------------------------- \n"+string)
    

    @commands.command()
    async def s(self, ctx):
        if self.q:
            self.voice_channel.stop()
            await self.next(ctx)

        else:
            self.voice_channel.stop()
    
    @commands.command()
    async def skip(self, ctx):
        if self.q:
            self.voice_channel.stop()
            await self.next(ctx)

        else:
            self.voice_channel.stop()

    @commands.command()
    async def stop(self, ctx):
        self.voice_channel.stop()
        self.is_playing = False
        self.q = []

    @commands.command()
    async def rm(self, ctx, i):
        try:
            i = int(i)
            song = [self.current_song]+self.q
            song = song[i-1]
            await ctx.send("SE HA ELIMINADO: **"+song[0]['title'].upper()+"** DE LA LISTA\n")
            self.q.pop(i-2)
        except Exception as e:
            await ctx.send("ESO NO ES UNA POSICIÓN DE LA LISTA CHULO\n")
    

    @commands.command()
    async def remove(self, ctx, i):
        try:
            i = int(i)
            song = [self.current_song]+self.q
            song = song[i-1]
            await ctx.send("SE HA ELIMINADO: **"+song[0]['title'].upper()+"** DE LA LISTA\n")
            self.q.pop(i-2)
        except Exception as e:
            await ctx.send("ESO NO ES UNA POSICIÓN DE LA LISTA CHULO\n")

        
    
    @commands.command()
    async def dc(self,ctx):
        await self.voice_channel.disconnect()
        self.is_playing = False
        self.q = []
    
    @commands.command()
    async def disconnect(self,ctx):
        await self.voice_channel.disconnect()
        self.is_playing = False
        self.q = []
    
    
    @commands.command()
    async def login(self, ctx, *args):
        user  = args[0]
        status, data =self.db.verify_credentials(user)
        
        if status:
            await ctx.send("EY MIRAD QUIEN HA VENIDO. BIENVENIDO "+user+" TE HAS LOGEADO DE PUTA MADRE.")
            self.logged_users[ctx.author.display_name+"#"+ctx.author.discriminator] = user

        else:
            await ctx.send("TAS EQUIVOCAO NO TE ACUERDAS O QUE.")
    

    @commands.command()
    async def register(self, ctx, *args):
        user  = args[0]
        status, data =self.db.verify_credentials(user)
        
        if not status:
            self.db.add_user(user)
            await ctx.send("FELICIDADES HERMANO TU USUARIO "+user+" SE HA REGISTRADO AL MEJOR BOT DE EUROPA.")

        else:
            await ctx.send("EEEEEEE EL USUARIO YA EXISTE FUYERO NO INTENTES ROBAR.")
    

    @commands.command()
    async def mylists(self, ctx, *args):
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

        








    

def run():
    bot = commands.Bot(command_prefix="-")
    bot.add_cog(MusicBot(bot))
    while True:
        try:
            bot.run(os.environ["DISCORD_KEY"])
        except:
            pass



run()