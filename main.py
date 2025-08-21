import asyncio
import signal
import sys
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID
from db import add_bot, remove_bot, list_bots, get_bot

app = Client("iseng", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# State user
user_states = {}

QURAN_ANTI_DEWASA = {
    "arab": "قُل لِّلْمُؤْمِنِينَ يَغُضُّوا۟ مِنْ أَبْصَـٰرِهِمْ وَيَحْفَظُوا۟ فُرُوجَهُمْ ۚ ذَٰلِكَ أَزْكَىٰ لَهُمْ ۗ إِنَّ ٱللَّهَ خَبِيرٌۢ بِمَا يَصْنَعُونَ",
    "arti": "Katakanlah kepada orang laki-laki yang beriman: Hendaklah mereka menahan pandangannya, dan memelihara kemaluannya; yang demikian itu lebih suci bagi mereka. Sesungguhnya Allah Maha Mengetahui apa yang mereka perbuat. (QS An-Nur:30)"
}

# ==========================
# Helper fungsi bot terdaftar
# ==========================
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
            # Pastikan peer dikenali dulu
            if "target" in kwargs:
                try:
                    await subbot.get_chat(kwargs["target"])
                except Exception as e:
                    return None, f"❌ Gagal mengenali target: {str(e)}"

            result = await func(subbot, *args, **kwargs)
            return result, None
        except Exception as e:
            return None, f"❌ Error pada bot {bot_name}: {str(e)}"

# ==========================
# Commands
# ==========================
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

@app.on_message(filters.command("addbot"))
async def add_bot_cmd(client, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ Hanya Owner yang bisa menambahkan bot!")
    try:
        _, name, token = message.text.split(" ", 2)
        if add_bot(name, token):
            await message.reply(f"✅ Bot {name} berhasil ditambahkan.")
        else:
            await message.reply("❌ Bot sudah ada di database.")
    except:
        await message.reply("Format salah!\nGunakan: `/addbot namabot token`")

# ==========================
# Callback
# ==========================
@app.on_callback_query()
async def callback_handler(client, cq):
    data = cq.data

    if data == "add_bot":
        if cq.from_user.id != OWNER_ID:
            return await cq.answer("Hanya Owner yang bisa menambahkan bot!", show_alert=True)
        return await cq.message.reply("Kirim dengan format:\n\n`/addbot namabot token`")

    elif data == "hapus_bot":
        bots = list_bots()
        if not bots:
            return await cq.message.reply("Tidak ada bot terdaftar.")
        buttons = [[InlineKeyboardButton(bot['name'], callback_data=f"hapus_{bot['name']}")] for bot in bots]
        return await cq.message.reply("Pilih bot yang akan dihapus:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("hapus_"):
        name = data.split("_", 1)[1]
        if remove_bot(name):
            return await cq.message.reply(f"✅ Bot {name} berhasil dihapus.")
        return await cq.message.reply("❌ Gagal menghapus bot.")

    elif data == "lihat_daftar":
        bots = list_bots()
        if not bots:
            return await cq.message.reply("Tidak ada bot terdaftar.")

        buttons = []
        for bot in bots:
            token = bot["token"]
            try:
                async with Client(
                    f"tmp_{bot['name']}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    bot_token=token,
                    no_updates=True
                ) as tmpbot:
                    me = await tmpbot.get_me()
                    buttons.append([InlineKeyboardButton(me.first_name, callback_data=f"lihat_{bot['name']}")])
            except:
                buttons.append([InlineKeyboardButton(bot['name'], callback_data=f"lihat_{bot['name']}")])

        return await cq.message.reply("Daftar bot:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("lihat_"):
        name = data.split("_", 1)[1]
        buttons = [
            [InlineKeyboardButton("🚫 Banall", callback_data=f"banall_{name}")],
            [InlineKeyboardButton("📤 Send", callback_data=f"send_{name}")],
            [InlineKeyboardButton("👥 GetStaff", callback_data=f"getstaff_{name}")]
        ]
        return await cq.message.reply(f"Bot {name} terdaftar.\nPilih aksi:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("banall_"):
        name = data.split("_", 1)[1]
        user_states[cq.from_user.id] = {"action": "banall", "bot": name}
        return await cq.message.reply("Masukkan ID Grup/Channel target (-100xxx):")

    elif data.startswith("send_"):
        name = data.split("_", 1)[1]
        user_states[cq.from_user.id] = {"action": "send_wait_id", "bot": name}
        return await cq.message.reply("Masukkan ID Grup/Channel target:")

    elif data.startswith("getstaff_"):
        name = data.split("_", 1)[1]
        user_states[cq.from_user.id] = {"action": "getstaff", "bot": name}
        return await cq.message.reply("Masukkan ID Grup/Channel target untuk daftar staff/admin:")

# ==========================
# State handler
# ==========================
@app.on_message(filters.text & ~filters.command(["start", "addbot"]))
async def handle_states(client, message):
    uid = message.from_user.id
    if uid not in user_states:
        return
    state = user_states[uid]

    # 🚫 Banall
    if state["action"] == "banall":
        target = message.text.strip()
        name = state["bot"]

        async def do_banall(bot, chat_id):
            async for member in bot.get_chat_members(chat_id):
                try:
                    await bot.ban_chat_member(chat_id, member.user.id)
                except:
                    pass

        _, err = await run_with_bot(name, do_banall, target=target, chat_id=target)
        if err:
            await message.reply(f"{err}\nMengirim ayat Qur’an...")
            await run_with_bot(
                name,
                lambda b, c: b.send_message(c, f"{QURAN_ANTI_DEWASA['arab']}\n\n_{QURAN_ANTI_DEWASA['arti']}_"),
                target=target,
                c=target
            )
        else:
            await message.reply("✅ Banned Telah Selesai")
        del user_states[uid]

    # 📤 Send
    elif state["action"] == "send_wait_id":
        user_states[uid]["target"] = message.text.strip()
        user_states[uid]["action"] = "send_wait_msg"
        return await message.reply("Silakan kirim isi pesan yang ingin dikirim:")

    elif state["action"] == "send_wait_msg":
        target = state["target"]
        name = state["bot"]
        _, err = await run_with_bot(
            name,
            lambda b, c, t: b.send_message(c, t),
            target=target,
            c=target,
            t=message.text
        )
        if err:
            await message.reply(err)
        else:
            await message.reply("✅ Pesan berhasil dikirim.")
        del user_states[uid]

    # 👥 GetStaff
    elif state["action"] == "getstaff":
        target = message.text.strip()
        name = state["bot"]

        async def do_getstaff(bot, chat_id):
            admins = []
            async for m in bot.get_chat_members(chat_id, filter="administrators"):
                admins.append(f"- {m.user.first_name} ({m.user.id})")
            return admins

        admins, err = await run_with_bot(name, do_getstaff, target=target, chat_id=target)
        if err:
            await message.reply(err)
        else:
            if admins:
                await message.reply("👥 Daftar Admin:\n" + "\n".join(admins))
            else:
                await message.reply("❌ Tidak ada admin ditemukan.")
        del user_states[uid]

# ==========================
# Run with logging
# ==========================
def handle_exit(botname):
    print(f"\n⚠️ Bot {botname} diberhentikan.")
    sys.exit(0)

if __name__ == "__main__":
    async def startup():
        async with app:
            me = await app.get_me()
            print(f"✅ Bot {me.first_name} (@{me.username}) telah dijalankan.")
        app.run()

    # Tangani CTRL+C
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: handle_exit("iseng"))
    startup()
