import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID
from db import add_bot, remove_bot, list_bots, get_bot

app = Client("iseng", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

QURAN_ANTI_DEWASA = {
    "arab": "قُل لِّلْمُؤْمِنِينَ يَغُضُّوا۟ مِنْ أَبْصَـٰرِهِمْ وَيَحْفَظُوا۟ فُرُوجَهُمْ ۚ ذَٰلِكَ أَزْكَىٰ لَهُمْ ۗ إِنَّ ٱللَّهَ خَبِيرٌۢ بِمَا يَصْنَعُونَ",
    "arti": "Katakanlah kepada orang laki-laki yang beriman: Hendaklah mereka menahan pandangannya, dan memelihara kemaluannya; yang demikian itu lebih suci bagi mereka. Sesungguhnya Allah Maha Mengetahui apa yang mereka perbuat. (QS An-Nur:30)"
}

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    buttons = [
        [InlineKeyboardButton("➕ Add Bot", callback_data="add_bot")],
        [InlineKeyboardButton("🗑️ Hapus Bot", callback_data="hapus_bot")],
        [InlineKeyboardButton("📜 Lihat Daftar", callback_data="lihat_daftar")]
    ]
    await message.reply_photo(
        photo="https://files.catbox.moe/dh73a7.jpg",
        caption="🤖 Selamat datang! Silakan pilih menu.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    if data == "add_bot":
        if callback_query.from_user.id != OWNER_ID:
            await callback_query.answer("Hanya Owner yang bisa menambahkan bot!", show_alert=True)
            return
        await callback_query.message.reply("Kirim dengan format:\n\n`/addbot namabot token`")

    elif data == "hapus_bot":
        bots = list_bots()
        if not bots:
            await callback_query.message.reply("Tidak ada bot terdaftar.")
            return
        buttons = [[InlineKeyboardButton(bot['name'], callback_data=f"hapus_{bot['name']}")] for bot in bots]
        await callback_query.message.reply("Pilih bot yang akan dihapus:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("hapus_"):
        name = data.split("_", 1)[1]
        if remove_bot(name):
            await callback_query.message.reply(f"✅ Bot {name} berhasil dihapus.")
        else:
            await callback_query.message.reply("❌ Gagal menghapus bot.")

    elif data == "lihat_daftar":
        bots = list_bots()
        if not bots:
            await callback_query.message.reply("Tidak ada bot terdaftar.")
            return
        buttons = [[InlineKeyboardButton(bot['name'], callback_data=f"lihat_{bot['name']}")] for bot in bots]
        await callback_query.message.reply("Daftar bot:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("lihat_"):
        name = data.split("_", 1)[1]
        await callback_query.message.reply(
            f"Bot {name} terdaftar.\nPilih aksi:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚫 Banall", callback_data=f"banall_{name}")]
            ])
        )

    elif data.startswith("banall_"):
        name = data.split("_", 1)[1]
        await callback_query.message.reply("Kirim ID Group/Channel (-100xxxx) untuk Banall dengan format:\n\n`/banall -100123456789`")

@app.on_message(filters.command("addbot"))
async def add_bot_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ Hanya Owner yang bisa menambahkan bot!")
    try:
        _, name, token = message.text.split(" ", 2)
        if add_bot(name, token):
            await message.reply(f"✅ Bot {name} berhasil ditambahkan.\nJika diklik start, bot akan menampilkan ayat Qur’an anti-dewasa.")
        else:
            await message.reply("❌ Bot sudah ada di database.")
    except:
        await message.reply("Format salah!\nGunakan: `/addbot namabot token`")

@app.on_message(filters.command("banall"))
async def banall_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply("❌ Format salah!\nGunakan: `/banall -100xxxx`")
    target = message.command[1]
    await message.reply(f"🔄 Memulai banned all di {target}...")

    try:
        async for member in client.get_chat_members(target):
            try:
                await client.ban_chat_member(target, member.user.id)
            except:
                pass
        await message.reply("✅ Banned Telah Selesai")
    except:
        await message.reply(f"⚠️ Bot perlu interaksi ke grup.\nMengirim ayat Qur’an...")
        await client.send_message(
            target,
            f"{QURAN_ANTI_DEWASA['arab']}\n\n_{QURAN_ANTI_DEWASA['arti']}_"
        )

if __name__ == "__main__":
    app.run()
