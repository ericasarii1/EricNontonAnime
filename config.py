import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
import requests
import asyncio
from threading import Thread
from pyrogram import Client
from pyrogram.raw.functions.phone import GetGroupCall
import subprocess

logging.basicConfig(level=logging.INFO)

# ==== Bagian anime bot kamu (tidak diubah) ====

def search_anime(title):
    query = '''
    query ($search: String) {
      Media(search: $search, type: ANIME) {
        id
        title {
          romaji
          english
          native
        }
        description(asHtml: false)
        episodes
        status
        genres
        averageScore
        siteUrl
      }
    }
    '''
    variables = {"search": title}
    url = "https://graphql.anilist.co"
    r = requests.post(url, json={'query': query, 'variables': variables})
    if r.status_code == 200:
        return r.json()["data"]["Media"]
    return None

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Halo! Ketik /anime <judul> untuk cari anime.")

def anime_command(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text("Masukkan judul anime setelah /anime, contoh:\n/anime Naruto")
        return
    title = " ".join(context.args)
    anime = search_anime(title)
    if anime:
        msg = f"🎬 *{anime['title']['romaji']}* ({anime['title']['english']})\n\n"
        msg += f"📖 {anime['description'][:500]}...\n\n"
        msg += f"📺 Episodes: {anime['episodes']}\n"
        msg += f"⭐ Score: {anime['averageScore']}\n"
        msg += f"🎭 Genres: {', '.join(anime['genres'])}\n"
        msg += f"🔗 [More info]({anime['siteUrl']})"
        
        buttons = []
        if anime['episodes'] and anime['episodes'] > 0:
            for ep in range(1, min(anime['episodes'], 6)):
                buttons.append([InlineKeyboardButton(f"Episode {ep}", callback_data=f"ep|{anime['id']}|{ep}")])
        reply_markup = InlineKeyboardMarkup(buttons)
        
        update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        update.message.reply_text("Anime tidak ditemukan.")

def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data.split("|")
    if data[0] == "ep":
        anime_id, ep_num = data[1], data[2]
        stream_link = f"https://youtube.com/watch?v=anime_episode_{anime_id}_{ep_num}"  # placeholder
        query.edit_message_text(f"Streaming Episode {ep_num}:\n{stream_link}")

# ==== Bagian userbot streaming ==== 

# Isi dengan API_ID dan API_HASH akun Telegram userbot-mu
API_ID = 1234567
API_HASH = "your_api_hash"
USERBOT_SESSION_NAME = "userbot_session"  # nama session pyrogram userbot

# Variabel global kontrol streaming
is_streaming = False
stream_process = None

app = Client(USERBOT_SESSION_NAME, api_id=API_ID, api_hash=API_HASH)

async def join_and_stream(chat_id: int):
    global is_streaming, stream_process
    await app.start()
    print("[Userbot] Started, mencoba join group call...")

    try:
        # Dapatkan group call
        group_call = await app.invoke(GetGroupCall(peer=await app.resolve_peer(chat_id)))
        print(f"[Userbot] Group call found: {group_call}")

        # Contoh streaming video file lokal 'sample.mp4' ke group call via ffmpeg
        # Ini contoh sederhana, streaming ke Telegram voice chat perlu ffmpeg pipe ke userbot audio/video
        # Setup ffmpeg command sesuai kebutuhan streaming voice+video

        # Contoh dummy: kita jalankan ffmpeg yang output-nya ke virtual device (ubah sesuai implementasi)
        ffmpeg_command = [
            "ffmpeg", "-re", "-i", "sample.mp4",
            "-f", "s16le", "-ar", "48000", "-ac", "2", "pipe:1"
        ]

        print("[Userbot] Mulai streaming...")
        stream_process = subprocess.Popen(ffmpeg_command)
        is_streaming = True

        # Tahan sampai streaming selesai atau dihentikan
        while is_streaming:
            await asyncio.sleep(1)

        # Stop streaming
        if stream_process:
            stream_process.terminate()
            stream_process = None
            print("[Userbot] Streaming dihentikan.")

    except Exception as e:
        print(f"[Userbot] Error: {e}")

    await app.stop()
    print("[Userbot] Userbot berhenti.")

def start_stream_thread(chat_id):
    asyncio.run(join_and_stream(chat_id))

# ==== Command live streaming di bot utama ====

def startstream_command(update: Update, context: CallbackContext):
    global is_streaming

    if is_streaming:
        update.message.reply_text("Streaming sudah berjalan.")
        return

    chat_id = update.effective_chat.id
    update.message.reply_text("Mencoba memulai live streaming di obrolan video grup...")

    # Jalankan userbot streaming di thread terpisah
    thread = Thread(target=start_stream_thread, args=(chat_id,))
    thread.start()

def stopstream_command(update: Update, context: CallbackContext):
    global is_streaming, stream_process
    if not is_streaming:
        update.message.reply_text("Streaming belum berjalan.")
        return

    is_streaming = False
    if stream_process:
        stream_process.terminate()
        stream_process = None

    update.message.reply_text("Live streaming dihentikan.")

# ==== Main bot setup ====

def main():
    updater = Updater("TOKEN_BOT")
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("anime", anime_command))
    dp.add_handler(CallbackQueryHandler(button_callback))

    # Tambah handler live streaming
    dp.add_handler(CommandHandler("startstream", startstream_command))
    dp.add_handler(CommandHandler("stopstream", stopstream_command))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
