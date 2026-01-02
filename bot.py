# -*- coding: utf-8 -*-

import logging
import uuid
import asyncio
import os
from threading import Thread
from flask import Flask
from pymongo import MongoClient

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
    ContextTypes,
    MessageHandler,
    filters
)
from telegram.error import RetryAfter
from telegram import constants

# ================= CONFIG =================

BOT_TOKEN = "8495846696:AAHwUx4wktmUxtt4dpMJUff9tNPbyu6am4A"

PHOTO_MAIN = "AgACAgUAAxkBAAM1aVaegv6Pszyh9ZvpftAxw9GaPFcAAhQLaxsxubhWSyRRVjsF2A8ACAEAAwIAA3kABx4E"
PHOTO_ABOUT = "AgACAgUAAxkBAAM5aVagPt-P0QYVBSF-iY8K_bB2C_IAAhgLaxsxubhW8ti1nJgvUJIACAEAAwIAA3kABx4E"
RESTART_PHOTO_ID = "AgACAgUAAxkBAAM7aVajLkigiY4oCHYNgkaVqUfEB9MAAhsLaxsxubhWFWCpbMwqccwACAEAAwIAA3kABx4E"

OWNER_ID = 7156099919

# ---------- DATABASE ----------
MONGO_URI = "mongodb+srv://ANI_OTAKU:ANI_OTAKU@cluster0.t3frstc.mongodb.net/?appName=Cluster0"
DB_NAME = "ANI_OTAKU"

mongo = MongoClient(MONGO_URI)
db = mongo[DB_NAME]

users_col = db["users"]
restart_col = db["restart"]
ban_col = db["banned"]
mods_col = db["moderators"]

BAN_WAIT = set()
UNBAN_WAIT = set()
MOD_WAIT = set()
REVMOD_WAIT = set()

# =========================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ---------- FLASK WEB SERVER (FIXED) ----------

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---------- HELPERS ----------

def is_owner(uid: int) -> bool:
    return uid == OWNER_ID

def is_moderator(uid: int) -> bool:
    return mods_col.find_one({"_id": uid}) is not None

def has_permission(uid: int) -> bool:
    return is_owner(uid) or is_moderator(uid)

# ---------- KEYBOARDS ----------

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
            [InlineKeyboardButton("➥ SUPPORT", url="https://t.me/BotifyX_support")],
            [
                InlineKeyboardButton("« BACK", callback_data="back_to_start"),
                InlineKeyboardButton("➥ CLOSE", callback_data="close_msg")
            ]
        ]
    )

# ---------- /START ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users_col.update_one(
        {"_id": update.effective_user.id},
        {"$set": {"_id": update.effective_user.id}},
        upsert=True
    )

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
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=PHOTO_ABOUT,
                caption=(
                    "<code>BOT INFORMATION AND STATISTICS</code>\n\n"
                    "<blockquote expandable><b>»» My Name :</b>"
                    "<a href='https://t.me/Seris_auto_approval_bot'>𝐒𝐄𝐑𝐈𝐒</a>\n"
                    "<b>»» Developer :</b> @Akuma_Rei_Kami\n"
                    "<b>»» Library :</b> <a href='https://docs.pyrogram.org/'>Pyrogram v2</a>\n"
                    "<b>»» Language :</b> <a href='https://www.python.org/'>Python 3</a>\n"
                    "<b>»» Database :</b> <a href='https://www.mongodb.com/docs/'>MongoDB</a>\n"
                    "<b>»» Hosting :</b> <a href='https://render.com/'>Render</a>"
                    "</blockquote>"
                ),
                parse_mode=constants.ParseMode.HTML
            ),
            reply_markup=about_keyboard()
        )

    elif query.data == "back_to_start":
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=PHOTO_MAIN,
                caption=(
                    "<code>WELCOME TO THE ADVANCED AUTO APPROVAL SYSTEM.\n"
                    "WITH THIS BOT, YOU CAN MANAGE JOIN REQUESTS AND\n"
                    "KEEP YOUR CHANNELS SECURE.</code>\n\n"
                    "<blockquote><b>➥ MAINTAINED BY : "
                    "<a href='https://t.me/Akuma_Rei_Kami'>Akuma_Rei</a>"
                    "</b></blockquote>"
                ),
                parse_mode=constants.ParseMode.HTML
            ),
            reply_markup=start_keyboard()
        )

# ---------- RESTART BROADCAST ----------

async def broadcast_restart(application: Application):
    restart_id = uuid.uuid4().hex

    restart_col.update_one(
        {"_id": "last"},
        {"$set": {"rid": restart_id}},
        upsert=True
    )

    caption = (
        "<blockquote>"
        "🔄 <b>Bot Restarted Successfully!\n\n"
        "✅ Updates have been applied.\n"
        "🚀 Bot is now online and running smoothly.\n\n"
        "Thank you for your patience.</b>"
        "</blockquote>"
    )

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🆘 Support", url="https://t.me/BotifyX_support"),
                InlineKeyboardButton("📢 Update Channel", url="https://t.me/BotifyX_Pro")
            ]
        ]
    )

    for user in users_col.find({}):
        try:
            await application.bot.send_photo(
                chat_id=user["_id"],
                photo=RESTART_PHOTO_ID,
                caption=caption,
                reply_markup=buttons,
                parse_mode=constants.ParseMode.HTML
            )
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except:
            continue

# ---------- MAIN ----------

async def post_init(application: Application):
    await broadcast_restart(application)

def main():
    Thread(target=run_flask, daemon=True).start()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callbacks))

    application.run_polling()

if __name__ == "__main__":
    main()
