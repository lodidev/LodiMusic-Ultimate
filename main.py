import discord
from discord.ext import commands
import yt_dlp
import lyricsgenius
import asyncio

# --- CONFIGURAÇÕES ---
AUTHOR = "LodiDEV"
LODI_COLOR = 0x00FFFF 
 
 # NESSA ETAPA VOCÊ VAI PRECISAR CRIAR UMA CONTA NO GENIUS.COM/API-CLIENTES GERAR O TOKEN
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
genius = lyricsgenius.Genius(" TOKEN DO GENIUS AQUI")

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': False, 'quiet': True, 'default_search': 'ytsearch'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

queues = {}
active_filters = {}

FILTERS = {
    "bassboost": "bass=g=15,caps=20",
    "nightcore": "asetrate=44100*1.25,aresample=44100",
    "slow": "asetrate=44100*0.8,aresample=44100",
    "karaoke": "stereotools=mlev=0.03"
}

async def check_queue(ctx):
    if queues[ctx.guild.id]:
        track = queues[ctx.guild.id].pop(0)
        await play_music(ctx, track)

async def play_music(ctx, track):
    options = FFMPEG_OPTIONS.copy()
    if ctx.guild.id in active_filters:
        options['options'] += f" -af \"{active_filters[ctx.guild.id]}\""
    
    source = await discord.FFmpegOpusAudio.from_probe(track['url'], **options)
    ctx.voice_client.play(source, after=lambda e: bot.loop.create_task(check_queue(ctx)))
    
    embed = discord.Embed(title="🎶 Tocando Agora", description=f"**{track['title']}**", color=LODI_COLOR)
    embed.set_thumbnail(url=track['thumb'])
    embed.set_footer(text=f"Filtro: {active_filters.get(ctx.guild.id, 'Nenhum')} | LodiDEV Ultimate")
    await ctx.send(embed=embed)

@bot.command(name="play")
async def play(ctx, *, search: str):
    if not ctx.author.voice: return await ctx.send("❌ Entre num canal de voz!")
    if not ctx.voice_client: await ctx.author.voice.channel.connect()

    async with ctx.typing():
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(search, download=False)
            if 'entries' in info: info = info['entries'][0]
            track = {'url': info['url'], 'title': info['title'], 'thumb': info['thumbnail']}

        if ctx.guild.id not in queues: queues[ctx.guild.id] = []
        
        if ctx.voice_client.is_playing():
            queues[ctx.guild.id].append(track)
            await ctx.send(f"✅ **{track['title']}** adicionada à fila por {AUTHOR}!")
        else:
            await play_music(ctx, track)

@bot.command(name="filter")
async def apply_filter(ctx, tipo: str = None):
    if tipo is None or tipo.lower() not in FILTERS:
        return await ctx.send(f"❓ Filtros: `{', '.join(FILTERS.keys())}` ou `reset`")
    
    if tipo.lower() == "reset":
        active_filters.pop(ctx.guild.id, None)
        await ctx.send("✅ Filtros resetados para a próxima música.")
    else:
        active_filters[ctx.guild.id] = FILTERS[tipo.lower()]
        await ctx.send(f"🚀 Filtro **{tipo.upper()}** aplicado!")

@bot.command(name="queue")
async def show_queue(ctx):
    if ctx.guild.id not in queues or not queues[ctx.guild.id]:
        return await ctx.send("📋 A fila está vazia.")
    
    lista = "\n".join([f"{i+1}. {t['title']}" for i, t in enumerate(queues[ctx.guild.id][:10])])
    embed = discord.Embed(title="📋 Fila de Reprodução", description=lista, color=LODI_COLOR)
    embed.set_footer(text=f"LodiMusic | {AUTHOR}")
    await ctx.send(embed=embed)

@bot.command(name="skip")
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop() # O after do play_music já chama a próxima
        await ctx.send("⏭️ Pulei para a próxima!")

@bot.command(name="lyrics")
async def lyrics(ctx, *, track: str = None):
    async with ctx.typing():
        song = genius.search_song(track)
        if song:
            embed = discord.Embed(title=f"📜 {song.title}", description=song.lyrics[:1900], color=LODI_COLOR)
            embed.set_footer(text=f"Genius Lyrics | {AUTHOR}")
            await ctx.send(embed=embed)
        else: await ctx.send("❌ Letra não encontrada.")

@bot.command(name="stop")
async def stop(ctx):
    if ctx.voice_client:
        queues[ctx.guild.id] = []
        await ctx.voice_client.disconnect()
        await ctx.send(f"👋 Bot desconectado por {AUTHOR}.")

@bot.event
async def on_ready():
    print(f'--- {AUTHOR} ULTIMATE ONLINE ---')

bot.run(" TOKEN DO SEU BOT AQUI ")