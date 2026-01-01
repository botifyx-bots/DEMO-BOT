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

# =========================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ---------- FLASK WEB SERVER (Single Port) ----------

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Bot is running successfully!", 200

def run_flask():
    # Render automatically provides PORT
    flask_app.run(host="0.0.0.0")

# ---------- /START COMMAND ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➥ 𝐀𝐁𝐎𝐔𝐓", callback_data="about")],
        [
            InlineKeyboardButton("➥ 𝗢𝗪𝗡𝗘𝗥", url="https://t.me/Akuma_Rei_Kami"),
            InlineKeyboardButton("➥ 𝐍𝐄𝐓𝐖𝐎𝐑𝐊", url="https://t.me/+YM2e5j3C3pgzMmVl")
        ],
        [InlineKeyboardButton("➥ 𝗖𝗟𝗢𝗦𝗘", callback_data="close_msg")]
    ])

    caption = (
        "<b>WELCOME TO THE AUTO APPROVAL SYSTEM</b>\n\n"
        "<blockquote>"
        "This bot automatically approves join requests\n"
        "and manages access smoothly & securely.\n\n"
        "<b>Status:</b> Active ✅"
        "</blockquote>"
    )

    await update.message.reply_photo(
        photo=PHOTO_MAIN,
        caption=caption,
        reply_markup=keyboard,
        parse_mode=constants.ParseMode.HTML
    )

# ---------- CALLBACK HANDLER ----------

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "close_msg":
        await query.message.delete()

    elif query.data == "about":
        about_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➥ SUPPORT", url="https://t.me/BotifyX_support")],
            [
                InlineKeyboardButton("« BACK", callback_data="back_to_start"),
                InlineKeyboardButton("➥ CLOSE", callback_data="close_msg")
            ]
        ])

        about_text = (
            "<b>BOT INFORMATION</b>\n\n"
            "<blockquote>"
            "<b>» Developer :</b> @Akuma_Rei_Kami\n"
            "<b>» Library :</b> PTB v20+\n"
            "<b>» Database :</b> Local JSON\n"
            "</blockquote>"
        )

        await query.edit_message_media(
            media=InputMediaPhoto(
                media=PHOTO_MAIN,
                caption=about_text,
                parse_mode=constants.ParseMode.HTML
            ),
            reply_markup=about_keyboard
        )

    elif query.data == "back_to_start":
        main_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➥ 𝐀𝐁𝐎𝐔𝐓", callback_data="about")],
            [
                InlineKeyboardButton("➥ 𝗢𝗪𝗡𝗘𝗥", url="https://t.me/Akuma_Rei_Kami"),
                InlineKeyboardButton("➥ 𝐍𝐄𝐓𝐖𝐎𝐑𝐊", url="https://t.me/+YM2e5j3C3pgzMmVl")
            ],
            [InlineKeyboardButton("➥ 𝗖𝗟𝗢𝗦𝗘", callback_data="close_msg")]
        ])

        main_caption = (
            "<b>WELCOME TO THE AUTO APPROVAL SYSTEM</b>\n"
            "<code>Status: Active</code>"
        )

        await query.edit_message_media(
            media=InputMediaPhoto(
                media=PHOTO_MAIN,
                caption=main_caption,
                parse_mode=constants.ParseMode.HTML
            ),
            reply_markup=main_keyboard
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
