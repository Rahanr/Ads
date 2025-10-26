import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import random
import time
import json
import os

# 🔹 তোমার বট টোকেন
BOT_TOKEN = "8283235321:AAERGIPDPoye3D0ZD2lW3QRAJ9p3bFCIYO0"

# 🔹 ডিফল্ট লিংক (সবার জন্য থাকবে)
OWNER_LINK = "https://otieu.com/4/10082724"

bot = telebot.TeleBot(BOT_TOKEN)

# 🔹 ইউজার ডাটা রাখার ফাইল
DATA_FILE = "users.json"

# 🔹 আগের অ্যাড ট্র্যাক করার জন্য
last_ads = {}

# --------------------------------------------------

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

user_channels = load_data()

# --------------------------------------------------
@bot.message_handler(commands=["start"])
def start(message: Message):
    user_id = str(message.from_user.id)

    if user_id not in user_channels:
        user_channels[user_id] = {"channel": None, "links": []}
        save_data(user_channels)

        bot.reply_to(
            message,
            "👋 স্বাগতম!\n\nআমার কাজ হচ্ছে তোমার চ্যানেলে স্বয়ংক্রিয়ভাবে অ্যাড পোস্ট করা।\n\nদয়া করে তোমার চ্যানেলের @username দিন যেখানে আমি এডমিন আছি।"
        )
    else:
        bot.reply_to(
            message,
            "✅ তুমি আগেই রেজিস্টার করেছো!\n\nতোমার লিংক দিতে /1 /2 /3 কমান্ড ব্যবহার করো।"
        )

# --------------------------------------------------
@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith("@"))
def set_channel(message: Message):
    user_id = str(message.from_user.id)
    channel = message.text.strip()

    if user_id not in user_channels:
        bot.reply_to(message, "⚠️ প্রথমে /start কমান্ড দাও।")
        return

    try:
        member = bot.get_chat_member(channel, message.from_user.id)
        bot_member = bot.get_chat_member(channel, bot.get_me().id)

        if bot_member.status not in ("administrator", "creator"):
            bot.reply_to(message, "🚫 আমি ওই চ্যানেলে অ্যাডমিন না। আমাকে অ্যাডমিন দাও।")
            return

        if member.status not in ("administrator", "creator"):
            bot.reply_to(message, "⚠️ তুমি ওই চ্যানেলের অ্যাডমিন না।")
            return
    except Exception as e:
        bot.reply_to(message, f"❌ ভুল হয়েছে বা আমি ওই চ্যানেলে নেই।\n({e})")
        return

    user_channels[user_id]["channel"] = channel
    save_data(user_channels)
    bot.reply_to(message, f"✅ চ্যানেল সেট হয়েছে: {channel}")

# --------------------------------------------------
@bot.message_handler(commands=["1", "2", "3"])
def add_link(message: Message):
    user_id = str(message.from_user.id)
    cmd = message.text.split()[0]
    idx = int(cmd.replace("/", ""))

    if user_id not in user_channels:
        bot.reply_to(message, "⚠️ প্রথমে /start দাও।")
        return

    bot.reply_to(message, f"🔗 এখন তোমার {idx}-নম্বর লিংকটি পাঠাও:")

    def save_link(msg: Message):
        link = msg.text.strip()
        user_data = user_channels[user_id]

        if len(user_data["links"]) < idx:
            user_data["links"].append(link)
        else:
            user_data["links"][idx - 1] = link

        save_data(user_channels)
        bot.reply_to(msg, f"✅ {idx}-নম্বর লিংক সেট হয়েছে!")

        bot.unregister_message_handler(save_link)

    bot.register_next_step_handler(message, save_link)

# --------------------------------------------------
@bot.channel_post_handler(func=lambda m: True)
def auto_ad(post: Message):
    channel_id = post.chat.id
    username = post.chat.username

    # আগের অ্যাড থাকলে মুছে ফেলো
    if channel_id in last_ads:
        try:
            bot.delete_message(channel_id, last_ads[channel_id])
        except Exception:
            pass

    # ইউজারের চ্যানেল খোঁজা
    matched_user = None
    for uid, data in user_channels.items():
        if data.get("channel") == f"@{username}":
            matched_user = data
            break

    # 🔹 সব লিংক (ডিফল্ট + ইউজার)
    all_links = [OWNER_LINK]
    if matched_user and matched_user["links"]:
        all_links += matched_user["links"]

    # যদি একদমই লিংক না থাকে, কিছু করো না
    if not all_links:
        return

    selected_link = random.choice(all_links)

    # 🔹 অ্যাড টেক্সট
    ad_text = (
        "📢 **বিজ্ঞাপন**\n\n"
        "💰 ইনকাম করতে চান?\n\n"
        "🚀 অফিসিয়াল টেলিগ্রাম বিজ্ঞাপন দেখুন নিচের লিংকে 👇"
    )

    # 🔹 ইনলাইন বাটন তৈরি
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔗 Earn now 🤑", url=selected_link))

    # 🔹 পোস্ট পাঠাও
    sent = bot.send_message(
        channel_id,
        ad_text,
        parse_mode="Markdown",
        reply_markup=markup,
        disable_web_page_preview=True
    )

    last_ads[channel_id] = sent.message_id

# --------------------------------------------------
print("🤖 Bot is running...")
while True:
    try:
        bot.polling(non_stop=True)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
