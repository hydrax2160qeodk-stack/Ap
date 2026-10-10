import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# ================= CONFIG =================
BOT_TOKEN = "8848201471:AAGHchewkhO2CI-_63R6CAJ7JsCjYFNd0lU" # Replace with your token
ADMIN_ID = 8170952537  
CHANNEL_LINK = "https://t.me/Rayyan_Hacks"
QR_IMAGE_URL = "https://kommodo.ai/i/qF4FLWL7wK3SjLsyNmH1"
SUPPORT_USERNAME = "@RayyanDevx"

# States
SENDING_KEY, ADMIN_MSG_USER, ADMIN_MSG_TEXT = range(3)

# ================= DATA (In-Memory) =================
# Note: Use SQLite/MongoDB for production
db = {
    "users": {}, # {user_id: {name: str, keys: [], balance: 0, refs: 0}}
    "stats": {"total_approved": 0, "total_rejected": 0, "keys_sold": 0}
}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= UTILS =================
def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("🛒 Buy Keys", callback_data="buy"), InlineKeyboardButton("🔑 My Keys", callback_data="mykeys")],
        [InlineKeyboardButton("🎁 Referral", callback_data="ref"), InlineKeyboardButton("📞 Support", callback_data="support")]
    ])

# ================= START HANDLER =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in db["users"]:
        db["users"][user.id] = {"name": user.first_name, "keys": [], "balance": 0, "refs": 0}

    welcome_text = (
        f"👋 *Welcome, {user.first_name}*\n\n"
        f"✨ *ROLEX X PREMIUM FEATURES*\n"
        f"╰ 🎯 180° Bullet Track\n"
        f"╰ 🪄 Magic Bullet High DMG\n"
        f"╰ ⚡ Ultra Aim Assist\n"
        f"╰ 💎 Smooth ESP (Internal)\n\n"
        f"🚀 *Status:* `Undetected` | *Server:* `Stable`"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

# ================= BUY FLOW =================
async def buy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("1 Day - ₹100", callback_data="p_1_100")],
        [InlineKeyboardButton("7 Days - ₹300", callback_data="p_7_300")],
        [InlineKeyboardButton("15 Days - ₹500", callback_data="p_15_500")],
        [InlineKeyboardButton("30 Days - ₹800", callback_data="p_30_800")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_start")]
    ]
    await query.message.edit_text("💎 *Select Your Membership:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def plan_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, days, price = query.data.split("_")
    context.user_data['temp_plan'] = {"days": days, "price": price}
    
    text = (
        f"🧾 *ORDER CONFIRMATION*\n\n"
        f"👤 *Client:* {query.from_user.first_name}\n"
        f"⏳ *Duration:* {days} Days\n"
        f"💰 *Total Amount:* ₹{price}\n\n"
        f"Click below to generate payment QR."
    )
    keyboard = [[InlineKeyboardButton("💳 Pay Now", callback_data="pay_now")], [InlineKeyboardButton("❌ Cancel", callback_data="buy")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def pay_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    plan = context.user_data.get('temp_plan')
    text = (
        f"✨ *PAYMENT GATEWAY*\n\n"
        f"👤 *User:* {query.from_user.first_name}\n"
        f"💰 *Amount:* ₹{plan['price']}\n\n"
        f"⚠️ *Step 1:* Scan QR and Pay\n"
        f"⚠️ *Step 2:* Send **Screenshot** here\n\n"
        f"Admin will verify and send your key instantly."
    )
    await query.message.delete()
    await context.bot.send_photo(chat_id=query.message.chat_id, photo=QR_IMAGE_URL, caption=text, parse_mode="Markdown")

# ================= SCREENSHOT & APPROVAL =================
async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    plan = context.user_data.get('temp_plan')
    if not plan: return

    await update.message.reply_text("⏳ *Payment Sent for Verification...*", parse_mode="Markdown")
    
    admin_kb = [[InlineKeyboardButton("✅ Approve", callback_data=f"adm_app_{user.id}"), 
                 InlineKeyboardButton("❌ Reject", callback_data=f"adm_rej_{user.id}")]]
    
    admin_text = (
        f"💸 *NEW PAYMENT*\n\n"
        f"👤 ID: `{user.id}`\n"
        f"👤 Name: {user.first_name}\n"
        f"📅 Plan: {plan['days']} Days\n"
        f"💰 Price: ₹{plan['price']}"
    )
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=admin_text, reply_markup=InlineKeyboardMarkup(admin_kb), parse_mode="Markdown")

# ================= ADMIN PANEL =================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    
    stats_text = (
        f"🛠 *ADMIN CONTROL PANEL*\n\n"
        f"👥 Total Users: {len(db['users'])}\n"
        f"✅ Approved: {db['stats']['total_approved']}\n"
        f"❌ Rejected: {db['stats']['total_rejected']}\n"
        f"🔑 Keys Sold: {db['stats']['keys_sold']}\n\n"
        f"Use commands:\n"
        f"`/notify` - Send msg to any user"
    )
    kb = [[InlineKeyboardButton("📢 Broadcast", callback_data="bc"), InlineKeyboardButton("🔄 Refresh", callback_data="admin_ref")]]
    await update.message.reply_text(stats_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data.startswith("adm_app_"):
        target_id = data.split("_")[2]
        context.user_data['target_id'] = target_id
        await query.message.reply_text(f"Paste the **KEY** for user `{target_id}`:")
        return SENDING_KEY
    
    elif data.startswith("adm_rej_"):
        target_id = data.split("_")[2]
        db["stats"]["total_rejected"] += 1
        await context.bot.send_message(target_id, "❌ *Payment Rejected:* Screenshot invalid or payment not received.", parse_mode="Markdown")
        await query.message.reply_text("Rejected successfully.")

async def deliver_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_id = context.user_data.get('target_id')
    key = update.message.text
    
    db["stats"]["total_approved"] += 1
    db["stats"]["keys_sold"] += 1
    if int(target_id) in db["users"]:
        db["users"][int(target_id)]["keys"].append(key)

    await context.bot.send_message(target_id, f"🎉 *PURCHASE SUCCESSFUL*\n\n🔑 Key: `{key}`\n\nEnjoy your hack!", parse_mode="Markdown")
    await update.message.reply_text("✅ Key Delivered!")
    return ConversationHandler.END

# ================= NOTIFY USER LOGIC =================
async def notify_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("Enter User ID to contact:")
    return ADMIN_MSG_USER

async def notify_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['contact_id'] = update.message.text
    await update.message.reply_text(f"Enter Message for `{update.message.text}`:")
    return ADMIN_MSG_TEXT

async def notify_send_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = context.user_data['contact_id']
    msg = update.message.text
    try:
        await context.bot.send_message(target, f"💬 *Message from Admin:*\n\n{msg}", parse_mode="Markdown")
        await update.message.reply_text("✅ Message Sent!")
    except:
        await update.message.reply_text("❌ Failed. ID wrong or bot blocked.")
    return ConversationHandler.END

# ================= OTHER HANDLERS =================
async def my_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    keys = db["users"].get(user_id, {}).get("keys", [])
    text = "🔑 *Your Keys:*\n\n" + ("\n".join([f"• `{k}`" for k in keys]) if keys else "No history found.")
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_start")]]), parse_mode="Markdown")

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    link = f"https://t.me/{(await context.bot.get_me()).username}?start={user.id}"
    text = f"🎁 *REFERRAL PROGRAM*\n\n🔗 *Link:* {link}\n👥 *Referrals:* 0\n💰 *Wallet:* ₹0"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_start")]]), parse_mode="Markdown")

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"📞 *SUPPORT CENTER*\n\n• Payment Issues\n• Setup Guide\n• Key Replacement\n\n💬 Admin: {SUPPORT_USERNAME}"
    await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_start")]]), parse_mode="Markdown")

# ================= MAIN =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Admin Conversation
    admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_callback, pattern="adm_"), CommandHandler("notify", notify_start)],
        states={
            SENDING_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, deliver_key)],
            ADMIN_MSG_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, notify_get_id)],
            ADMIN_MSG_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, notify_send_final)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(admin_conv)
    app.add_handler(CallbackQueryHandler(buy_menu, pattern="buy"))
    app.add_handler(CallbackQueryHandler(plan_confirm, pattern="p_"))
    app.add_handler(CallbackQueryHandler(pay_now, pattern="pay_now"))
    app.add_handler(CallbackQueryHandler(my_keys, pattern="mykeys"))
    app.add_handler(CallbackQueryHandler(referral, pattern="ref"))
    app.add_handler(CallbackQueryHandler(support, pattern="support"))
    app.add_handler(CallbackQueryHandler(start, pattern="back_start"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_screenshot))

    print("🚀 Rolex Premium Bot Started...")
    app.run_polling()

if __name__ == "__main__":
    main()
