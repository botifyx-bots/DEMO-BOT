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
from telegram.ext import ChatJoinRequestHandler

# ================= CONFIG =================

BOT_TOKEN = "8495846696:AAHwUx4wktmUxtt4dpMJUff9tNPbyu6am4A"
PHOTO_MAIN = "AgACAgUAAxkBAAM1aVaegv6Pszyh9ZvpftAxw9GaPFcAAhQLaxsxubhWSyRRVjsF2A8ACAEAAwIAA3kABx4E"
PHOTO_ABOUT = "AgACAgUAAxkBAAM5aVagPt-P0QYVBSF-iY8K_bB2C_IAAhgLaxsxubhW8ti1nJgvUJIACAEAAwIAA3kABx4E"
RESTART_PHOTO_ID = "AgACAgUAAxkBAAM7aVajLkigiY4oCHYNgkaVqUfEB9MAAhsLaxsxubhWFWCpbMwqccwACAEAAwIAA3kABx4E"
FORCE_SUB_PHOTO = "AgACAgUAAxkBAAM9aVajnHmWrIUttpMzQRk7UfvoPswAAhwLaxsxubhWf70oZRL-qWoACAEAAwIAA3kABx4E"
OWNER_ID = 7156099919

# ---------- DATABASE ----------
FORCE_SUB_CHANNELS = [
    {"id": -1003538176254, "name": "Channel 1", "url": "https://t.me/BotifyX_Pro"},
    {"id": -1002733246601, "name": "Channel 2", "url": "https://t.me/ANI_MARK_NET"},
    {"id": -1002990773255, "name": "Channel 3", "url": "https://t.me/+tMr9UhqAWbxiMmRl"},
    {"id": -1003497399888, "name": "Channel 4", "url": "https://t.me/+66nB-xbC3MpkZjY1"},
    {"id": -1003117217377, "name": "Channel 5", "url": "https://t.me/NXTERA_INDEX"},
    {"id": -1003038993740, "name": "Channel 6", "url": "https://t.me/Animez_Edits"}
]
MONGO_URI = "mongodb+srv://ANI_OTAKU:ANI_OTAKU@cluster0.t3frstc.mongodb.net/?appName=Cluster0"
DB_NAME = "ANI_OTAKU"

mongo = MongoClient(MONGO_URI)
db = mongo[DB_NAME]

users_col = db["users"]
restart_col = db["restart"]
ban_col = db["banned"]
mods_col = db["moderators"]
links_col = db["links"]
batch_col = db["batches"]
settings_col = db["settings"]

BAN_WAIT = set()
UNBAN_WAIT = set()
MOD_WAIT = set()
REVMOD_WAIT = set()
GENLINK_WAIT = set()
BATCH_WAIT = {}

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

# ---------- FORCE SUB HELPERS ----------

async def is_user_joined(bot, user_id: int):
    for ch in FORCE_SUB_CHANNELS:
        try:
            member = await bot.get_chat_member(ch["id"], user_id)
            if member.status in ("left", "kicked"):
                return False
        except:
            return False
    return True

def force_sub_keyboard():
    buttons = []
    row = []
    for ch in FORCE_SUB_CHANNELS:
        row.append(InlineKeyboardButton(ch["name"], url=ch["url"]))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("‼️ CHECK JOIN", callback_data="check_fsub")])
    return InlineKeyboardMarkup(buttons)

async def force_sub_message(update):
    fsub_caption = (
        f"<blockquote><b>◈ Hᴇʏ  {update.effective_user.mention_html()} ×\n"
        "›› ʏᴏᴜʀ ғɪʟᴇ ɪs ʀᴇᴀᴅʏ ‼️  ʟᴏᴏᴋs ʟɪᴋᴇ ʏᴏᴜ ʜᴀᴠᴇɴ'ᴛ sᴜʙsᴄʀɪʙᴇᴅ "
        "ᴛᴏ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ʏᴇᴛ, sᴜʙsᴄʀɪʙᴇ ɴᴏᴡ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ғɪʟᴇs</b></blockquote>\n\n"
        "<blockquote><b>›› Pᴏᴡᴇʀᴇᴅ ʙʏ : @BotifyX_Pro</b></blockquote>"
    )

    await update.message.reply_photo(
        photo=FORCE_SUB_PHOTO,
        caption=fsub_caption,
        reply_markup=force_sub_keyboard(),
        parse_mode=constants.ParseMode.HTML
    )
    
# ---------- HELPERS ----------

def is_owner(uid: int) -> bool:
    return uid == OWNER_ID

def is_banned(uid: int) -> bool:
    return ban_col.find_one({"_id": uid}) is not None

def is_moderator(uid: int) -> bool:
    return mods_col.find_one({"_id": uid}) is not None

def has_permission(uid: int) -> bool:
    return is_owner(uid) or is_moderator(uid)

def get_auto_delete_seconds():
    data = settings_col.find_one({"_id": "auto_delete"})
    if not data:
        return None
    return data["minutes"] * 60

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
    # 🔒 BAN CHECK
    if is_banned(update.effective_user.id):
        return

    # 🔒 FORCE SUB CHECK
    if not await is_user_joined(context.bot, update.effective_user.id):
        await force_sub_message(update)
        return

    # 🔗 PAYLOAD HANDLING (/start <key>)
    if context.args:
        key = context.args[0]

        # ---------- BATCH PAYLOAD ----------
        if key.startswith("BATCH_"):
            batch = batch_col.find_one({"_id": key})
            if batch:
                for mid in range(batch["from_id"], batch["to_id"] + 1):
                    try:
                        await context.bot.copy_message(
                            chat_id=update.effective_chat.id,
                            from_chat_id=batch["chat_id"],
                            message_id=mid
                        )
                    except:
                        continue
                return

        # ---------- GENLINK PAYLOAD ----------
        data = links_col.find_one({"_id": key})
        if data:
            await context.bot.copy_message(
                chat_id=update.effective_chat.id,
                from_chat_id=data["chat_id"],
                message_id=data["message_id"]
            )
            return

    # 👤 SAVE USER
    users_col.update_one(
        {"_id": update.effective_user.id},
        {"$set": {"_id": update.effective_user.id}},
        upsert=True
    )

    # 👋 NORMAL START MESSAGE CONTINUES BELOW
    # (your existing start UI code)


    caption = (
        "<blockquote>WELCOME TO THE ADVANCED AUTO APPROVAL SYSTEM.\n"
        "WITH THIS BOT, YOU CAN MANAGE JOIN REQUESTS AND\n"
        "KEEP YOUR CHANNELS SECURE.</blockquote>\n\n"
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

# ---------- GENLINK ----------
async def genlink_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_banned(update.effective_user.id):
        return

    GENLINK_WAIT.add(update.effective_user.id)

    await update.message.reply_text(
        "<blockquote>Send A Message For To Get Your Shareable Link</blockquote>",
        parse_mode=constants.ParseMode.HTML
    )

# ---------- BATCH ----------
async def batch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_banned(update.effective_user.id):
        return

    BATCH_WAIT[update.effective_user.id] = {"step": "first"}

    await update.message.reply_text(
        "<blockquote>Forward The Batch First Message From your Batch Channel (With Forward Tag)..</blockquote>",
        parse_mode=constants.ParseMode.HTML
    )

# ---------- AUTO APPROVAL WITH FORCE-SUB ----------
async def auto_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    join = update.chat_join_request
    user = join.from_user
    chat = join.chat

    # 🔒 FORCE-SUB CHECK (REUSE EXISTING LOGIC)
    if not await is_user_joined(context.bot, user.id):
        try:
            # reuse SAME force-sub UI
            await context.bot.send_photo(
                chat_id=user.id,
                photo=FORCE_SUB_PHOTO,
                caption=(
                    f"<blockquote><b>◈ Hᴇʏ  {user.mention_html()} ×\n"
                    "›› ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴀʟʟ ʀᴇǫᴜɪʀᴇᴅ ᴄʜᴀɴɴᴇʟs "
                    "ʙᴇғᴏʀᴇ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ɪs ᴀᴘᴘʀᴏᴠᴇᴅ.</b></blockquote>\n\n"
                    "<blockquote><b>›› Pᴏᴡᴇʀᴇᴅ ʙʏ : @BotifyX_Pro</b></blockquote>"
                ),
                reply_markup=force_sub_keyboard(),
                parse_mode=constants.ParseMode.HTML
            )
        except:
            pass
        return  # ❌ DO NOT APPROVE

    # ✅ APPROVE ONLY AFTER FORCE-SUB
    await context.bot.approve_chat_join_request(
        chat_id=chat.id,
        user_id=user.id
    )

    # ✅ APPROVAL MESSAGE (YOUR FORMAT)
    approval_caption = (
        f"<blockquote>◈ Hᴇʏ {user.mention_html()} ×\n\n"
        f"›› ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {chat.title} "
        "ʜᴀs ʙᴇᴇɴ ᴀᴘᴘʀᴏᴠᴇᴅ.</blockquote>\n\n"
        "<blockquote>›› Pᴏᴡᴇʀᴇᴅ ʙʏ : "
        "<a href='https://t.me/Akuma_Rei_Kami'>Akuma Rei</a></blockquote>"
    )

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🆘 Support", url="https://t.me/BotifyX_support"),
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Akuma_Rei_Kami")
            ]
        ]
    )

    try:
        await context.bot.send_photo(
            chat_id=user.id,
            photo="AgACAgUAAxkBAAM3aVafIH9b2c4DDN5njA73ooObksUAAhULaxsxubhWDcTCfP-ZwHkACAEAAwIAA3kABx4E",
            caption=approval_caption,
            reply_markup=buttons,
            parse_mode=constants.ParseMode.HTML
        )
    except:
        pass
        
# ---------- SET AUTO DELETE ----------
async def setdel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "<blockquote>Usage: /setdel &lt;minutes&gt;</blockquote>",
            parse_mode=constants.ParseMode.HTML
        )
        return

    minutes = int(context.args[0])

    settings_col.update_one(
        {"_id": "auto_delete"},
        {"$set": {"minutes": minutes}},
        upsert=True
    )

    await update.message.reply_text(
        f"<blockquote>Auto delete time set to {minutes} minute(s)</blockquote>",
        parse_mode=constants.ParseMode.HTML
    )

# ---------- HELP ----------
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_banned(update.effective_user.id):
        return

    help_text = (
        "<code>🤖 BOT COMMANDS GUIDE</code>\n\n"
        "<blockquote expandable>"
        "➥ <b>/start</b> — Start the bot and access the main panel\n"
        "➥ <b>/genlink</b> — Generate a shareable link for any file/message\n"
        "➥ <b>/batch</b> — Generate a single link for multiple messages from a channel\n"
        "➥ <b>/broadcast</b> — Broadcast a message to all users (Owner only)\n"
        "➥ <b>/ban</b> — Ban a user from using the bot (Admin)\n"
        "➥ <b>/unban</b> — Unban a previously banned user (Admin)\n"
        "➥ <b>/moderator</b> — Add a moderator (Owner only)\n"
        "➥ <b>/revmoderator</b> — Remove a moderator (Owner only)\n"
        "➥ <b>/help</b> — Show this help menu</blockquote>\n\n"
        "<blockquote expandable><b>👑 Credits</b>\n"
        "This bot is developed and maintained by\n"
        "<b>@Akuma_Rei_Kami</b>\n\n"
        "<b>⚙️ Powered by</b>\n"
        "• Python\n"
        "• python-telegram-bot\n"
        "• MongoDB\n"
        "• Render Hosting"
        "</blockquote>"
    )

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🆘 Support", url="https://t.me/BotifyX_support"),
                InlineKeyboardButton("📢 Update Channel", url="https://t.me/BotifyX_Pro")
            ],
            [
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Akuma_Rei_Kami"),
                InlineKeyboardButton("➥ CLOSE", callback_data="close_msg")
            ]
        ]
    )

    await update.message.reply_photo(
        photo="AgACAgUAAxkBAAM_aVakMx1bndT59YFQKkS7alJEtu8AAh0LaxsxubhWEEYErV7ehKYACAEAAwIAA3kABx4E",
        caption=help_text,
        reply_markup=buttons,
        parse_mode=constants.ParseMode.HTML
    )
    
# ---------- BROADCAST (REPLY MODE) ----------
async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "<blockquote>Reply to a message to broadcast it</blockquote>",
            parse_mode=constants.ParseMode.HTML
        )
        return

    msg = update.message.reply_to_message

    total = users_col.count_documents({})
    success = 0
    blocked = 0
    deleted = 0
    failed = 0

    for user in users_col.find({}):
        try:
            await context.bot.copy_message(
                chat_id=user["_id"],
                from_chat_id=msg.chat.id,
                message_id=msg.message_id
            )
            success += 1

        except RetryAfter as e:
            await asyncio.sleep(e.retry_after)
            failed += 1

        except Exception as e:
            err = str(e).lower()
            if "blocked" in err:
                blocked += 1
            elif "deleted" in err:
                deleted += 1
            else:
                failed += 1

    report = (
        "<b>Broadcast completed</b>\n\n"
        f"◇ Total Users: {total}\n"
        f"◇ Successful: {success}\n"
        f"◇ Blocked Users: {blocked}\n"
        f"◇ Deleted Accounts: {deleted}\n"
        f"◇ Unsuccessful: {failed}"
    )

    await update.message.reply_text(
        report,
        parse_mode=constants.ParseMode.HTML
    )

# ---------- BAN / UNBAN ----------

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_permission(update.effective_user.id):
        return
    BAN_WAIT.add(update.effective_user.id)
    await update.message.reply_text("<blockquote>send the user id</blockquote>", parse_mode=constants.ParseMode.HTML)


async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not has_permission(update.effective_user.id):
        return
    UNBAN_WAIT.add(update.effective_user.id)
    await update.message.reply_text("<blockquote>send the user id</blockquote>", parse_mode=constants.ParseMode.HTML)


# ---------- MODERATOR SYSTEM (OWNER ONLY) ----------

async def moderator_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    MOD_WAIT.add(update.effective_user.id)
    await update.message.reply_text("<blockquote>send the user id</blockquote>", parse_mode=constants.ParseMode.HTML)


async def revmoderator_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    REVMOD_WAIT.add(update.effective_user.id)
    await update.message.reply_text("<blockquote>send the user id</blockquote>", parse_mode=constants.ParseMode.HTML)

# ---------- CALLBACK HANDLER ----------

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if is_banned(query.from_user.id):
        await query.answer("You are banned from using this bot.", show_alert=True)
        return
    query = update.callback_query
    await query.answer()

    if query.data == "check_fsub":
        if not await is_user_joined(context.bot, query.from_user.id):
            await query.answer(
                "Join all channels first!",
                show_alert=True
            )
            return

        await query.message.delete()
        await start(update, context)
        return


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
# ---------- PRIVATE HANDLER ----------
async def private_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_banned(update.effective_user.id):
        return

    if not update.message:
        return

    uid = update.effective_user.id
    text = update.message.text.strip() if update.message.text else ""

    if text.startswith("/"):
        return

    # ---------- BAN ----------
    if uid in BAN_WAIT:
        BAN_WAIT.remove(uid)
        ban_col.insert_one({"_id": int(text)})
        await update.message.reply_text(
            "<blockquote>✨ Successfully Banned the user</blockquote>",
            parse_mode=constants.ParseMode.HTML
        )
        return

    # ---------- UNBAN ----------
    if uid in UNBAN_WAIT:
        UNBAN_WAIT.remove(uid)
        ban_col.delete_one({"_id": int(text)})
        await update.message.reply_text(
            "<blockquote>✨ Successfully Unbanned the user</blockquote>",
            parse_mode=constants.ParseMode.HTML
        )
        return

    # ---------- ADD MODERATOR ----------
    if uid in MOD_WAIT:
        MOD_WAIT.remove(uid)
        mods_col.insert_one({"_id": int(text)})
        await update.message.reply_text(
            "<blockquote>👮 Successfully Added Moderator</blockquote>",
            parse_mode=constants.ParseMode.HTML
        )
        return

    # ---------- REMOVE MODERATOR ----------
    if uid in REVMOD_WAIT:
        REVMOD_WAIT.remove(uid)
        mods_col.delete_one({"_id": int(text)})
        await update.message.reply_text(
            "<blockquote>👮 Successfully Removed Moderator</blockquote>",
            parse_mode=constants.ParseMode.HTML
        )
        return

    # ---------- GENLINK PROCESS ----------
    if uid in GENLINK_WAIT:
        GENLINK_WAIT.remove(uid)

        msg = update.message
        key = uuid.uuid4().hex[:12]

        links_col.insert_one({
            "_id": key,
            "chat_id": msg.chat.id,
            "message_id": msg.message_id
        })

        link = f"https://t.me/ANI_UPLODE_BOT?start={key}"

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔗 Share", url=f"https://t.me/share/url?url={link}")]]
        )

        await msg.reply_text(
            f"Here is your link:\n\n{link}",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        return

    # ---------- BATCH PROCESS ----------
    if uid in BATCH_WAIT:
        data = BATCH_WAIT[uid]

        if data["step"] == "first":
            if not update.message.forward_from_chat:
                return

            data["chat_id"] = update.message.forward_from_chat.id
            data["from_id"] = update.message.forward_from_message_id
            data["step"] = "last"

            await update.message.reply_text(
                "<blockquote>Forward The Batch Last Message From Your Batch Channel (With Forward Tag)..</blockquote>",
                parse_mode=constants.ParseMode.HTML
            )
            return

        if data["step"] == "last":
            if not update.message.forward_from_chat:
                return

            to_id = update.message.forward_from_message_id
            batch_key = f"BATCH_{uuid.uuid4().hex[:12]}"

            batch_col.insert_one({
                "_id": batch_key,
                "chat_id": data["chat_id"],
                "from_id": data["from_id"],
                "to_id": to_id
            })

            del BATCH_WAIT[uid]

            link = f"https://t.me/ANI_UPLODE_BOT?start={batch_key}"

            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔗 Share", url=f"https://t.me/share/url?url={link}")]]
            )

            await update.message.reply_text(
                f"Here is your link:\n\n{link}",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            return

# ---------- RESTART BROADCAST ----------

async def broadcast_restart(application: Application):
    restart_id = uuid.uuid4().hex

    restart_col.update_one(
        {"_id": "last"},
        {"$set": {"rid": restart_id}},
        upsert=True
    )

    RE_caption = (
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
                caption=RE_caption,
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
    application.add_handler(CommandHandler("ban", ban_cmd))
    application.add_handler(CommandHandler("unban", unban_cmd))
    application.add_handler(CommandHandler("moderator", moderator_cmd))
    application.add_handler(CommandHandler("revmoderator", revmoderator_cmd))
    application.add_handler(CommandHandler("broadcast", broadcast_cmd))
    application.add_handler(CommandHandler("genlink", genlink_cmd))
    application.add_handler(CommandHandler("batch", batch_cmd))
    application.add_handler(CommandHandler("setdel", setdel_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(ChatJoinRequestHandler(auto_approve))


    application.add_handler(
    MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, private_handler)
)



    application.run_polling()

if __name__ == "__main__":
    main()










