import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ForceReply,
    CallbackQuery,
    Message,
    InputMediaPhoto,
)
from utils import verify_user, check_token
from utils import verify_user, check_token
from helper.database import TFTBOTS
from config import *
from plugins.queue import pending_tokens

# Start Command Handler
@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):
    if len(message.command) > 1:
        data = message.command[1]
        if data.split("-", 1)[0] == "verify":
            userid = data.split("-", 2)[1]
            token = data.split("-", 3)[2]
            if str(message.from_user.id) != str(userid):
                return await message.reply_text(
                    text="<b>Invalid link or Expired link !</b>",
                    protect_content=True
                )
            is_valid = await check_token(client, userid, token)
            if is_valid:
                await message.reply_text(
                    text=f"<b>Hey {message.from_user.mention}, You are successfully verified !\n\nNow you have unlimited access for all files For 1Hour.</b>",
                    protect_content=True
                )
                if userid in pending_tokens:
                    del pending_tokens[userid]
                await verify_user(client, userid, token)
            else:
                return await message.reply_text(
                    text="<b>Invalid link or Expired link !</b>",
                    protect_content=True
                )
                if userid in pending_tokens:
                    del pending_tokens[userid]
            return
    user = message.from_user
    await TFTBOTS.add_user(client, message)                
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton('🔊 Updates', url='https://t.me/jcodefixe'),
        InlineKeyboardButton('♻️ Sᴜᴩᴩᴏʀᴛ', url='https://t.me/jcodefixenet')],
        [InlineKeyboardButton('❤️‍🩹 About', callback_data='about'),
        InlineKeyboardButton('🛠️ Help', callback_data='help')],
        [InlineKeyboardButton("Close ❌", callback_data='close')]
    ])
    if Config.START_PIC:
        await message.reply_photo(Config.START_PIC, caption=Txt.START_TXT.format(user.mention), reply_markup=button)       
    else:
        await message.reply_text(text=Txt.START_TXT.format(user.mention), reply_markup=button, disable_web_page_preview=True)
   

@Client.on_callback_query()
async def cb_handler(bot:Client, query: CallbackQuery):
    data = query.data 
    if data == "start":
        await query.message.edit_text(
            text=Txt.START_TXT.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton('🔊 Updates', url='https://t.me/jcodefixe'),
                InlineKeyboardButton('♻️ Sᴜᴩᴩᴏʀᴛ', url='https://t.me/jcodefixenet')],
                [InlineKeyboardButton('❤️‍🩹 About', callback_data='about'),
                InlineKeyboardButton('🛠️ Help', callback_data='help')],
                [InlineKeyboardButton("❌ Close", callback_data='close')]
            ])
        )
    elif data == "help":
        await query.message.edit_text(
            text=Txt.HELP_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⚡ Rename Bot", url="https://t.me/jcodefixenet")],
                [InlineKeyboardButton("🔒 Close", callback_data = "close"),
                InlineKeyboardButton("◀️ Back", callback_data = "start")]
            ])            
        )
    elif data == "about":
        await query.message.edit_text(
            text=Txt.ABOUT_TXT.format(bot.mention),
            disable_web_page_preview = True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 More Bots", url="https://t.me/jcodefixe")],
                [InlineKeyboardButton("🔒 Cʟᴏꜱᴇ", callback_data = "close"),
                InlineKeyboardButton("◀️ Bᴀᴄᴋ", callback_data = "start")]
            ])            
        )
    elif data == "close":
        try:
            await query.message.delete()
            await query.message.reply_to_message.delete()
            await query.message.continue_propagation()
        except:
            await query.message.delete()
            await query.message.continue_propagation()
