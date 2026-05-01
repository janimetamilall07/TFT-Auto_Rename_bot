from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import TFTBOTS
import os
import asyncio


@Client.on_message(filters.private & filters.command("watermark"))
async def set_watermark(client, message: Message):
    user_id = message.from_user.id

    if len(message.command) < 2:
        current = await TFTBOTS.get_watermark_text(user_id)
        current_img = await TFTBOTS.get_watermark_image(user_id)
        text = "<b>🔲 Watermark Settings</b>\n\n"
        text += f"📝 <b>Text Watermark:</b> <code>{current or 'Not Set'}</code>\n"
        text += f"🖼️ <b>Image Watermark:</b> {'✅ Set' if current_img else '❌ Not Set'}\n\n"
        text += "<b>Commands:</b>\n"
        text += "➪ <code>/watermark YourText</code> - Text watermark set\n"
        text += "➪ /watermark_pos - Position set\n"
        text += "➪ /del_watermark - Delete watermark\n"
        text += "➪ /view_watermark - View watermark"
        return await message.reply_text(text, parse_mode="html")

    watermark_text = " ".join(message.command[1:])
    await TFTBOTS.set_watermark_text(user_id, watermark_text)
    await message.reply_text(
        f"✅ <b>Watermark Set!</b>\n📝 <code>{watermark_text}</code>",
        parse_mode="html"
    )


@Client.on_message(filters.private & filters.photo & filters.caption & filters.regex(r"^/setwatermarkimg"))
async def set_watermark_image(client, message: Message):
    user_id = message.from_user.id
    msg = await message.reply_text("⏳ Saving watermark image...")
    file_id = message.photo.file_id
    await TFTBOTS.set_watermark_image(user_id, file_id)
    await msg.edit("✅ <b>Image Watermark Set!</b>", parse_mode="html")


@Client.on_message(filters.private & filters.command("watermark_pos"))
async def watermark_position(client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("↖️ Top Left",     callback_data="wpos_top-left"),
            InlineKeyboardButton("↗️ Top Right",    callback_data="wpos_top-right"),
        ],
        [
            InlineKeyboardButton("↙️ Bottom Left",  callback_data="wpos_bottom-left"),
            InlineKeyboardButton("↘️ Bottom Right", callback_data="wpos_bottom-right"),
        ],
        [
            InlineKeyboardButton("⬛ Center", callback_data="wpos_center"),
        ]
    ])
    await message.reply_text("📍 <b>Select Position:</b>", reply_markup=keyboard, parse_mode="html")


@Client.on_callback_query(filters.regex(r"^wpos_"))
async def watermark_pos_callback(client, callback_query):
    user_id = callback_query.from_user.id
    position = callback_query.data.replace("wpos_", "")
    await TFTBOTS.set_watermark_position(user_id, position)
    await callback_query.message.edit_text(
        f"✅ <b>Position Set:</b> <code>{position}</code>", parse_mode="html"
    )


@Client.on_message(filters.private & filters.command("del_watermark"))
async def delete_watermark(client, message: Message):
    user_id = message.from_user.id
    await TFTBOTS.set_watermark_text(user_id, None)
    await TFTBOTS.set_watermark_image(user_id, None)
    await message.reply_text("🗑️ <b>Watermark Deleted!</b>", parse_mode="html")


@Client.on_message(filters.private & filters.command("view_watermark"))
async def view_watermark(client, message: Message):
    user_id = message.from_user.id
    text = await TFTBOTS.get_watermark_text(user_id)
    img  = await TFTBOTS.get_watermark_image(user_id)
    pos  = await TFTBOTS.get_watermark_position(user_id) or "bottom-right"
    reply = "<b>🔲 Your Watermark:</b>\n\n"
    reply += f"📝 <b>Text:</b> <code>{text or 'Not Set'}</code>\n"
    reply += f"🖼️ <b>Image:</b> {'✅ Set' if img else '❌ Not Set'}\n"
    reply += f"📍 <b>Position:</b> <code>{pos}</code>"
    await message.reply_text(reply, parse_mode="html")


async def apply_watermark(client, user_id, input_path, output_path, progress_msg):
    watermark_text = await TFTBOTS.get_watermark_text(user_id)
    watermark_img  = await TFTBOTS.get_watermark_image(user_id)
    position       = await TFTBOTS.get_watermark_position(user_id) or "bottom-right"

    if not watermark_text and not watermark_img:
        return input_path

    await progress_msg.edit("💧 <b>Adding Watermark...</b>", parse_mode="html")

    pos_map = {
        "top-left":     "x=20:y=20",
        "top-right":    "x=W-w-20:y=20",
        "bottom-left":  "x=20:y=H-h-20",
        "bottom-right": "x=W-w-20:y=H-h-20",
        "center":       "x=(W-w)/2:y=(H-h)/2",
    }
    pos_str = pos_map.get(position, "x=W-w-20:y=H-h-20")
    os.makedirs("Watermark", exist_ok=True)

    if watermark_img:
        wm_img_path = f"Watermark/wm_{user_id}.png"
        try:
            await client.download_media(watermark_img, file_name=wm_img_path)
        except Exception as e:
            await progress_msg.edit(f"❌ Watermark image download failed: {e}")
            return input_path
        cmd = (
            f'ffmpeg -y -i "{input_path}" -i "{wm_img_path}" '
            f'-filter_complex "[1][0]scale2ref=w=iw/5:h=ow/mdar[wm][base];'
            f'[base][wm]overlay={pos_str}" '
            f'-codec:a copy "{output_path}"'
        )
    else:
        safe_text = watermark_text.replace("'", r"\'").replace(":", r"\:")
        cmd = (
            f'ffmpeg -y -i "{input_path}" '
            f'-vf "drawtext=text=\'{safe_text}\':'
            f'fontcolor=white:fontsize=36:borderw=2:bordercolor=black@0.6:'
            f'alpha=0.8:{pos_str}" '
            f'-codec:a copy "{output_path}"'
        )

    try:
        process = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            await progress_msg.edit("✅ <b>Watermark Added!</b>", parse_mode="html")
            if watermark_img and os.path.exists(wm_img_path):
                os.remove(wm_img_path)
            return output_path
        else:
            await progress_msg.edit(f"❌ Watermark Error: {stderr.decode()[:200]}")
            return input_path
    except Exception as e:
        await progress_msg.edit(f"❌ Exception: {e}")
        return input_path
