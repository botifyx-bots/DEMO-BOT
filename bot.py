# -*- coding: utf-8 -*-

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode

from flask import Flask
from threading import Thread

# ================= BOT CONFIG =================
API_ID = 27226524
API_HASH = "a14c9cd4629fde6b4d9b8c77df00fb00"
BOT_TOKEN = "8495846696:AAGcbqhSBKjQbVQGLjaN2x3Wgwxl09qZkbo"
# ============================================

PHOTO_MAIN = "AgACAgUAAxkBAAM1aVaegv6Pszyh9ZvpftAxw9GaPFcAAhQLaxsxubhWSyRRVjsF2A8ACAEAAwIAA3kABx4E"

bot = Client(
    "auto_approval_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= FLASK WEB SERVER =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_flask).start()
# ====================================================


# ================= /START COMMAND =================
@bot.on_message(filters.command("start"))
async def start_cmd(client, message):

    caption = (
        "<blockquote>"
        "<code>WELCOME TO THE ADVANCED AUTO APPROVAL SYSTEM.\n"
        "WITH THIS BOT, YOU CAN MANAGE JOIN REQUESTS AND\n"
        "KEEP YOUR CHANNELS SECURE.</code>\n\n"
        "<b>➥ MAINTAINED BY : "
        "<a href='https://t.me/Akuma_Rei_Kami'>Akuma_Rei</a>"
        "</b>"
        "</blockquote>"
    )

    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➥ 𝐀𝐁𝐎𝐔𝐓", callback_data="about")],
            [
                InlineKeyboardButton("➥ 𝗢𝗪𝗡𝗘𝗥", url="https://t.me/Akuma_Rei_Kami"),
                InlineKeyboardButton("➥ 𝐍𝐄𝐓𝐖𝐎𝐑𝐊", url="https://t.me/BotifyX_Pro")
            ],
            [InlineKeyboardButton("➥ 𝗖𝗟𝗢𝗦𝗘", callback_data="close_msg")]
        ]
    )

    await message.reply_photo(
        photo=PHOTO_MAIN,
        caption=caption,
        reply_markup=buttons,
        parse_mode=ParseMode.HTML,
        quote=True
    )
# ==================================================


bot.run()
