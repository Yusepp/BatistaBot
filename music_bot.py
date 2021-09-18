import os
import discord
from discord.ext.commands.core import after_invoke
from discord.ext.commands import bot
from discord.ext import commands
from youtube_dl import YoutubeDL

class MusicBot(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.is_playing = False
        self.q = []
        self.YDL_OPTIONS = { "format": "bestaudio",
                             "noplaylists":"True" }

        self.FFMEPG_OPTIONS = { "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                "options": "-vn" }

        self.voice_channel = None
        self.current_song = None
    

    def search_youtube(self, item) -> dict:

        ydl = YoutubeDL(self.YDL_OPTIONS)

        try:
            info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]

        except Exception:
            return {}
        
        return { 'source': info['formats'][0]['url'], 
                 'title': info['title'] }


    async def next(self,ctx) -> None:

        if self.q:
            self.is_playing = True
            url = self.q[0][0]['source']
            self.current_song = self.q.pop(0)
            await ctx.send("REPRODUCIENDO LA SIGUIENTE CANCION QUE FLIPAS: {} \n".format(self.current_song[0]['title']))
            self.voice_channel.play(discord.FFmpegPCMAudio(url, **self.FFMEPG_OPTIONS), after=lambda e: self.next(ctx))

        else:
            self.is_playing = False
    

    async def play(self,ctx) -> None:

        if self.q:
            self.is_playing = True
            url = self.q[0][0]['source']

            if not self.voice_channel or not self.voice_channel.is_connected():
                self.voice_channel = await self.q[0][1].connect()
            
            self.current_song = self.q.pop(0)
            self.voice_channel.play(discord.FFmpegPCMAudio(url, **self.FFMEPG_OPTIONS), after=lambda e: self.next(ctx))
        
        else:
            self.is_playing = False
    
    @commands.command()
    async def p(self, ctx, *args) -> None:
        query = " ".join(args)
        vc = ctx.author.voice.channel

        if vc is None:
            await ctx.send("LA BOMBA BATISTA YA ESTA AQUI!")

        else:
            song = self.search_youtube(query)

            if not song:
                await ctx.send("TE HAS EQUIVOCADO EN ALGO O LOS SERVIDORES VAN MAL NOSE YO SOY SOLO BATISTA XD\n")
            
            else:
                await ctx.send("HERMANO TE REGALAS HEMOS ENCONTRADO LA CANCIÓN Y LA HEMOS METIDO EN LA COLA\n")
                await ctx.send("SE HA AÑADIDO: "+song['title'].upper()+" A LA LISTA\n")
                self.q.append([song, vc])
                if not self.is_playing:
                    self.is_playing = True
                    await self.play(ctx)


    @commands.command()
    async def q(self, ctx) -> None:
        if not self.q and not self.is_playing:
            await ctx.send("NO HAY CANCIONES MANIN AÑADELAS")

        else:
            string = [("{}- ".format(i+1)+str(song[0]['title'])).upper() for i,song in enumerate([self.current_song]+self.q)]
            string = "\n".join(string)
            await ctx.send("LISTA ACTUAL: \n"+string)
    

    @commands.command()
    async def s(self, ctx) -> None:
        if self.q:
            self.voice_channel.stop()
            await self.next(ctx)

        else:
            await ctx.send("COMO VAS A SKIPPEAR ALGO QUE NO EXISTE CRACK")
            self.voice_channel.stop()
    

    @commands.command()
    async def stop(self, ctx) -> None:
        self.voice_channel.stop()
        self.is_playing = False
        self.q = []

    @commands.command()
    async def rm(self, ctx, i) -> None:
        try:
            song = ([self.curren_song]+self.q)[i-1]
            await ctx.send("SE HA ELIMINADO: "+song['title'].upper()+" DE LA LISTA\n")
            self.q.remove(song)
        except:
            await ctx.send("ESO NO ES UNA POSICIÓN DE LA LISTA CHULO\n")

        
    
    @commands.command()
    async def dc(self,ctx) -> None:
        await self.voice_channel.disconnect()
        self.is_playing = False
        self.q = []
    

def run() -> None:
    bot = commands.Bot(command_prefix="-")
    bot.add_cog(MusicBot(bot))
    bot.run(os.environ["DISCORD_KEY"])


run()