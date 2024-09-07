import logging
import os
import json
import telebot
from chatgpt import openai
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from admintf import (
     bot as admin_bot, load_cloned_bots, is_admin_bot, save_json_file, schedule_broadcast_all, list_scheduled_jobs, cancel_scheduled_job, set_join_group_or_channel, get_join_requirements, 
     check_user_joined, broadcast_to_all_bots, broadcast_to_freemium_bots, broadcast_to_premium_bots, handle_schedule_user_broadcast, handle_schedule_group_broadcast,
     handle_schedule_channel_broadcast, handle_schedule_all_broadcast,handle_list_scheduled_jobs, handle_cancel_scheduled_job, handle_set_join, handle_user_not_joined
)
from broadcast import ( 
     load_json_file, load_user_data, load_group_ids, load_channel_ids, is_admin, is_freemium, is_premium, get_admins_of_chat, 
     schedule_broadcast, broadcast_to_user, broadcast_to_group, broadcast_to_channel, broadcast_to_all, schedule_user_broadcast,
     schedule_group_broadcast, schedule_channel_broadcast, schedule_all_broadcast
)
from handlers import (
    start, button, handle_message, set_admin_id, set_user_id, clone_bot, process_payment, payment_callback, total_users,
    handle_downloader_fb, handle_downloader_tg, handle_downloader_ig, handle_downloader_tt, handle_downloader_yt,
    is_user_allowed, is_user_paid, save_user_data, extract_info_from_text, handle_conversion,
    generate_random_string, create_category, create_bill, update_config
)
from keyboards import get_main_keyboard, get_submenu_keyboard, get_conversion_keyboard, SUBMENU_OPTIONS
from clonebot import get_user_data, clone_bot, fetch_additional_data, get_user_bot_limits
from config import TOKEN as TELEGRAM_BOT_TOKEN, ADMIN_BOT_ID, ADMIN_USER_ID, ALLOWED_USER_IDS, PAID_USER_IDS, TOYYIBPAY_SECRET_KEY

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the bot token from environment variables
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("Telegram bot token is not set in environment variables.")
    exit(1)

# Create the bot instance
bot = telebot.TeleBot(TOKEN)

def save_auto_approve_group_id(group_id: int) -> None:
    """Save the group ID to a file."""
    with open('auto_approve_group_id.txt', 'w') as f:
        f.write(str(group_id))

def get_auto_approve_group_id() -> int:
    """Load the group ID from the file."""
    if os.path.exists('auto_approve_group_id.txt'):
        with open('auto_approve_group_id.txt', 'r') as f:
            return int(f.read().strip())
    return 0

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_chat_member(message: telebot.types.Message) -> None:
    """Handle new members joining the group and automatically approve them."""
    if message.new_chat_members:
        for member in message.new_chat_members:
            if member.id == bot.get_me().id:
                group_id = message.chat.id
                save_auto_approve_group_id(group_id)
                bot.send_message(group_id, "Auto Approve is now enabled for this group.")
                break

    group_id = get_auto_approve_group_id()
    if group_id and message.chat.id == group_id:
        bot.approve_chat_join_request(message.chat.id, message.from_user.id)

def save_user_data(user_id: int) -> None:
    """Simpan user_id ke dalam user_data.json."""
    file_path = 'user_data.json'
    
    # Muatkan data sedia ada
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
    else:
        data = {}

    # Tambah atau kemas kini user_id dalam data
    data[str(user_id)] = {"user_id": user_id}

    # Simpan data ke dalam fail
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

@bot.message_handler(commands=['start'])
def handle_start(message: telebot.types.Message) -> None:
    """Handle the /start command and show the main menu."""
    user_id = message.from_user.id
    save_user_data(user_id)  # Simpan user_id ke dalam user_data.json
    
    markup = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton(text='Service', callback_data='service'),
        InlineKeyboardButton(text='Dev Bot', callback_data='dev_bot'),
        InlineKeyboardButton(text='Support Bot', callback_data='support_bot'),
        InlineKeyboardButton(text='Clone Bot', callback_data='clone_bot')
    ]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Welcome! Please choose an option from the menu below:", reply_markup=markup)

def show_service_submenu(chat_id: int) -> None:
    """Show sub-menu options under 'Service'."""
    markup = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton(text='Free Version', callback_data='free_version'),
        InlineKeyboardButton(text='Premium Version', callback_data='premium_version')
    ]
    markup.add(*buttons)
    bot.send_message(chat_id, "Please choose an option from the service below:", reply_markup=markup)

def show_version_submenu(chat_id: int, version_type: str) -> None:
    """Show sub-menu options under Free or Premium Version."""
    markup = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton(text='Convert', callback_data=f'{version_type}_convert'),
        InlineKeyboardButton(text='Broadcast', callback_data=f'{version_type}_broadcast'),
        InlineKeyboardButton(text='Auto Approve', callback_data=f'{version_type}_auto_approve'),
        InlineKeyboardButton(text='Downloader', callback_data=f'{version_type}_downloader'),
        InlineKeyboardButton(text='ChatGPT', callback_data=f'{version_type}_chatgpt')
    ]
    markup.add(*buttons)
    bot.send_message(chat_id, f"Please choose an option for {version_type}:", reply_markup=markup)

def show_downloader_submenu(chat_id: int, version_type: str) -> None:
    """Show sub-menu options under 'Downloader'."""
    markup = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton(text='FB', callback_data=f'{version_type}_fb'),
        InlineKeyboardButton(text='IG', callback_data=f'{version_type}_ig'),
        InlineKeyboardButton(text='TG', callback_data=f'{version_type}_tg'),
        InlineKeyboardButton(text='TT', callback_data=f'{version_type}_tt'),
        InlineKeyboardButton(text='YT', callback_data=f'{version_type}_yt')
    ]
    markup.add(*buttons)
    bot.send_message(chat_id, f"Please choose an option for {version_type} Downloader:", reply_markup=markup)

def show_convert_submenu(chat_id: int) -> None:
    """Show sub-menu options under 'Convert'."""
    markup = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton(text='Bug Vless', callback_data='bug_vless'),
        InlineKeyboardButton(text='Text to Img', callback_data='text_to_img'),
        InlineKeyboardButton(text='Img to Text', callback_data='img_to_text'),
        InlineKeyboardButton(text='Img to PDF', callback_data='img_to_pdf'),
        InlineKeyboardButton(text='PDF to Img', callback_data='pdf_to_img'),
        InlineKeyboardButton(text='MP4 to Audio', callback_data='mp4_to_audio')
    ]
    markup.add(*buttons)
    bot.send_message(chat_id, "Please choose an option for Convert:", reply_markup=markup)

def show_broadcast_submenu(chat_id: int) -> None:
    """Show sub-menu options under 'Broadcast'."""
    markup = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton(text='Broadcast User', callback_data='broadcast_user'),
        InlineKeyboardButton(text='Broadcast Group', callback_data='broadcast_group'),
        InlineKeyboardButton(text='Broadcast Channel', callback_data='broadcast_channel'),
        InlineKeyboardButton(text='Broadcast All', callback_data='broadcast_all'),
        InlineKeyboardButton(text='Schedule User', callback_data='schedule_user'),
        InlineKeyboardButton(text='Schedule Group', callback_data='schedule_group'),
        InlineKeyboardButton(text='Schedule Channel', callback_data='schedule_channel'),
        InlineKeyboardButton(text='Schedule All', callback_data='schedule_all')
    ]
    markup.add(*buttons)
    bot.send_message(chat_id, "Please choose an option for Broadcast:", reply_markup=markup)

def show_chatgpt_info(chat_id: int) -> None:
    """Send information about how to use ChatGPT."""
    info_message = (
        "To interact with ChatGPT, please use the /ask command followed by your question. "
        "For example:\n\n"
        "/ask What is the capital of France?\n\n"
        "The bot will then send your question to ChatGPT and return the response."
    )
    bot.send_message(chat_id, info_message)

@bot.message_handler(commands=['ask'])
def handle_ask_command(message: telebot.types.Message) -> None:
    """Handle /ask command to interact with ChatGPT or extract information."""
    try:
        user_input = message.text[len('/ask'):].strip()

        if user_input.startswith('extract:'):
            text_to_extract = user_input[len('extract:'):].strip()
            extracted_info = extract_info_from_text(text_to_extract)
            bot.send_message(message.chat.id, json.dumps(extracted_info, indent=2))
        else:
            response = generate_chatgpt_response(user_input)
            bot.send_message(message.chat.id, response)
    except Exception as e:
        logger.error(f"Error handling /ask command: {e}")
        bot.send_message(message.chat.id, "Sorry, there was an error processing your request.")

@bot.callback_query_handler(func=lambda call: call.data == 'free_version_chatgpt' or call.data == 'premium_version_chatgpt')
def handle_chatgpt_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries related to the ChatGPT button."""
    version_type = call.data.split('_', 2)[0].capitalize()
    show_chatgpt_info(call.message.chat.id, version_type)

@bot.callback_query_handler(func=lambda call: call.data.startswith('service'))
def handle_service_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries related to the 'Service' button."""
    if call.data == 'service':
        show_service_submenu(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('free_version', 'premium_version')))
def handle_version_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries related to service versions."""
    version_type = call.data.split('_')[0]
    show_version_submenu(call.message.chat.id, version_type.capitalize())

@bot.callback_query_handler(func=lambda call: call.data.startswith(('free_version_downloader', 'premium_version_downloader')))
def handle_downloader_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries for Downloader options."""
    version_type = call.data.split('_', 2)[0].capitalize()
    show_downloader_submenu(call.message.chat.id, version_type)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('free_version_auto_approve', 'premium_version_auto_approve')))
def handle_auto_approve_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries for Auto Approve options."""
    version_type = call.data.split('_', 1)[0].capitalize()
    bot.send_message(call.message.chat.id, f"Auto Approve functionality is now active for the {version_type} version.")
    group_id = get_auto_approve_group_id()
    if group_id:
        bot.send_message(call.message.chat.id, "Auto Approve feature is active. The bot will now monitor and approve group join requests.")

@bot.callback_query_handler(func=lambda call: call.data == 'clone_bot')
def handle_clone_bot_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries related to the 'Clone Bot' button."""
    bot.send_message(call.message.chat.id, "To clone the bot, please use the /clone_bot command.")

@bot.callback_query_handler(func=lambda call: call.data == 'dev_bot')
def handle_dev_bot_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries related to the 'Dev Bot' button."""
    bot.send_message(call.message.chat.id, "You can find more information about the bot at: https://t.me/abgomey")

@bot.callback_query_handler(func=lambda call: call.data == 'support_bot')
def handle_support_bot_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries related to the 'Support Bot' button."""
    bot.send_message(call.message.chat.id, "For support, please contact us at: https://t.me/+X999yVVgz4I5NDdl")

@bot.callback_query_handler(func=lambda call: call.data.startswith('convert'))
def handle_convert_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries related to 'Convert' button."""
    if call.data == 'convert':
        show_convert_submenu(call.message.chat.id)

# Add handlers for conversion options
conversion_handlers = {
    'bug_vless': "Bug Vless functionality is under development.",
    'text_to_img': "Text to Image functionality is under development.",
    'img_to_text': "Image to Text functionality is under development.",
    'img_to_pdf': "Image to PDF functionality is under development.",
    'pdf_to_img': "PDF to Image functionality is under development.",
    'mp4_to_audio': "MP4 to Audio functionality is under development."
}

for callback_data, response_message in conversion_handlers.items():
    @bot.callback_query_handler(func=lambda call, data=callback_data: call.data.startswith(data))
    def handle_conversion_callback(call: telebot.types.CallbackQuery, response_message=response_message) -> None:
        bot.send_message(call.message.chat.id, response_message)

@bot.callback_query_handler(func=lambda call: call.data == 'bug_vless')
def handle_bug_vless_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback for Bug Vless option."""
    chat_id = call.message.chat.id
    conversion_keyboard = get_conversion_keyboard()
    bot.send_message(chat_id, "Please choose a conversion option:", reply_markup=conversion_keyboard)
     
@bot.message_handler(commands=['set_admin_id'])
def handle_set_admin_id(message: telebot.types.Message) -> None:
    set_admin_id(message, bot)

@bot.message_handler(commands=['set_user_id'])
def handle_set_user_id(message: telebot.types.Message) -> None:
    set_user_id(message, bot)

@bot.message_handler(commands=['process_payment'])
def handle_process_payment(message: telebot.types.Message) -> None:
    process_payment(message, bot)

@bot.message_handler(commands=['payment_callback'])
def handle_payment_callback(message: telebot.types.Message) -> None:
    payment_callback(message, bot)

@bot.message_handler(commands=['total_users'])
def handle_total_users(message: telebot.types.Message) -> None:
    total_users(message, bot)

@bot.message_handler(commands=['downloader_fb'])
def handle_downloader_fb_command(message: telebot.types.Message) -> None:
    handle_downloader_fb(message, bot)

@bot.message_handler(commands=['downloader_tg'])
def handle_downloader_tg_command(message: telebot.types.Message) -> None:
    handle_downloader_tg(message, bot)

@bot.message_handler(commands=['downloader_ig'])
def handle_downloader_ig_command(message: telebot.types.Message) -> None:
    handle_downloader_ig(message, bot)

@bot.message_handler(commands=['downloader_tt'])
def handle_downloader_tt_command(message: telebot.types.Message) -> None:
    handle_downloader_tt(message, bot)

@bot.message_handler(commands=['downloader_yt'])
def handle_downloader_yt_command(message: telebot.types.Message) -> None:
    handle_downloader_yt(message, bot)

@bot.message_handler(commands=['broadcast_user'])
def broadcast_to_user_command(message: telebot.types.Message) -> None:
    broadcast_to_user(message)

@bot.message_handler(commands=['broadcast_group'])
def broadcast_to_group_command(message: telebot.types.Message) -> None:
    broadcast_to_group(message)

@bot.message_handler(commands=['broadcast_channel'])
def broadcast_to_channel_command(message: telebot.types.Message) -> None:
    broadcast_to_channel(message)

@bot.message_handler(commands=['broadcast_all'])
def broadcast_to_all_command(message: telebot.types.Message) -> None:
    broadcast_to_all(message)

@bot.message_handler(commands=['schedule_user'])
def schedule_user_broadcast_command(message: telebot.types.Message) -> None:
    schedule_user_broadcast(message)

@bot.message_handler(commands=['schedule_group'])
def schedule_group_broadcast_command(message: telebot.types.Message) -> None:
    schedule_group_broadcast(message)

@bot.message_handler(commands=['schedule_channel'])
def schedule_channel_broadcast_command(message: telebot.types.Message) -> None:
    schedule_channel_broadcast(message)

@bot.message_handler(commands=['schedule_all'])
def schedule_all_broadcast_command(message: telebot.types.Message) -> None:
    schedule_all_broadcast(message)

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def handle_text_message(message: telebot.types.Message) -> None:
    handle_message(message, bot)

def main() -> None:
    try:
        logger.info("Starting bot...")
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
