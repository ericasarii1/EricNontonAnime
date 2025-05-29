import os
import yt_dlp
import httpx
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.types import Message

# Ganti ini dengan data bot kamu
API_ID = 123456
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"

app = Client("otakudesu_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("anime") & (filters.private | filters.group))
async def search_otakudesu(_, message: Message):
    if len(message.command) < 2:
        return await message.reply("Contoh: `/anime jujutsu kaisen`", quote=True)

    query = " ".join(message.command[1:])
    search_url = f"https://otakudesu.cloud/?s={query.replace(' ', '+')}"
    await message.reply("🔍 Lagi nyari dulu ya...", quote=True)

    try:
        # Scrape hasil pencarian
        async with httpx.AsyncClient() as client:
            r = await client.get(search_url, follow_redirects=True)
            soup = BeautifulSoup(r.text, "html.parser")
            result = soup.select_one("div.venutama div.venutama a")

            if not result:
                return await message.reply("Anime gak ketemu 😔", quote=True)

            anime_url = result['href']

            # Masuk ke halaman anime dan ambil episode pertama (terbaru)
            r = await client.get(anime_url)
            soup = BeautifulSoup(r.text, "html.parser")
            episode_link = soup.select_one(".episodelist ul li a")

            if not episode_link:
                return await message.reply("Gagal ambil episode 😭", quote=True)

            episode_url = episode_link['href']

        await message.reply("📥 Download dulu ya bentar...", quote=True)

        # Download video pakai yt-dlp
        ydl_opts = {
            'quiet': True,
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'anime_temp.%(ext)s'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(episode_url, download=True)
            file_path = ydl.prepare_filename(info)

        await message.reply_video(file_path, caption=f"Nih anime-nya: {query.title()} 🎬", quote=True)

        os.remove(file_path)

    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}", quote=True)

app.run()
