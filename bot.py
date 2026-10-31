import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ========== تنظیمات ==========
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_ID = 123456789  # آیدی عددی ادمین در تلگرام

DATA_FILE = "prices.json"

# ========== دیتای پیش‌فرض ==========
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

# ========== مراحل مکالمه ==========
SELECT_TYPE, SELECT_COFFEE, ENTER_GRAMS = range(3)
ADMIN_SELECT_TYPE, ADMIN_SELECT_COFFEE, ADMIN_ENTER_PRICE = range(3, 6)

# ========== توابع دیتا ==========
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    save_data(DEFAULT_DATA)
    return DEFAULT_DATA

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========== منوی اصلی ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("☕ مشاهده قیمت قهوه‌ها", callback_data="show_types")],
        [InlineKeyboardButton("🧮 محاسبه قیمت بر اساس گرم", callback_data="calc_grams")],
    ]
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ ویرایش قیمت‌ها (ادمین)", callback_data="admin_edit")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "☕📚 *به ربات قهوه و کتاب خوش آمدید!*\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)

# ========== نمایش انواع قهوه ==========
async def show_types(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    keyboard = []
    for t in data:
        keyboard.append([InlineKeyboardButton(f"☕ {t}", callback_data=f"type_{t}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
    await query.edit_message_text(
        "نوع قهوه را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========== نمایش قهوه‌های هر دسته ==========
async def show_coffees(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coffee_type = query.data.replace("type_", "")
    data = load_data()
    coffees = data.get(coffee_type, {})

    text = f"☕ *قهوه‌های {coffee_type}*\n\n"
    keyboard = []
    for name, price in coffees.items():
        price_formatted = f"{price:,}"
        text += f"• *{name}*: {price_formatted} تومان / کیلوگرم\n"
        keyboard.append([InlineKeyboardButton(f"🧮 محاسبه گرم — {name}", callback_data=f"calc_{coffee_type}_{name}")])

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="show_types")])
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# ========== محاسبه بر اساس گرم ==========
async def calc_grams_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    keyboard = []
    for t in data:
        keyboard.append([InlineKeyboardButton(f"☕ {t}", callback_data=f"calctype_{t}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
    await query.edit_message_text("برای محاسبه، ابتدا نوع قهوه را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

async def calc_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coffee_type = query.data.replace("calctype_", "")
    data = load_data()
    coffees = data.get(coffee_type, {})
    keyboard = []
    for name in coffees:
        keyboard.append([InlineKeyboardButton(name, callback_data=f"calc_{coffee_type}_{name}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="calc_grams")])
    context.user_data["calc_type"] = coffee_type
    await query.edit_message_text("نوع قهوه را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

async def calc_select_coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.replace("calc_", "").split("_", 1)
    coffee_type = parts[0]
    coffee_name = parts[1]
    context.user_data["selected_type"] = coffee_type
    context.user_data["selected_coffee"] = coffee_name
    data = load_data()
    price_per_kg = data[coffee_type][coffee_name]
    context.user_data["price_per_kg"] = price_per_kg

    await query.edit_message_text(
        f"☕ *{coffee_name}* ({coffee_type})\n"
        f"قیمت هر کیلو: *{price_per_kg:,}* تومان\n\n"
        f"چند گرم می‌خواهید؟ (عدد را به فارسی یا انگلیسی وارد کنید)\n"
        f"مثال: 250 یا 500",
        parse_mode="Markdown"
    )
    return ENTER_GRAMS

async def receive_grams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    # تبدیل اعداد فارسی به انگلیسی
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    for i, d in enumerate(persian_digits):
        text = text.replace(d, str(i))

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
        [InlineKeyboardButton("🔄 محاسبه مجدد", callback_data=f"calc_{coffee_type}_{coffee_name}")],
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

# ========== پنل ادمین ==========
async def admin_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ شما ادمین نیستید!", show_alert=True)
        return

    data = load_data()
    keyboard = []
    for t in data:
        keyboard.append([InlineKeyboardButton(f"☕ {t}", callback_data=f"admtype_{t}")])
    keyboard.append([InlineKeyboardButton("➕ افزودن قهوه جدید", callback_data="admin_add")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
    await query.edit_message_text("⚙️ *پنل ادمین*\nکدام دسته را ویرایش کنید؟", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coffee_type = query.data.replace("admtype_", "")
    context.user_data["admin_type"] = coffee_type
    data = load_data()
    coffees = data.get(coffee_type, {})
    keyboard = []
    for name, price in coffees.items():
        keyboard.append([InlineKeyboardButton(f"{name} — {price:,} ت", callback_data=f"admedit_{coffee_type}_{name}")])
    keyboard.append([InlineKeyboardButton("🗑 حذف یک قهوه", callback_data=f"admdelete_{coffee_type}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_edit")])
    await query.edit_message_text(f"☕ *{coffee_type}*\nکدام قهوه را ویرایش کنید؟", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_edit_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    raw = query.data.replace("admedit_", "")
    parts = raw.split("_", 1)
    coffee_type = parts[0]
    coffee_name = parts[1]
    context.user_data["admin_type"] = coffee_type
    context.user_data["admin_coffee"] = coffee_name
    data = load_data()
    current = data[coffee_type][coffee_name]
    await query.edit_message_text(
        f"✏️ ویرایش قیمت: *{coffee_name}*\n"
        f"قیمت فعلی: *{current:,}* تومان\n\n"
        f"قیمت جدید را به تومان وارد کنید (فقط عدد):\n"
        f"مثال: 900000",
        parse_mode="Markdown"
    )
    return ADMIN_ENTER_PRICE

async def admin_receive_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    for i, d in enumerate(persian_digits):
        text = text.replace(d, str(i))
    text = text.replace(",", "").replace("،", "")

    try:
        price = int(text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ لطفاً یک عدد معتبر وارد کنید. مثال: 850000")
        return ADMIN_ENTER_PRICE

    coffee_type = context.user_data.get("admin_type")
    coffee_name = context.user_data.get("admin_coffee")
    data = load_data()
    data[coffee_type][coffee_name] = price
    save_data(data)

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_edit")]]
    await update.message.reply_text(
        f"✅ قیمت *{coffee_name}* به *{price:,}* تومان بروزرسانی شد!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def admin_add_coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    keyboard = []
    for t in data:
        keyboard.append([InlineKeyboardButton(f"☕ {t}", callback_data=f"addto_{t}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_edit")])
    await query.edit_message_text("به کدام دسته قهوه اضافه شود؟", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_add_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coffee_type = query.data.replace("addto_", "")
    context.user_data["add_type"] = coffee_type
    context.user_data["add_step"] = "name"
    await query.edit_message_text(
        f"➕ افزودن قهوه جدید به دسته *{coffee_type}*\n\nنام قهوه را وارد کنید:",
        parse_mode="Markdown"
    )
    return ADMIN_ENTER_PRICE + 1  # مرحله ورود نام

async def admin_receive_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["add_name"] = name
    context.user_data["add_step"] = "price"
    await update.message.reply_text(f"قیمت هر کیلوگرم *{name}* را به تومان وارد کنید:", parse_mode="Markdown")
    return ADMIN_ENTER_PRICE + 2

async def admin_receive_new_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    for i, d in enumerate(persian_digits):
        text = text.replace(d, str(i))
    text = text.replace(",", "").replace("،", "")
    try:
        price = int(text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ عدد معتبر وارد کنید:")
        return ADMIN_ENTER_PRICE + 2

    coffee_type = context.user_data.get("add_type")
    coffee_name = context.user_data.get("add_name")
    data = load_data()
    data[coffee_type][coffee_name] = price
    save_data(data)
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_edit")]]
    await update.message.reply_text(
        f"✅ قهوه *{coffee_name}* با قیمت *{price:,}* تومان به دسته *{coffee_type}* اضافه شد!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def admin_delete_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coffee_type = query.data.replace("admdelete_", "")
    context.user_data["delete_type"] = coffee_type
    data = load_data()
    keyboard = []
    for name in data.get(coffee_type, {}):
        keyboard.append([InlineKeyboardButton(f"🗑 {name}", callback_data=f"confirmdelete_{coffee_type}_{name}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"admtype_{coffee_type}")])
    await query.edit_message_text("کدام قهوه حذف شود؟", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    raw = query.data.replace("confirmdelete_", "")
    parts = raw.split("_", 1)
    coffee_type = parts[0]
    coffee_name = parts[1]
    data = load_data()
    if coffee_name in data.get(coffee_type, {}):
        del data[coffee_type][coffee_name]
        save_data(data)
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_edit")]]
    await query.edit_message_text(
        f"✅ قهوه *{coffee_name}* از دسته *{coffee_type}* حذف شد.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد. برای شروع مجدد /start را بزنید.")
    return ConversationHandler.END

# ========== اجرای ربات ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # ConversationHandler برای محاسبه گرم
    calc_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(calc_select_coffee, pattern="^calc_")],
        states={
            ENTER_GRAMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_grams)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # ConversationHandler برای ادمین - ویرایش قیمت
    admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_edit_price, pattern="^admedit_")],
        states={
            ADMIN_ENTER_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # ConversationHandler برای ادمین - افزودن قهوه
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_add_select_type, pattern="^addto_")],
        states={
            ADMIN_ENTER_PRICE + 1: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_new_name)],
            ADMIN_ENTER_PRICE + 2: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_new_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(calc_conv)
    app.add_handler(admin_conv)
    app.add_handler(add_conv)
    app.add_handler(CallbackQueryHandler(show_types, pattern="^show_types$"))
    app.add_handler(CallbackQueryHandler(show_coffees, pattern="^type_"))
    app.add_handler(CallbackQueryHandler(calc_grams_menu, pattern="^calc_grams$"))
    app.add_handler(CallbackQueryHandler(calc_select_type, pattern="^calctype_"))
    app.add_handler(CallbackQueryHandler(admin_edit, pattern="^admin_edit$"))
    app.add_handler(CallbackQueryHandler(admin_select_type, pattern="^admtype_"))
    app.add_handler(CallbackQueryHandler(admin_add_coffee, pattern="^admin_add$"))
    app.add_handler(CallbackQueryHandler(admin_delete_select, pattern="^admdelete_"))
    app.add_handler(CallbackQueryHandler(admin_confirm_delete, pattern="^confirmdelete_"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$"))

    print("✅ ربات در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()
