import os
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from db import add_bot, remove_bot, get_bots, save_state, get_state, clear_state
from config import OWNER_ID, BOT_TOKEN, API_ID, API_HASH

# Load ENV
load_dotenv()

# Main Bot (utama dari .env)
main_bot = Client(
    "MainBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,
)

# Dictionary untuk menyimpan client bot yang didaftarkan
registered_bots = {}


# -------- Fungsi Utilitas -------- #
async def get_bot_username(bot_token: str) -> str:
    """Dapatkan username bot dari token"""
    try:
        api_id = int(API_ID)
        api_hash = API_HASH
        client = Client("temp", api_id=api_id, api_hash=api_hash, bot_token=bot_token, in_memory=True)
        await client.start()
        me = await client.get_me()
        username = me.username
        await client.stop()
        return username
    except Exception as e:
        return f"Invalid Token ({str(e)})"


async def ensure_registered_clients():
    """Pastikan semua bot terdaftar dibuatkan client-nya"""
    bots = get_bots()
    for token in bots:
        if token not in registered_bots:
            try:
                client = Client(
                    f"ubot_{token[:8]}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    bot_token=token,
                    in_memory=True,
                )
                await client.start()
                registered_bots[token] = client
            except Exception as e:
                print(f"Gagal start bot {token}: {e}")


# -------- Handler -------- #
@main_bot.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("➕ Add Bot", callback_data="add_bot"),
            InlineKeyboardButton("🗑 Hapus Bot", callback_data="hapus_bot"),
        ],
         [
            InlineKeyboardButton("📋 Lihat Daftar", callback_data="lihat_daftar")
        ]]
    )

    await message.reply_photo(
        "https://files.catbox.moe/dh73a7.jpg",
        caption="Selamat datang! Pilih menu di bawah.",
        reply_markup=keyboard
    )


@main_bot.on_callback_query()
async def callback_handler(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    # Add Bot (Owner only)
    if data == "add_bot":
        if user_id != OWNER_ID:
            return await callback.answer("Hanya Owner yang bisa menambahkan bot!", show_alert=True)
        save_state(user_id, "waiting_bot_token")
        await callback.message.reply("Silakan kirim Bot Token untuk didaftarkan.")

    # Hapus Bot
    elif data == "hapus_bot":
        bots = get_bots()
        if not bots:
            return await callback.message.reply("❌ Tidak ada bot terdaftar.")
        buttons = [[InlineKeyboardButton(await get_bot_username(token), callback_data=f"delbot_{token}")]
                   for token in bots]
        await callback.message.reply("Pilih bot untuk dihapus:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("delbot_"):
        token = data.split("_", 1)[1]
        remove_bot(token)
        if token in registered_bots:
            await registered_bots[token].stop()
            registered_bots.pop(token)
        await callback.message.reply(f"✅ Bot berhasil dihapus.")

    # Lihat Daftar Bot
    elif data == "lihat_daftar":
        bots = get_bots()
        if not bots:
            return await callback.message.reply("❌ Belum ada bot yang terdaftar.")
        buttons = [[InlineKeyboardButton(await get_bot_username(token), callback_data=f"botmenu_{token}")]
                   for token in bots]
        await callback.message.reply("📋 Daftar Bot:", reply_markup=InlineKeyboardMarkup(buttons))

    # Menu Bot (banall, cekadmin, getstaff, sendmsg)
    elif data.startswith("botmenu_"):
        token = data.split("_", 1)[1]
        buttons = [
            [InlineKeyboardButton("⛔ Banall", callback_data=f"banall_{token}")],
            [InlineKeyboardButton("🛡 Cek Admin", callback_data=f"cekadmin_{token}")],
            [InlineKeyboardButton("👥 Get Staff", callback_data=f"getstaff_{token}")],
            [InlineKeyboardButton("✉️ Send", callback_data=f"sendmsg_{token}")]
        ]
        await callback.message.reply("Pilih aksi:", reply_markup=InlineKeyboardMarkup(buttons))

    # Banall
    elif data.startswith("banall_"):
        token = data.split("_", 1)[1]
        save_state(user_id, f"banall_target_{token}")
        await callback.message.reply("Masukkan ID Grup/Channel target:")

    # Cek Admin
    elif data.startswith("cekadmin_"):
        token = data.split("_", 1)[1]
        save_state(user_id, f"cekadmin_{token}")
        await callback.message.reply("Masukkan ID Grup/Channel target:")

    # Get Staff
    elif data.startswith("getstaff_"):
        token = data.split("_", 1)[1]
        save_state(user_id, f"getstaff_{token}")
        await callback.message.reply("Masukkan ID Grup/Channel target:")

    # Send Msg
    elif data.startswith("sendmsg_"):
        token = data.split("_", 1)[1]
        save_state(user_id, f"sendmsg_target_{token}")
        await callback.message.reply("Masukkan ID Grup/Channel target:")


@main_bot.on_message(filters.private & ~filters.command("start"))
async def state_handler(client: Client, message: Message):
    user_id = message.from_user.id
    state = get_state(user_id)

    if not state:
        return

    # Tambah Bot Token
    if state == "waiting_bot_token":
        token = message.text.strip()
        add_bot(token)
        await ensure_registered_clients()
        clear_state(user_id)
        bot_name = await get_bot_username(token)
        return await message.reply(f"✅ Bot {bot_name} berhasil didaftarkan.")

    # Banall
    if state.startswith("banall_target_"):
        token = state.split("_", 2)[2]
        target = message.text.strip()
        clear_state(user_id)
        if token not in registered_bots:
            return await message.reply("❌ Bot tidak aktif.")
        ubot = registered_bots[token]
        try:
            members = ubot.get_chat_members(target)
            async for m in members:
                if m.user and not m.user.is_self:
                    try:
                        await ubot.ban_chat_member(target, m.user.id)
                    except Exception:
                        pass
            await message.reply("✅ Banned Telah Selesai.")
        except Exception as e:
            await message.reply(f"❌ Gagal: {e}")

    # Cek Admin
    elif state.startswith("cekadmin_"):
        token = state.split("_", 1)[1]
        target = message.text.strip()
        clear_state(user_id)
        if token not in registered_bots:
            return await message.reply("❌ Bot tidak aktif.")
        ubot = registered_bots[token]
        try:
            admins = await ubot.get_chat_members(target, filter=enums.ChatMembersFilter.ADMINISTRATORS)
            result = "\n".join([f"- {a.user.first_name} ({a.user.id})" for a in admins])
            await message.reply(f"🛡 Admin di {target}:\n{result}")
        except Exception as e:
            await message.reply(f"❌ Gagal: {e}")

    # Get Staff
    elif state.startswith("getstaff_"):
        token = state.split("_", 1)[1]
        target = message.text.strip()
        clear_state(user_id)
        if token not in registered_bots:
            return await message.reply("❌ Bot tidak aktif.")
        ubot = registered_bots[token]
        try:
            admins = await ubot.get_chat_members(target, filter=enums.ChatMembersFilter.ADMINISTRATORS)
            result = "\n".join([f"- {a.user.first_name} ({a.user.id})" for a in admins])
            await message.reply(f"👥 Staff di {target}:\n{result}")
        except Exception as e:
            await message.reply(f"❌ Gagal: {e}")

    # Send Message
    elif state.startswith("sendmsg_target_"):
        token = state.split("_", 2)[2]
        target = message.text.strip()
        save_state(user_id, f"sendmsg_content_{token}_{target}")
        await message.reply("Silakan kirim isi pesan yang ingin dikirim:")

    elif state.startswith("sendmsg_content_"):
        _, token, target = state.split("_", 2)
        text = message.text
        clear_state(user_id)
        if token not in registered_bots:
            return await message.reply("❌ Bot tidak aktif.")
        ubot = registered_bots[token]
        try:
            await ubot.send_message(target, text)
            await message.reply("✅ Pesan berhasil dikirim.")
        except Exception as e:
            await message.reply(f"❌ Gagal mengirim pesan: {e}")


# -------- Startup -------- #
async def startup():
    await ensure_registered_clients()
    me = await main_bot.get_me()
    print(f"✅ Bot utama {me.first_name} (@{me.username}) telah dijalankan.")


if __name__ == "__main__":
    async def runner():
        await main_bot.start()
        await startup()
        print("Bot berjalan. Tekan Ctrl+C untuk menghentikan.")
        await idle()
        await main_bot.stop()

    from pyrogram import idle
    asyncio.run(runner())
