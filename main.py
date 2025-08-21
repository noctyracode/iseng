import asyncio
import signal
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

# =======================
# Helper untuk jalanin bot terdaftar
# =======================
async def run_with_bot(bot_name, func, *args, **kwargs):
    bot = get_bot(bot_name)
    if not bot:
        return None, f"❌ Bot {bot_name} tidak ditemukan di database."

    token = bot["token"]
    async with Client(
        f"bot_{bot_name}",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=token,
        no_updates=True
    ) as subbot:
        try:
            result = await func(subbot, *args, **kwargs)
            return result, None
        except Exception as e:
            # Handling khusus Peer_ID_Invalid
            if "PEER_ID_INVALID" in str(e):
                return None, "⚠️ Error: Bot belum kenal ID target. Pastikan bot sudah join & pernah ada aktivitas di grup itu."
            return None, f"❌ Error pada bot {bot_name}: {str(e)}"

# =======================
# START
# =======================
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

# =======================
# CALLBACK HANDLER
# =======================
@app.on_callback_query()
async def callback_handler(client, cq):
    data = cq.data

    # Tambah bot
    if data == "add_bot":
        if cq.from_user.id != OWNER_ID:
            return await cq.answer("Hanya Owner yang bisa menambahkan bot!", show_alert=True)
        return await cq.message.reply("Kirim dengan format:\n\n`/addbot namabot token`")

    # Hapus bot
    elif data == "hapus_bot":
        bots = list_bots()
        if not bots:
            return await cq.message.reply("Tidak ada bot terdaftar.")
        # ambil nama dari DB
        buttons = [[InlineKeyboardButton(bot['name'], callback_data=f"hapus_{bot['name']}")] for bot in bots]
        return await cq.message.reply("Pilih bot yang akan dihapus:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("hapus_"):
        name = data.split("_", 1)[1]
        if remove_bot(name):
            return await cq.message.reply(f"✅ Bot {name} berhasil dihapus.")
        return await cq.message.reply("❌ Gagal menghapus bot.")

    # Lihat daftar bot
    elif data == "lihat_daftar":
        bots = list_bots()
        if not bots:
            return await cq.message.reply("Tidak ada bot terdaftar.")

        buttons = []
        for b in bots:
            token = b["token"]
            try:
                async with Client(f"check_{b['name']}", api_id=API_ID, api_hash=API_HASH, bot_token=token, no_updates=True) as tempbot:
                    me = await tempbot.get_me()
                    buttons.append([InlineKeyboardButton(me.first_name, callback_data=f"lihat_{b['name']}")])
            except:
                buttons.append([InlineKeyboardButton(b['name'], callback_data=f"lihat_{b['name']}")])

        return await cq.message.reply("Daftar bot terdaftar:", reply_markup=InlineKeyboardMarkup(buttons))

    # Pilih bot → tampilkan aksi
    elif data.startswith("lihat_"):
        name = data.split("_", 1)[1]
        buttons = [
            [InlineKeyboardButton("🚫 Banall", callback_data=f"banall_{name}")],
            [InlineKeyboardButton("📤 Send", callback_data=f"send_{name}")],
            [InlineKeyboardButton("👥 GetStaff", callback_data=f"getstaff_{name}")]
        ]
        return await cq.message.reply(f"Bot {name} terdaftar.\nPilih aksi:", reply_markup=InlineKeyboardMarkup(buttons))

    # Banall
    elif data.startswith("banall_"):
        name = data.split("_", 1)[1]
        user_states[cq.from_user.id] = {"action": "banall", "bot": name}
        return await cq.message.reply("Masukkan ID Grup/Channel target (-100xxx):")

    # Send
    elif data.startswith("send_"):
        name = data.split("_", 1)[1]
        user_states[cq.from_user.id] = {"action": "send_wait_id", "bot": name}
        return await cq.message.reply("Masukkan ID Grup/Channel target untuk mengirim pesan:")

    # GetStaff
    elif data.startswith("getstaff_"):
        name = data.split("_", 1)[1]
        user_states[cq.from_user.id] = {"action": "getstaff", "bot": name}
        return await cq.message.reply("Masukkan ID Grup/Channel target untuk mendapatkan daftar staff/admin:")

# =======================
# STATE HANDLER
# =======================
@app.on_message(filters.text & ~filters.command(["start", "addbot"]))
async def handle_states(client, message):
    uid = message.from_user.id
    if uid not in user_states:
        return
    state = user_states[uid]

    # Banall
    if state["action"] == "banall":
        target = message.text.strip()
        name = state["bot"]

        async def do_banall(bot, chat_id):
            async for member in bot.get_chat_members(chat_id):
                try:
                    await bot.ban_chat_member(chat_id, member.user.id)
                except:
                    pass

        _, err = await run_with_bot(name, do_banall, target)
        if err:
            await message.reply(err)
            await run_with_bot(
                name,
                lambda b, c: b.send_message(c, f"{QURAN_ANTI_DEWASA['arab']}\n\n_{QURAN_ANTI_DEWASA['arti']}_"),
                target
            )
        else:
            await message.reply("✅ Banned Telah Selesai")
        del user_states[uid]

    # Send
    elif state["action"] == "send_wait_id":
        user_states[uid]["target"] = message.text.strip()
        user_states[uid]["action"] = "send_wait_msg"
        return await message.reply("Silakan kirim isi pesan yang ingin dikirim:")

    elif state["action"] == "send_wait_msg":
        target = state["target"]
        name = state["bot"]

        _, err = await run_with_bot(name, lambda b, c, t: b.send_message(c, t), target, message.text)
        if err:
            await message.reply(err)
        else:
            await message.reply("✅ Pesan berhasil dikirim.")
        del user_states[uid]

    # GetStaff
    elif state["action"] == "getstaff":
        target = message.text.strip()
        name = state["bot"]

        async def do_getstaff(bot, chat_id):
            admins = []
            async for m in bot.get_chat_members(chat_id, filter="administrators"):
                admins.append(f"- {m.user.first_name} ({m.user.id})")
            return admins

        admins, err = await run_with_bot(name, do_getstaff, target)
        if err:
            await message.reply(err)
        else:
            if admins:
                await message.reply("👥 Daftar Admin:\n" + "\n".join(admins))
            else:
                await message.reply("❌ Tidak ada admin ditemukan.")
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

# =======================
# Pesan saat start/stop
# =======================
def on_start():
    async def _inner():
        async with app:
            me = await app.get_me()
            print(f"✅ Bot {me.first_name} (@{me.username}) berhasil dijalankan!")
    asyncio.get_event_loop().run_until_complete(_inner())

def on_stop(*args):
    async def _inner():
        async with app:
            me = await app.get_me()
            print(f"🛑 Bot {me.first_name} (@{me.username}) dihentikan!")
    asyncio.get_event_loop().run_until_complete(_inner())
    exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, on_stop)
    signal.signal(signal.SIGTERM, on_stop)
    on_start()
    app.run()
