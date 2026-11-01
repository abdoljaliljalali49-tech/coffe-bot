import os
import json
import asyncio
import logging
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "9092864819:AAGlDGgaCEo87nn42wW206C5_8kQZAIps10"
ADMIN_ID = 1066821685
WEBHOOK_URL = "https://coffe-bot-01lg.onrender.com"
PORT = int(os.environ.get("PORT", 10000))
DATA_FILE = "prices.json"

DEFAULT_DATA = {
    "عربیکا": {
        "اتیوپی یرگاچف": 850000,
        "کلمبیا سوپریمو": 780000,
        "کنیا AA": 920000
    },
    "ربوستا": {
        "ویتنام": 420000,
        "اوگاندا": 390000,
        "اندونزی": 450000
    },
    "هیت": {
        "اسپرسو رست": 600000,
        "فرنچ رست": 580000,
        "بلند رست": 560000
    }
}

ENTER_GRAMS = 0
ENTER_BUDGET = 1
ADMIN_ENTER_PRICE = 2
ADMIN_ADD_NAME = 3
ADMIN_ADD_PRICE = 4

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    save_data(DEFAULT_DATA)
    return DEFAULT_DATA

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def to_english_digits(text):
    persian = '۰۱۲۳۴۵۶۷۸۹'
    for i, d in enumerate(persian):
        text = text.replace(d, str(i))
    return text.replace(",", "").replace("،", "")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("☕ مشاهده قیمت قهوه‌ها", callback_data="show_types")],
        [InlineKeyboardButton("🧮 محاسبه قیمت", callback_data="calc_grams")],
    ]
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ پنل ادمین — ویرایش قیمت", callback_data="admin_edit")])
    text = "☕📚 *به ربات قهوه و کتاب خوش آمدید!*\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_types(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    keyboard = [[InlineKeyboardButton(f"☕ {t}", callback_data=f"type_{t}")] for t in data]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
    await query.edit_message_text("نوع قهوه را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_coffees(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coffee_type = query.data[5:]
    data = load_data()
    coffees = data.get(coffee_type, {})
    text = f"☕ *قهوه‌های {coffee_type}*\n\n"
    keyboard = []
    for name, price in coffees.items():
        text += f"• *{name}*: {price:,} تومان / کیلوگرم\n"
        keyboard.append([InlineKeyboardButton(f"🧮 محاسبه — {name}", callback_data=f"calc_{coffee_type}||{name}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="show_types")])
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def calc_grams_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    keyboard = [[InlineKeyboardButton(f"☕ {t}", callback_data=f"calctype_{t}")] for t in data]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
    await query.edit_message_text("ابتدا نوع قهوه را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

async def calc_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coffee_type = query.data[9:]
    data = load_data()
    keyboard = [[InlineKeyboardButton(name, callback_data=f"calc_{coffee_type}||{name}")] for name in data.get(coffee_type, {})]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="calc_grams")])
    await query.edit_message_text("نوع قهوه را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

async def calc_select_coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    raw = query.data[5:]
    coffee_type, coffee_name = raw.split("||")
    data = load_data()
    price_per_kg = data[coffee_type][coffee_name]
    context.user_data["selected_type"] = coffee_type
    context.user_data["selected_coffee"] = coffee_name
    context.user_data["price_per_kg"] = price_per_kg

    keyboard = [
        [InlineKeyboardButton("⚖️ گرم دارم، قیمت میخوام", callback_data=f"mode_grams")],
        [InlineKeyboardButton("💰 مبلغ دارم، گرم میخوام", callback_data=f"mode_budget")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="calc_grams")]
    ]
    await query.edit_message_text(
        f"☕ *{coffee_name}*  |  {coffee_type}\n"
        f"💵 قیمت هر کیلو: *{price_per_kg:,}* تومان\n\n"
        f"چه نوع محاسبه‌ای میخواید؟",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def mode_grams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coffee_name = context.user_data.get("selected_coffee", "")
    price_per_kg = context.user_data.get("price_per_kg", 0)
    await query.edit_message_text(
        f"☕ *{coffee_name}*\n"
        f"💵 قیمت هر کیلو: *{price_per_kg:,}* تومان\n\n"
        f"⚖️ چند گرم میخواید؟\n"
        f"مثال: 250 یا 500",
        parse_mode="Markdown"
    )
    return ENTER_GRAMS

async def mode_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coffee_name = context.user_data.get("selected_coffee", "")
    price_per_kg = context.user_data.get("price_per_kg", 0)
    await query.edit_message_text(
        f"☕ *{coffee_name}*\n"
        f"💵 قیمت هر کیلو: *{price_per_kg:,}* تومان\n\n"
        f"💰 چقدر بودجه دارید؟ (تومان)\n"
        f"مثال: 100000 یا 250000",
        parse_mode="Markdown"
    )
    return ENTER_BUDGET

async def receive_grams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = to_english_digits(update.message.text.strip())
    try:
        grams = float(text)
        if grams <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ لطفاً یک عدد معتبر وارد کنید. مثال: 250")
        return ENTER_GRAMS

    price_per_kg = context.user_data.get("price_per_kg", 0)
    coffee_name = context.user_data.get("selected_coffee", "")
    coffee_type = context.user_data.get("selected_type", "")
    price = (price_per_kg / 1000) * grams

    keyboard = [
        [InlineKeyboardButton("🔄 محاسبه مجدد", callback_data=f"calc_{coffee_type}||{coffee_name}")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="back_main")]
    ]
    await update.message.reply_text(
        f"🧮 *نتیجه محاسبه*\n\n"
        f"☕ قهوه: *{coffee_name}* ({coffee_type})\n"
        f"⚖️ مقدار: *{grams:g}* گرم\n"
        f"💰 قیمت: *{price:,.0f}* تومان",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def receive_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = to_english_digits(update.message.text.strip())
    try:
        budget = float(text)
        if budget <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ لطفاً یک مبلغ معتبر وارد کنید. مثال: 100000")
        return ENTER_BUDGET

    price_per_kg = context.user_data.get("price_per_kg", 0)
    coffee_name = context.user_data.get("selected_coffee", "")
    coffee_type = context.user_data.get("selected_type", "")
    grams = (budget / price_per_kg) * 1000

    keyboard = [
        [InlineKeyboardButton("🔄 محاسبه مجدد", callback_data=f"calc_{coffee_type}||{coffee_name}")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="back_main")]
    ]
    await update.message.reply_text(
        f"🧮 *نتیجه محاسبه*\n\n"
        f"☕ قهوه: *{coffee_name}* ({coffee_type})\n"
        f"💰 مبلغ: *{budget:,.0f}* تومان\n"
        f"⚖️ مقدار قهوه: *{grams:,.0f}* گرم",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def admin_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ دسترسی ندارید!", show_alert=True)
        return
    data = load_data()
    keyboard = [[InlineKeyboardButton(f"☕ {t}", callback_data=f"admtype_{t}")] for t in data]
    keyboard.append([InlineKeyboardButton("➕ افزودن قهوه جدید", callback_data="admin_add")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
    await query.edit_message_text("⚙️ *پنل ادمین*\nکدام دسته را ویرایش کنید؟", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coffee_type = query.data[8:]
    context.user_data["admin_type"] = coffee_type
    data = load_data()
    keyboard = []
    for name, price in data.get(coffee_type, {}).items():
        keyboard.append([InlineKeyboardButton(f"✏️ {name} — {price:,} ت", callback_data=f"admedit_{coffee_type}||{name}")])
    keyboard.append([InlineKeyboardButton(f"🗑 حذف از {coffee_type}", callback_data=f"admdelete_{coffee_type}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_edit")])
    await query.edit_message_text(f"☕ *{coffee_type}*\nکدام قهوه را ویرایش کنید؟", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_edit_price_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    raw = query.data[8:]
    coffee_type, coffee_name = raw.split("||")
    context.user_data["admin_type"] = coffee_type
    context.user_data["admin_coffee"] = coffee_name
    data = load_data()
    current = data[coffee_type][coffee_name]
    await query.edit_message_text(
        f"✏️ ویرایش: *{coffee_name}*\nقیمت فعلی: *{current:,}* تومان\n\nقیمت جدید را وارد کنید (فقط عدد):\nمثال: 900000",
        parse_mode="Markdown"
    )
    return ADMIN_ENTER_PRICE

async def admin_receive_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = to_english_digits(update.message.text.strip())
    try:
        price = int(text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ عدد معتبر وارد کنید. مثال: 850000")
        return ADMIN_ENTER_PRICE
    coffee_type = context.user_data.get("admin_type")
    coffee_name = context.user_data.get("admin_coffee")
    data = load_data()
    data[coffee_type][coffee_name] = price
    save_data(data)
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_edit")]]
    await update.message.reply_text(
        f"✅ قیمت *{coffee_name}* به *{price:,}* تومان بروزرسانی شد!",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def admin_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    keyboard = [[InlineKeyboardButton(f"☕ {t}", callback_data=f"addto_{t}")] for t in data]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_edit")])
    await query.edit_message_text("به کدام دسته قهوه اضافه شود؟", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_add_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coffee_type = query.data[6:]
    context.user_data["add_type"] = coffee_type
    await query.edit_message_text(
        f"➕ افزودن به *{coffee_type}*\n\nنام قهوه جدید را وارد کنید:",
        parse_mode="Markdown"
    )
    return ADMIN_ADD_NAME

async def admin_receive_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["add_name"] = name
    await update.message.reply_text(f"قیمت هر کیلوگرم *{name}* را وارد کنید:\nمثال: 800000", parse_mode="Markdown")
    return ADMIN_ADD_PRICE

async def admin_receive_new_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = to_english_digits(update.message.text.strip())
    try:
        price = int(text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ عدد معتبر وارد کنید:")
        return ADMIN_ADD_PRICE
    coffee_type = context.user_data.get("add_type")
    coffee_name = context.user_data.get("add_name")
    data = load_data()
    data[coffee_type][coffee_name] = price
    save_data(data)
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_edit")]]
    await update.message.reply_text(
        f"✅ *{coffee_name}* با قیمت *{price:,}* تومان به *{coffee_type}* اضافه شد!",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def admin_delete_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coffee_type = query.data[11:]
    data = load_data()
    keyboard = [[InlineKeyboardButton(f"🗑 {name}", callback_data=f"confirmdelete_{coffee_type}||{name}")] for name in data.get(coffee_type, {})]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"admtype_{coffee_type}")])
    await query.edit_message_text("کدام قهوه حذف شود؟", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    raw = query.data[14:]
    coffee_type, coffee_name = raw.split("||")
    data = load_data()
    if coffee_name in data.get(coffee_type, {}):
        del data[coffee_type][coffee_name]
        save_data(data)
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_edit")]]
    await query.edit_message_text(
        f"✅ قهوه *{coffee_name}* حذف شد.", parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد. برای شروع مجدد /start بزنید.")
    return ConversationHandler.END

def build_app():
    app = Application.builder().token(BOT_TOKEN).build()

    calc_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(calc_select_coffee, pattern="^calc_")],
        states={
            ENTER_GRAMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_grams)],
            ENTER_BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_budget)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    mode_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(mode_grams, pattern="^mode_grams$"),
            CallbackQueryHandler(mode_budget, pattern="^mode_budget$"),
        ],
        states={
            ENTER_GRAMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_grams)],
            ENTER_BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_budget)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    admin_edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_edit_price_start, pattern="^admedit_")],
        states={ADMIN_ENTER_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_price)]},
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
    admin_add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_add_select_type, pattern="^addto_")],
        states={
            ADMIN_ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_new_name)],
            ADMIN_ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_new_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(calc_conv)
    app.add_handler(mode_conv)
    app.add_handler(admin_edit_conv)
    app.add_handler(admin_add_conv)
    app.add_handler(CallbackQueryHandler(show_types, pattern="^show_types$"))
    app.add_handler(CallbackQueryHandler(show_coffees, pattern="^type_"))
    app.add_handler(CallbackQueryHandler(calc_grams_menu, pattern="^calc_grams$"))
    app.add_handler(CallbackQueryHandler(calc_select_type, pattern="^calctype_"))
    app.add_handler(CallbackQueryHandler(admin_edit, pattern="^admin_edit$"))
    app.add_handler(CallbackQueryHandler(admin_select_type, pattern="^admtype_"))
    app.add_handler(CallbackQueryHandler(admin_add_start, pattern="^admin_add$"))
    app.add_handler(CallbackQueryHandler(admin_delete_select, pattern="^admdelete_"))
    app.add_handler(CallbackQueryHandler(admin_confirm_delete, pattern="^confirmdelete_"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$"))
    return app

async def webhook_handler(request):
    tg_app = request.app["tg_app"]
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return web.Response(text="OK")

async def health(request):
    return web.Response(text="OK")

async def main():
    tg_app = build_app()
    await tg_app.initialize()
    await tg_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    await tg_app.start()

    web_app = web.Application()
    web_app["tg_app"] = tg_app
    web_app.router.add_post("/webhook", webhook_handler)
    web_app.router.add_get("/", health)

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logger.info(f"✅ ربات روی پورت {PORT} در حال اجراست...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
