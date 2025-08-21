import os
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from dotenv import load_dotenv
from db import add_bot, remove_bot, get_bots, save_state, get_state, clear_state

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

main_bot = Client(
    "main_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Startup message
async def startup():
    await main_bot.start()
    me = await main_bot.get_me()
    print(f"✅ Bot {me.first_name} (@{me.username}) telah dijalankan")
    await main_bot.stop()

# Fungsi untuk tombol utama
def main_menu():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ Add Bot", callback_data="add_bot")],
            [InlineKeyboardButton("❌ Hapus Bot", callback_data="hapus_bot")],
            [InlineKeyboardButton("📜 Lihat Daftar", callback_data="lihat_daftar")]
        ]
    )

# Handler /start
@main_bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ Kamu tidak diizinkan menggunakan bot ini.")

    await message.reply_photo(
        "https://files.catbox.moe/dh73a7.jpg",
        caption="🤖 Selamat datang di Panel Bot\n\nGunakan tombol di bawah untuk mengelola bot.",
        reply_markup=main_menu()
    )

# Callback untuk tombol
@main_bot.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data

    if data == "add_bot":
        await callback_query.message.reply("🔑 Kirimkan Bot Token untuk didaftarkan:")
        save_state(callback_query.from_user.id, {"action": "awaiting_bot_token"})

    elif data == "hapus_bot":
        bots = get_bots()
        if not bots:
            return await callback_query.message.reply("⚠️ Belum ada bot yang terdaftar.")
        keyboard = [[InlineKeyboardButton(b["name"], callback_data=f"del_{b['token']}")] for b in bots]
        await callback_query.message.reply("Pilih bot untuk dihapus:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "lihat_daftar":
        bots = get_bots()
        if not bots:
            return await callback_query.message.reply("📭 Tidak ada bot yang terdaftar.")
        keyboard = [[InlineKeyboardButton(b["name"], callback_data=f"bot_{b['token']}")] for b in bots]
        await callback_query.message.reply("📜 Daftar Bot Terdaftar:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("del_"):
        token = data.split("_", 1)[1]
        remove_bot(token)
        await callback_query.message.reply("✅ Bot berhasil dihapus dari daftar.")

    elif data.startswith("bot_"):
        token = data.split("_", 1)[1]
        # Sub menu bot
        keyboard = [
            [InlineKeyboardButton("🚫 BanAll", callback_data=f"banall_{token}")],
            [InlineKeyboardButton("📤 Send", callback_data=f"send_{token}")],
            [InlineKeyboardButton("👮 CekAdmin", callback_data=f"cekadmin_{token}")],
            [InlineKeyboardButton("👥 GetStaff", callback_data=f"getstaff_{token}")]
        ]
        await callback_query.message.reply("Pilih aksi untuk bot ini:", reply_markup=InlineKeyboardMarkup(keyboard))


# Handler untuk input teks (misal token, id, pesan)
@main_bot.on_message(filters.text & filters.private)
async def text_handler(client, message: Message):
    state = get_state(message.from_user.id)
    if not state:
        return

    action = state.get("action")

    # Menyimpan bot token baru
    if action == "awaiting_bot_token":
        token = message.text.strip()
        try:
            new_bot = Client("sub_bot", api_id=API_ID, api_hash=API_HASH, bot_token=token)
            await new_bot.start()
            me = await new_bot.get_me()
            add_bot(token, me.first_name)
            await message.reply(f"✅ Bot {me.first_name} (@{me.username}) berhasil didaftarkan!")
            await new_bot.stop()
        except Exception as e:
            await message.reply(f"❌ Gagal mendaftarkan bot: {e}")
        finally:
            clear_state(message.from_user.id)


if __name__ == "__main__":
    asyncio.run(startup())
    main_bot.run()
