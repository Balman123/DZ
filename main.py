import os
import json
import telebot
import logging

# Configuration
TELEGRAM_BOT_TOKEN = '5653703645:AAFf4kOIDOP7YGh8jegZ0yOOYAalVxGtiTY'
GROUP_CHAT_ID = -1002000607740
USER_TOPICS_FILE = 'user_topics.json'
CHAT_ID_FILE = 'chat_ids.json'

# Bot Initialization
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Data Management Functions
def load_data(filename):
    if not os.path.exists(filename):
        save_data(filename, {})
    with open(filename, 'r') as file:
        return json.load(file)

def save_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def load_user_topics():
    return load_data(USER_TOPICS_FILE)

def save_user_topics(user_name, topic_id):
    user_topics = load_user_topics()
    user_topics[user_name] = topic_id
    save_data(USER_TOPICS_FILE, user_topics)

def load_chat_ids():
    return load_data(CHAT_ID_FILE)

# Topic Creation
def create_topic(chat_id, user_topics, username):
    try:
        topic = bot.create_forum_topic(chat_id, username)
        user_topics[username] = topic.message_thread_id
        save_data(USER_TOPICS_FILE, user_topics)
        return topic.message_thread_id
    except telebot.apihelper.ApiTelegramException as e:
        logging.error(f"Error creating topic for {username}: {e}")
        return None

# Command to get chat ID
@bot.message_handler(commands=['my_id'])
def send_chat_id(message):
    chat_id = message.chat.id
    username = message.chat.username
    chat_ids = load_chat_ids()
    chat_ids[username] = chat_id
    save_data(CHAT_ID_FILE, chat_ids)
    bot.reply_to(message, f"Ваш Chat ID: {chat_id} \n Напишите сообщенеи системному администратору")

# Message Handling
@bot.message_handler(content_types=["text", "photo", "video", "audio", "document", "sticker", "voice", "video_note", "location", "contact"])
def handle_message(message):
    if message.chat.type == 'private':  # Message from a user to the bot
        user_topics = load_user_topics()
        chat_ids = load_chat_ids()
        user_chat_id = chat_ids.get(message.chat.username)

        if user_chat_id:
            topic_id = user_topics.get(message.chat.username)
            if not topic_id:
                topic_id = create_topic(GROUP_CHAT_ID, user_topics, message.chat.username)
                if topic_id:
                    save_user_topics(message.chat.username, topic_id)
                else:
                    bot.send_message(message.chat.id, "Не удалось создать тему. Попробуйте позже.")
                    return

            try:
                bot.forward_message(chat_id=GROUP_CHAT_ID, from_chat_id=message.chat.id, message_id=message.message_id, message_thread_id=topic_id)
            except telebot.apihelper.ApiTelegramException as e:
                logging.error(f"Error forwarding message to group chat: {e}")
        else:
            bot.send_message(message.chat.id, "Пожалуйста, отправьте команду /my_id, чтобы я мог узнать ваш Chat ID.")

    elif message.message_thread_id:  # Message is a reply within a group topic
        user_topics = load_user_topics()
        chat_ids = load_chat_ids()

        for username, topic in user_topics.items():
            if topic == message.message_thread_id:
                chat_id = chat_ids.get(username)
                if chat_id:
                    try:
                        bot.send_message(chat_id=chat_id, text=message.text)  # Send as text from the bot
                    except telebot.apihelper.ApiTelegramException as e:
                        logging.error(f"Error sending message to user {username}: {e}")
                else:
                    logging.error(f"Chat ID not found for user {username}")
                break

# Start Bot
if __name__ == '__main__':
    bot.polling()
