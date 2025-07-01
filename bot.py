import telebot
import re
from yandex_music import Client
from decouple import config
import logging
import sys

# Настройка логирования
logging.basicConfig(level=logging.INFO, filename='bot.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')

# Проверка наличия переменных окружения
try:
    TELEGRAM_TOKEN = config('TELEGRAM_TOKEN')
    YANDEX_MUSIC_TOKEN = config('YANDEX_MUSIC_TOKEN')
    playlist_uuid = config('playlist_uuid')
    link = config('link')
    playlist_name = config('playlist_name')
except Exception as e:
    logging.critical(f"Ошибка загрузки переменных окружения: {e}")
    sys.exit("Ошибка: переменные окружения не заданы корректно!")

# Инициализация Telegram бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)
# Инициализация клиента Яндекс Музыки
client = Client(YANDEX_MUSIC_TOKEN).init()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"Просто отправляй мне ссылки на треки в Яндекс Музыке, и я добавлю их в плейлист - {link}\nДля справки напиши /help")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Отправьте ссылку на трек Яндекс Музыки (например, https://music.yandex.ru/track/123456 или https://music.yandex.ru/album/123456/track/654321). Я добавлю его в плейлист. Если возникнут вопросы — пишите!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    # Если сообщение переслано, пробуем взять текст из пересланного
    if hasattr(message, 'forward_from') and message.forward_from:
        text = message.forward_from.text if hasattr(message.forward_from, 'text') else text
    try:
        album_id, track_id = extract_album_and_track_id(text)
        if album_id is None:
            track_info = client.tracks(track_id)[0]
            album_id = track_info.albums[0].id
        playlists = client.users_playlists_list()
        r = None
        for playlist in playlists:
            if playlist['title'] == playlist_name:
                r = playlist['revision']
                break
        if r is None:
            bot.reply_to(message, "Плейлист не найден! Проверьте имя плейлиста в настройках.")
            logging.warning(f"Плейлист '{playlist_name}' не найден для пользователя {message.from_user.id}")
            return
        client.users_playlists_insert_track(playlist_uuid, track_id, album_id, revision=r)
        bot.reply_to(message, "Трек успешно добавлен в плейлист!")
        logging.info(f"Трек {track_id} (альбом {album_id}) добавлен в плейлист '{playlist_name}' пользователем {message.from_user.id}")
    except ValueError as ve:
        bot.reply_to(message, f"Пожалуйста, отправьте корректную ссылку на трек Яндекс Музыки.\nОшибка: {ve}")
        logging.info(f"Некорректная ссылка: {text} от пользователя {message.from_user.id}")
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка при добавлении трека: {str(e)}")
        logging.error(f"Ошибка при добавлении трека: {str(e)} | Сообщение: {text}")

def extract_album_and_track_id(url):
    # Поддержка ссылок с параметрами (например, ? и #)
    album_track_pattern = re.compile(r'https://music\.yandex\.ru/album/(\d+)/track/(\d+)(?:[/?#].*)?')
    track_pattern = re.compile(r'https://music\.yandex\.ru/track/(\d+)(?:[/?#].*)?')
    album_track_match = album_track_pattern.search(url)
    if album_track_match:
        return album_track_match.group(1), album_track_match.group(2)
    track_match = track_pattern.search(url)
    if track_match:
        return None, track_match.group(1)
    raise ValueError("Неверная ссылка на трек. Пример: https://music.yandex.ru/track/123456")

# Запуск бота
bot.polling() 
