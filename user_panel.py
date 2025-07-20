# user_panel.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from db import *
from config import DEPOSIT_CARD
from ai_client import generate_tattoo
from utils import check_channel_member

START, TATTOO_DESC, RESERVE_DATE, RESERVE_TIME, WAIT_RECEIPT = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text('welcome', "به ربات رزرو و طراحی تتو خوش آمدید!"))
    kb = [
        [KeyboardButton("طراحی طرح تتو")],
        [KeyboardButton("رزرو وقت تتو")],
        [KeyboardButton("مشاهده رزروهای من")]
    ]
    await update.message.reply_text("انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return START

async def user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "طراحی طرح تتو":
        await update.message.reply_text(get_text('ask_tattoo_desc', "لطفاً توضیحات طرح تتو را بنویسید:"))
        return TATTOO_DESC
    elif text == "رزرو وقت تتو":
        # عضویت اجباری
        is_member = await check_channel_member(context.bot, update.effective_user.id)
        if not is_member:
            await update.message.reply_text("لطفاً ابتدا در کانال عضو شوید و سپس مجدداً امتحان کنید.")
            return START
        dates = get_all_dates()
        kb = [[InlineKeyboardButton(date, callback_data=date)] for date in dates]
        await update.message.reply_text(get_text('choose_date', "تاریخ مد نظر را انتخاب کنید:"), reply_markup=InlineKeyboardMarkup(kb))
        return RESERVE_DATE
    elif text == "مشاهده رزروهای من":
        reserves = get_user_reserves(update.effective_user.id)
        if not reserves:
            await update.message.reply_text("رزروی ثبت نکرده‌اید.")
            return START
        out = ""
        for d, t, s in reserves:
            out += f"{d} - {t} [{s}]\n"
        await update.message.reply_text(out)
        return START

async def tattoo_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text
    await update.message.reply_text("در حال ساخت طرح ...")
    img_url = generate_tattoo(desc)
    if img_url:
        await update.message.reply_photo(img_url, caption=get_text('discount_msg', "اگر همین طرح رو تتو کنید ۱۰٪ تخفیف هم می‌گیرید!"))
    else:
        await update.message.reply_text("مشکلی پیش آمد، دوباره تلاش کنید.")
    return START

async def reserve_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    date = query.data
    context.user_data["reserve_date"] = date
    times = get_free_times(date)
    kb = [[InlineKeyboardButton(t, callback_data=t)] for t in times]
    await query.edit_message_text(get_text('choose_time', "ساعت مد نظر را انتخاب کنید:"), reply_markup=InlineKeyboardMarkup(kb))
    return RESERVE_TIME

async def reserve_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    date = context.user_data["reserve_date"]
    time = query.data
    lock_reserve_time(date, time, query.from_user.id)
    context.user_data["reserve_time"] = time
    await query.edit_message_text(get_text('send_deposit', f"برای رزرو، مبلغ بیعانه را به شماره کارت {DEPOSIT_CARD} واریز کنید و رسید را ارسال نمایید."))
    return WAIT_RECEIPT

async def wait_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    date = context.user_data["reserve_date"]
    time = context.user_data["reserve_time"]
    if not update.message.photo:
        await update.message.reply_text("لطفاً عکس رسید را ارسال کنید.")
        return WAIT_RECEIPT
    receipt_id = update.message.photo[-1].file_id
    # ارسال به ادمین‌ها
    for admin in get_admins():
        txt = f"درخواست رزرو\nتاریخ: {date}\nساعت: {time}\nکاربر: @{update.effective_user.username or user_id}\nایدی عددی: {user_id}"
        await context.bot.send_photo(admin, receipt_id, caption=txt, reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("تایید", callback_data=f"confirm_{date}_{time}_{user_id}"),
                InlineKeyboardButton("رد", callback_data=f"reject_{date}_{time}")
            ]
        ]))
    await update.message.reply_text(get_text('wait_admin', "در حال بررسی رسید توسط ادمین..."))
    return START

user_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start), MessageHandler(filters.Regex("^طراحی طرح تتو$|^رزرو وقت تتو$|^مشاهده رزروهای من$"), user_menu)],
    states={
        START: [MessageHandler(filters.Regex("^طراحی طرح تتو$|^رزرو وقت تتو$|^مشاهده رزروهای من$"), user_menu)],
        TATTOO_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, tattoo_desc)],
        RESERVE_DATE: [CallbackQueryHandler(reserve_date)],
        RESERVE_TIME: [CallbackQueryHandler(reserve_time)],
        WAIT_RECEIPT: [MessageHandler(filters.PHOTO, wait_receipt)],
    },
    fallbacks=[CommandHandler("cancel", start)]
)