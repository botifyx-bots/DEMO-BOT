# -*- coding: utf-8 -*-

import logging
import uuid
import asyncio
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
    ContextTypes,
    MessageHandler,
    filters
)
from telegram.error import RetryAfter
from telegram import constants

# ================= CONFIG =================

BOT_TOKEN = "8495846696:AAGcbqhSBKjQbVQGLjaN2x3Wgwxl09qZkbo"

PHOTO_MAIN = "AgACAgUAAxkBAAM1aVaegv6Pszyh9ZvpftAxw9GaPFcAAhQLaxsxubhWSyRRVjsF2A8ACAEAAwIAA3kABx4E"
PHOTO_ABOUT = "AgACAgUAAxkBAAM5aVagPt-P0QYVBSF-iY8K_bB2C_IAAhgLaxsxubhW8ti1nJgvUJIACAEAAwIAA3kABx4E"

RESTART_PHOTO_ID = "AgACAgUAAxkBAAM7aVajLkigiY4oCHYNgkaVqUfEB9MAAhsLaxsxubhWFWCpbMwqccwACAEAAwIAA3kABx4E"

restart_col = db["restart"]
ban_col = db["banned"]

OWNER_ID = 7156099919  # <-- PUT YOUR TELEGRAM ID HERE

BAN_WAIT = set()
UNBAN_WAIT = set()

# =========================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ---------- FLASK WEB SERVER (RENDER) ----------

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!", 200

def run_flask():
    app.run(host="0.0.0.0")

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
            [
                InlineKeyboardButton("➥ SUPPORT", url="https://t.me/BotifyX_support")
            ],
            [InlineKeyboardButton("« BACK", callback_data="back_to_start"),
             InlineKeyboardButton("➥ CLOSE", callback_data="close_msg")
            ]
        ]
    )

# ---------- /START ----------

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
            "<pre>BOT INFORMATION AND STATISTICS</pre>\n\n"
            "<blockquote><b>»» My Name :</b>"
            "<a href='https://t.me/MORVESSA_NIGHTMARE_BOT'>𝙈𝙊𝙍𝙑𝙀𝙎𝙎𝘼</a>\n"
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

# ---------- BAN ----------

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    BAN_WAIT.add(update.effective_user.id)
    await update.message.reply_text("send the user id")

# ---------- UNBAN ----------

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    UNBAN_WAIT.add(update.effective_user.id)
    await update.message.reply_text("send the user id")

# ---------- PRIVATE HANDLER ----------

async def private_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    uid = update.effective_user.id
    text = update.message.text.strip()

    if text.startswith("/"):
        return

    if uid in BAN_WAIT:
        BAN_WAIT.remove(uid)
        ban_col.insert_one({"_id": int(text)})

        await update.message.reply_text(
            "<blockquote>✨ Successfully Banned the user</blockquote>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("➥ CLOSE", callback_data="close_msg")]]
            ),
            parse_mode=constants.ParseMode.HTML
        )
        return

    if uid in UNBAN_WAIT:
        UNBAN_WAIT.remove(uid)
        ban_col.delete_one({"_id": int(text)})

        await update.message.reply_text(
            "<blockquote>✨ Successfully Unbanned the user</blockquote>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("➥ CLOSE", callback_data="close_msg")]]
            ),
            parse_mode=constants.ParseMode.HTML
        )
        return

# ---------- RESTART BROADCAST ----------

async def broadcast_restart(application: Application):
    restart_id = uuid.uuid4().hex

    last = restart_col.find_one({"_id": "last"})
    if last and last.get("rid") == restart_id:
        return

    restart_col.update_one(
        {"_id": "last"},
        {"$set": {"rid": restart_id}},
        upsert=True
    )

    caption = (
        "<blockquote>"
        "🔄 <code>Bot Restarted Successfully!</code>\n\n"
        "✅ <code>Updates have been applied.</code>\n"
        "🚀 <code>Bot is now online and running smoothly.</code>\n\n"
        "<code>Thank you for your patience.</code>"
        "</blockquote>"
    )

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📢 Update Channel", url="https://t.me/BotifyX_Pro"),
                InlineKeyboardButton("🆘 Support", url="https://t.me/BotifyX_support")
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
    Thread(target=run_flask).start()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ban", ban_cmd))
    application.add_handler(CommandHandler("unban", unban_cmd))
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    application.add_handler(MessageHandler(filters.TEXT & filters.PRIVATE, private_handler))

    print("Bot started successfully...")
    application.run_polling()

if __name__ == "__main__":
    main()
