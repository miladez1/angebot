# main.py

from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from db import init_db, get_admins, confirm_reserve, reject_reserve
from config import TOKEN, ADMINS
from admin_panel import admin_conv_handler
from user_panel import user_conv_handler
import asyncio

async def admin_photo_callback(update, context):
    query = update.callback_query
    data = query.data
    if data.startswith("confirm_"):
        _, date, time, user_id = data.split("_")
        photo = None
        # پیدا کردن عکس رسید (در عمل باید بهتر مدیریت شود)
        for msg in await context.bot.get_chat(update.effective_chat.id).get_history():
            if msg.photo and msg.from_user.id == int(user_id):
                photo = msg.photo[-1].file_id
                break
        confirm_reserve(date, time, int(user_id), photo)
        await query.edit_message_caption("رزرو تایید شد.")
        await context.bot.send_message(int(user_id), "رزرو شما تایید شد!")
    elif data.startswith("reject_"):
        _, date, time = data.split("_")
        reject_reserve(date, time)
        await query.edit_message_caption("رزرو رد شد.")
    else:
        await query.answer("نامعتبر")

def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(admin_conv_handler)
    app.add_handler(user_conv_handler)
    app.add_handler(CallbackQueryHandler(admin_photo_callback, pattern="^(confirm_|reject_)"))
    app.run_polling()

if __name__ == "__main__":
    main()