import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID
from db import add_bot, remove_bot, list_bots, get_bot

app = Client("iseng", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Simpan state interaksi user
user_states = {}

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
async def callback_handler(client, cq):
    data = cq.data

    # ✅ Tambah bot
    if data == "add_bot":
        if cq.from_user.id != OWNER_ID:
            return await cq.answer("Hanya Owner yang bisa menambahkan bot!", show_alert=True)
        await cq.message.reply("Kirim dengan format:\n\n`/addbot namabot token`")

    # ✅ Hapus bot
    elif data == "hapus_bot":
        bots = list_bots()
        if not bots:
            return await cq.message.reply("Tidak ada bot terdaftar.")
        buttons = [[InlineKeyboardButton(bot['name'], callback_data=f"hapus_{bot['name']}")] for bot in bots]
        await cq.message.reply("Pilih bot yang akan dihapus:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("hapus_"):
        name = data.split("_", 1)[1]
        if remove_bot(name):
            await cq.message.reply(f"✅ Bot {name} berhasil dihapus.")
        else:
            await cq.message.reply("❌ Gagal menghapus bot.")

    # ✅ Lihat daftar bot
    elif data == "lihat_daftar":
        bots = list_bots()
        if not bots:
            return await cq.message.reply("Tidak ada bot terdaftar.")
        buttons = [[InlineKeyboardButton(bot['name'], callback_data=f"lihat_{bot['name']}")] for bot in bots]
        await cq.message.reply("Daftar bot:", reply_markup=InlineKeyboardMarkup(buttons))

    # ✅ Pilih bot → tampilkan aksi
    elif data.startswith("lihat_"):
        name = data.split("_", 1)[1]
        buttons = [
            [InlineKeyboardButton("🚫 Banall", callback_data=f"banall_{name}")],
            [InlineKeyboardButton("📤 Send", callback_data=f"send_{name}")],
            [InlineKeyboardButton("🛡️ CekAdmin", callback_data=f"cekadmin_{name}")],
            [InlineKeyboardButton("👥 GetStaff", callback_data=f"getstaff_{name}")]
        ]
        await cq.message.reply(f"Bot {name} terdaftar.\nPilih aksi:", reply_markup=InlineKeyboardMarkup(buttons))

    # ✅ Banall
    elif data.startswith("banall_"):
        name = data.split("_", 1)[1]
        user_states[cq.from_user.id] = {"action": "banall", "bot": name}
        await cq.message.reply("Masukkan ID Grup/Channel target (-100xxx):")

    # ✅ Send
    elif data.startswith("send_"):
        name = data.split("_", 1)[1]
        user_states[cq.from_user.id] = {"action": "send_wait_id", "bot": name}
        await cq.message.reply("Masukkan ID Grup/Channel target untuk mengirim pesan:")

    # ✅ CekAdmin
    elif data.startswith("cekadmin_"):
        name = data.split("_", 1)[1]
        # ❗Catatan: perlu API userbot untuk benar-benar cek semua grup
        await cq.message.reply(f"⚠️ Fitur CekAdmin global belum bisa dipakai penuh.\nBot {name} hanya bisa cek lewat perintah manual.")

    # ✅ GetStaff
    elif data.startswith("getstaff_"):
        name = data.split("_", 1)[1]
        user_states[cq.from_user.id] = {"action": "getstaff", "bot": name}
        await cq.message.reply("Masukkan ID Grup/Channel target untuk mendapatkan daftar staff/admin:")

# =======================
# Handle input lanjutan
# =======================
@app.on_message(filters.text & ~filters.command(["start", "addbot", "banall"]))
async def handle_states(client, message):
    uid = message.from_user.id
    if uid not in user_states:
        return

    state = user_states[uid]

    # ✅ Banall
    if state["action"] == "banall":
        target = message.text.strip()
        await message.reply(f"🔄 Memulai banned all di {target}...")

        try:
            async for member in client.get_chat_members(target):
                try:
                    await client.ban_chat_member(target, member.user.id)
                except:
                    pass
            await message.reply("✅ Banned Telah Selesai")
        except:
            await message.reply("⚠️ Bot perlu interaksi ke grup.\nMengirim ayat Qur’an...")
            await client.send_message(
                target,
                f"{QURAN_ANTI_DEWASA['arab']}\n\n_{QURAN_ANTI_DEWASA['arti']}_"
            )
        del user_states[uid]

    # ✅ Send (minta isi pesan)
    elif state["action"] == "send_wait_id":
        user_states[uid]["target"] = message.text.strip()
        user_states[uid]["action"] = "send_wait_msg"
        await message.reply("Silakan kirim isi pesan yang ingin dikirim:")

    elif state["action"] == "send_wait_msg":
        target = state["target"]
        try:
            await client.send_message(target, message.text)
            await message.reply("✅ Pesan berhasil dikirim.")
        except:
            await message.reply("❌ Gagal mengirim pesan, pastikan bot sudah join & admin.")
        del user_states[uid]

    # ✅ GetStaff
    elif state["action"] == "getstaff":
        target = message.text.strip()
        try:
            admins = []
            async for m in client.get_chat_members(target, filter="administrators"):
                admins.append(f"- {m.user.first_name} ({m.user.id})")
            if admins:
                await message.reply("👥 Daftar Admin:\n" + "\n".join(admins))
            else:
                await message.reply("❌ Tidak ada admin ditemukan.")
        except:
            await message.reply("⚠️ Bot bukan admin atau tidak ada akses ke target.")
        del user_states[uid]

# =======================
# Add Bot CMD
# =======================
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

if __name__ == "__main__":
    app.run()
