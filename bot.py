# -*- coding: utf-8 -*-

import logging
from threading import Thread
from flask import Flask

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from telegram import constants

# ================= CONFIG =================

BOT_TOKEN = "8495846696:AAGcbqhSBKjQbVQGLjaN2x3Wgwxl09qZkbo"

PHOTO_MAIN = "AgACAgUAAxkBAAM1aVaegv6Pszyh9ZvpftAxw9GaPFcAAhQLaxsxubhWSyRRVjsF2A8ACAEAAwIAA3kABx4E"
PHOTO_ABOUT = "AgACAgUAAxkBAAM5aVagPt-P0QYVBSF-iY8K_bB2C_IAAhgLaxsxubhW8ti1nJgvUJIACAEAAwIAA3kABx4E"

# =========================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ---------- FLASK WEB SERVER (RENDER SINGLE PORT) ----------

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Bot is running!", 200

def run_flask():
    flask_app.run(host="0.0.0.0")

# ---------- KEYBOARDS (REUSED) ----------

def start_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➥ 𝐀𝐁𝐎𝐔𝐓", callback_data="about")],
            [
                InlineKeyboardButton("➥ 𝗢𝗪𝗡𝗘𝗥", url="https://t.me/Akuma_Rei_Kami"),
                InlineKeyboardButton("➥ 𝐍𝐄𝐓𝐖𝐎𝐑𝐊", url="https://t.me/BotifyX_Pro")
            ],
            [InlineKeyboardButton("➥ 𝗖𝗟𝗢𝗦𝗘", callback_data="close_msg")]
        ]
    )

def about_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("➥ SUPPORT", url="https://t.me/BotifyX_support")
            ],
            [   InlineKeyboardButton("« BACK", callback_data="back_to_start"),
                InlineKeyboardButton("➥ CLOSE", callback_data="close_msg")
            ]
        ]
    )

# ---------- /START COMMAND ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = (
        "<code>WELCOME TO THE ADVANCED AUTO APPROVAL SYSTEM.\n"
        "WITH THIS BOT, YOU CAN MANAGE JOIN REQUESTS AND\n"
        "KEEP YOUR CHANNELS SECURE.</code>\n\n"
        "<blockquote><b>➥ MAINTAINED BY : "
        "<a href='https://t.me/Akuma_Rei_Kami'>Akuma_Rei</a>"
        "</b></blockquote>"
    )

    await update.message.reply_photo(
        photo=PHOTO_MAIN,
        caption=caption,
        reply_markup=start_keyboard(),
        parse_mode=constants.ParseMode.HTML
    )

# ---------- CALLBACK HANDLER ----------

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "close_msg":
        await query.message.delete()

    elif query.data == "about":
        about_text = (
            "<code>BOT INFORMATION AND STATISTICS</code>\n\n"
            "<blockquote expandable> <b>»» My Name :</b><a href='https://t.me/Seris_auto_approval_bot'>𝐒𝐄𝐑𝐈𝐒</a>\n"
            "<b>»» Developer :</b> @Akuma_Rei_Kami\n"
            "<b>»» Library :</b> <a href='https://docs.pyrogram.org/'>Pyrogram v2</a>\n"
            "<b>»» Language :</b> <a href='https://www.python.org/'>Python 3</a>\n"
            "<b>»» Database :</b> <a href='https://www.mongodb.com/docs/'>MongoDB</a>\n"
            "<b>»» Hosting :</b> <a href='https://render.com/'>Render</a>"
            "</blockquote>"
        )

        await query.edit_message_media(
            media=InputMediaPhoto(
                media=PHOTO_ABOUT,
                caption=about_text,
                parse_mode=constants.ParseMode.HTML
            ),
            reply_markup=about_keyboard()
        )

    elif query.data == "back_to_start":
        main_caption = (
            "<code>WELCOME TO THE ADVANCED AUTO APPROVAL SYSTEM.\n"
            "WITH THIS BOT, YOU CAN MANAGE JOIN REQUESTS AND\n"
            "KEEP YOUR CHANNELS SECURE.</code>\n\n"
            "<blockquote><b>➥ MAINTAINED BY : "
            "<a href='https://t.me/Akuma_Rei_Kami'>Akuma_Rei</a>"
            "</b></blockquote>"
        )

        await query.edit_message_media(
            media=InputMediaPhoto(
                media=PHOTO_MAIN,
                caption=main_caption,
                parse_mode=constants.ParseMode.HTML
            ),
            reply_markup=start_keyboard()
        )

# ---------- MAIN ----------

def main():
    Thread(target=run_flask).start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callbacks))

    print("Bot started successfully...")
    application.run_polling()

if __name__ == "__main__":
    main()



