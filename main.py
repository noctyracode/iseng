import asyncio
import os
import signal
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db import add_bot, remove_bot, get_bots, save_state, get_state, clear_state

API_ID = int(os.getenv("API_ID", "12345"))
API_HASH = os.getenv("API_HASH", "1234567890abcdef")
MAIN_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")

registered_clients = {}
main_client = Client("MainBot", api_id=API_ID, api_hash=API_HASH, bot_token=MAIN_BOT_TOKEN)


async def ensure_registered_clients():
    bots = get_bots()
    for bot in bots:
        token = bot["token"]
        if token not in registered_clients:
            client = Client(
                name=f"bot_{token[:8]}",
                bot_token=token,
                api_id=API_ID,
                api_hash=API_HASH,
                in_memory=True,
            )
            registered_clients[token] = client
            await client.start()


@main_client.on_message(filters.command("start"))
async def start_handler(client, message):
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("📋 Lihat Daftar Bot", callback_data="list_bots")]]
    )
    await message.reply_text("🤖 Bot Panel Aktif!\nPilih menu di bawah:", reply_markup=keyboard)


@main_client.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data

    if data == "list_bots":
        bots = get_bots()
        if not bots:
            await callback_query.message.edit_text("⚠️ Belum ada bot terdaftar.")
            return

        keyboard = []
        for bot in bots:
            token = bot["token"]
            try:
                c = Client(
                    name=f"temp_{token[:8]}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    bot_token=token,
                    in_memory=True,
                )
                await c.start()
                me = await c.get_me()
                await c.stop()
                bot_name = me.first_name
            except Exception as e:
                bot_name = f"❌ Error: {e}"

            keyboard.append(
                [InlineKeyboardButton(f"{bot_name}", callback_data=f"manage:{token}")]
            )

        await callback_query.message.edit_text("📋 Daftar Bot:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("manage:"):
        token = data.split(":")[1]
        keyboard = [
            [InlineKeyboardButton("🚫 Ban All", callback_data=f"banall:{token}")],
            [InlineKeyboardButton("📢 Kirim Pesan", callback_data=f"send:{token}")],
            [InlineKeyboardButton("👮 Cek Admin", callback_data=f"cekadmin:{token}")],
            [InlineKeyboardButton("👤 Get Staff", callback_data=f"getstaff:{token}")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="list_bots")],
        ]
        await callback_query.message.edit_text(f"⚙️ Kelola Bot Token: {token[:10]}...", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("send:"):
        token = data.split(":")[1]
        save_state(callback_query.from_user.id, {"action": "send", "token": token})
        await callback_query.message.edit_text("📨 Masukkan ID grup/channel tujuan:")


@main_client.on_message(filters.text & ~filters.command("start"))
async def text_handler(client, message):
    state = get_state(message.from_user.id)
    if not state:
        return

    action = state.get("action")
    token = state.get("token")

    if action == "send":
        if "step" not in state:
            state["chat_id"] = message.text.strip()
            state["step"] = "waiting_message"
            save_state(message.from_user.id, state)
            await message.reply_text("✍️ Silakan masukkan isi pesan yang ingin dikirim:")
        else:
            chat_id = state["chat_id"]
            text = message.text

            if token not in registered_clients:
                await message.reply_text("❌ Bot belum aktif.")
                clear_state(message.from_user.id)
                return

            try:
                client = registered_clients[token]
                await client.send_message(chat_id, text)
                await message.reply_text("✅ Pesan berhasil dikirim.")
            except Exception as e:
                await message.reply_text(f"❌ Gagal mengirim pesan: {e}")

            clear_state(message.from_user.id)


async def startup():
    await ensure_registered_clients()
    print(f"✅ Main bot {MAIN_BOT_TOKEN[:10]}... berhasil dijalankan.")


async def shutdown():
    print("🛑 Menutup semua bot...")
    for client in registered_clients.values():
        await client.stop()
    await main_client.stop()


def main():
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(shutdown()))
    loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(shutdown()))

    loop.run_until_complete(startup())
    main_client.run()


if __name__ == "__main__":
    main()
