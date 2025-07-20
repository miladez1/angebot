# admin_panel.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from db import *
from config import ADMINS, DEPOSIT_CARD

ADMIN_MAIN, EDIT_TIME, BROADCAST, EDIT_TEXT, EDIT_API = range(5)

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return
    kb = [
        [InlineKeyboardButton("مدیریت تاریخ/ساعت رزرو", callback_data="edit_time")],
        [InlineKeyboardButton("متن‌ها و دکمه‌ها", callback_data="edit_text")],
        [InlineKeyboardButton("تنظیم API هوش مصنوعی", callback_data="edit_api")],
        [InlineKeyboardButton("ارسال پیام همگانی", callback_data="broadcast")],
        [InlineKeyboardButton("برگشت به منوی اصلی", callback_data="cancel")]
    ]
    await update.message.reply_text("پنل مدیریت:", reply_markup=InlineKeyboardMarkup(kb))
    return ADMIN_MAIN

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "edit_time":
        await query.edit_message_text("تاریخ جدید (YYYY-MM-DD) را ارسال کنید:")
        return EDIT_TIME
    elif query.data == "broadcast":
        await query.edit_message_text("متن پیام همگانی را ارسال کنید:")
        return BROADCAST
    elif query.data == "edit_text":
        await query.edit_message_text("کلید متن (مثلاً welcome, ask_tattoo_desc) را ارسال کنید:")
        return EDIT_TEXT
    elif query.data == "edit_api":
        await query.edit_message_text("برای تنظیم API هوش مصنوعی، کلید و مقدار را با یک خط فاصله وارد کنید.\nمثال:\nAI_API_URL https://YOUR-URL")
        return EDIT_API
    elif query.data == "cancel":
        await query.edit_message_text("خروج از پنل مدیریت.")
        return ConversationHandler.END

async def admin_edit_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # اضافه کردن تاریخ/ساعت رزرو
    date = update.message.text.strip()
    context.user_data["admin_edit_date"] = date
    await update.message.reply_text("ساعت را به فرمت HH:MM ارسال کنید (مثلاً 15:30):")
    return EDIT_TIME+1

async def admin_edit_time2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date = context.user_data.get("admin_edit_date")
    time = update.message.text.strip()
    add_reserve_date_time(date, time)
    await update.message.reply_text("تاریخ و ساعت اضافه شد. مجدداً تاریخ جدید یا /cancel را ارسال کنید.")
    return EDIT_TIME

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # لیست همه کاربران را باید داشته باشید (مثلاً ذخیره کنید در دیتابیس در بخش ثبت‌نام)
    # اینجا فقط برای نمونه ارسال برای همه رزروکننده‌هاست
    users = set()
    for row in get_locked_reserves():
        users.add(row[3])
    for user_id in users:
        try:
            await context.bot.send_message(user_id, text)
        except Exception:
            pass
    await update.message.reply_text("پیام ارسال شد.")
    return ConversationHandler.END

async def admin_edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = update.message.text.strip()
    context.user_data["edit_text_key"] = key
    await update.message.reply_text(f"متن جدید برای {key} را وارد کنید:")
    return EDIT_TEXT+1

async def admin_edit_text2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = context.user_data["edit_text_key"]
    text = update.message.text
    set_text(key, text)
    await update.message.reply_text("متن ذخیره شد.")
    return ConversationHandler.END

async def admin_edit_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        k, v = update.message.text.split(" ", 1)
        set_ai_setting(k, v)
        await update.message.reply_text("تنظیم شد.")
    except Exception:
        await update.message.reply_text("فرمت اشتباه.")
    return ConversationHandler.END

admin_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("admin", admin_start)],
    states={
        ADMIN_MAIN: [CallbackQueryHandler(admin_callback)],
        EDIT_TIME: [MessageHandler(filters.TEXT, admin_edit_time)],
        EDIT_TIME+1: [MessageHandler(filters.TEXT, admin_edit_time2)],
        BROADCAST: [MessageHandler(filters.TEXT, admin_broadcast)],
        EDIT_TEXT: [MessageHandler(filters.TEXT, admin_edit_text)],
        EDIT_TEXT+1: [MessageHandler(filters.TEXT, admin_edit_text2)],
        EDIT_API: [MessageHandler(filters.TEXT, admin_edit_api)],
    },
    fallbacks=[CommandHandler("cancel", admin_start)],
)